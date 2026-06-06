from __future__ import annotations

import argparse
import json
import math
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from torch import nn
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModel, AutoTokenizer, get_cosine_schedule_with_warmup


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class MultiTaskDataset(Dataset):
    def __init__(
        self,
        frame: pd.DataFrame,
        tokenizer,
        text_col: str,
        max_len: int,
    ) -> None:
        self.texts = frame[text_col].astype(str).tolist()
        self.labels = frame["label_idx"].astype(int).tolist()
        self.sectors = frame["sector_idx"].astype(int).tolist()
        self.groups = frame["group_idx"].astype(int).tolist()
        self.sample_weights = frame["sample_weight"].astype(float).tolist()
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        enc = self.tokenizer(
            self.texts[idx],
            truncation=True,
            padding="max_length",
            max_length=self.max_len,
            return_tensors="pt",
        )
        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "labels": torch.tensor(self.labels[idx], dtype=torch.long),
            "sector_labels": torch.tensor(self.sectors[idx], dtype=torch.long),
            "group_labels": torch.tensor(self.groups[idx], dtype=torch.long),
            "sample_weight": torch.tensor(self.sample_weights[idx], dtype=torch.float32),
        }


class MultiTaskClassifier(nn.Module):
    def __init__(
        self,
        model_name: str,
        num_sectors: int,
        num_groups: int,
        num_labels: int,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.backbone = AutoModel.from_pretrained(model_name)
        hidden = self.backbone.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.sector_head = nn.Linear(hidden, num_sectors)
        self.group_head = nn.Linear(hidden, num_groups)
        self.label_head = nn.Linear(hidden, num_labels)

    def forward(self, input_ids, attention_mask):
        outputs = self.backbone(input_ids=input_ids, attention_mask=attention_mask)
        if hasattr(outputs, "last_hidden_state"):
            pooled = outputs.last_hidden_state[:, 0]
        else:
            pooled = outputs[0][:, 0]
        pooled = self.dropout(pooled)
        return {
            "sector_logits": self.sector_head(pooled),
            "group_logits": self.group_head(pooled),
            "label_logits": self.label_head(pooled),
        }


def inverse_sqrt_class_weights(labels: list[int], num_classes: int, power: float = 0.5) -> torch.Tensor:
    counts = np.bincount(labels, minlength=num_classes).astype(np.float64)
    counts[counts == 0] = 1.0
    weights = (counts.mean() / counts) ** power
    weights = weights / weights.mean()
    return torch.tensor(weights, dtype=torch.float32)


def compute_loss(
    outputs: dict[str, torch.Tensor],
    batch: dict[str, torch.Tensor],
    sector_weights: torch.Tensor,
    group_weights: torch.Tensor,
    label_weights: torch.Tensor,
    multitask_weights: tuple[float, float, float],
    label_smoothing: float,
    use_sample_weights: bool,
) -> torch.Tensor:
    sector_loss = F.cross_entropy(
        outputs["sector_logits"],
        batch["sector_labels"],
        weight=sector_weights,
        reduction="none",
        label_smoothing=label_smoothing,
    )
    group_loss = F.cross_entropy(
        outputs["group_logits"],
        batch["group_labels"],
        weight=group_weights,
        reduction="none",
        label_smoothing=label_smoothing,
    )
    label_loss = F.cross_entropy(
        outputs["label_logits"],
        batch["labels"],
        weight=label_weights,
        reduction="none",
        label_smoothing=label_smoothing,
    )
    total = (
        multitask_weights[0] * sector_loss
        + multitask_weights[1] * group_loss
        + multitask_weights[2] * label_loss
    )
    if use_sample_weights:
        total = total * batch["sample_weight"]
    return total.mean()


def evaluate(model, loader, device) -> tuple[float, float, int, list[int], list[int]]:
    model.eval()
    all_preds: list[int] = []
    all_labels: list[int] = []
    with torch.no_grad():
        for batch in loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = model(batch["input_ids"], batch["attention_mask"])
            preds = outputs["label_logits"].argmax(dim=-1)
            all_preds.extend(preds.cpu().tolist())
            all_labels.extend(batch["labels"].cpu().tolist())
    macro_f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)
    acc = sum(int(p == t) for p, t in zip(all_preds, all_labels)) / max(1, len(all_labels))
    counts = pd.Series(all_labels).value_counts()
    top10 = counts.index.tolist()[:10]
    top10_f1s = f1_score(all_labels, all_preds, average=None, labels=top10, zero_division=0)
    top10_pass = int(sum(1 for v in top10_f1s if v > 0.85))
    return macro_f1, acc, top10_pass, all_preds, all_labels


@dataclass
class RunConfig:
    model_name: str
    train_csv: str
    test_csv: str
    text_col: str
    output_dir: str
    max_len: int
    batch_size: int
    eval_batch_size: int
    grad_accum: int
    epochs: int
    lr: float
    weight_decay: float
    warmup_ratio: float
    seed: int
    dev_size: float
    use_sample_weights: bool
    sector_loss_weight: float
    group_loss_weight: float
    label_loss_weight: float
    label_smoothing: float
    freeze_backbone_epochs: int
    bf16: bool
    fp16: bool
    gradient_checkpointing: bool


def train(config: RunConfig) -> dict:
    seed_everything(config.seed)
    out_dir = Path(config.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_df = pd.read_csv(config.train_csv)
    test_df = pd.read_csv(config.test_csv)
    fit_df, dev_df = train_test_split(
        train_df,
        test_size=config.dev_size,
        random_state=config.seed,
        stratify=train_df["label_idx"],
    )

    tokenizer = AutoTokenizer.from_pretrained(config.model_name)
    fit_ds = MultiTaskDataset(fit_df.reset_index(drop=True), tokenizer, config.text_col, config.max_len)
    dev_ds = MultiTaskDataset(dev_df.reset_index(drop=True), tokenizer, config.text_col, config.max_len)
    test_ds = MultiTaskDataset(test_df.reset_index(drop=True), tokenizer, config.text_col, config.max_len)

    fit_loader = DataLoader(fit_ds, batch_size=config.batch_size, shuffle=True, num_workers=2, pin_memory=True)
    dev_loader = DataLoader(dev_ds, batch_size=config.eval_batch_size, shuffle=False, num_workers=2, pin_memory=True)
    test_loader = DataLoader(test_ds, batch_size=config.eval_batch_size, shuffle=False, num_workers=2, pin_memory=True)

    num_sectors = int(train_df["sector_idx"].nunique())
    num_groups = int(train_df["group_idx"].nunique())
    num_labels = int(train_df["label_idx"].nunique())

    model = MultiTaskClassifier(
        model_name=config.model_name,
        num_sectors=num_sectors,
        num_groups=num_groups,
        num_labels=num_labels,
    )
    if config.gradient_checkpointing and hasattr(model.backbone, "gradient_checkpointing_enable"):
        model.backbone.gradient_checkpointing_enable()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    sector_weights = inverse_sqrt_class_weights(fit_df["sector_idx"].astype(int).tolist(), num_sectors).to(device)
    group_weights = inverse_sqrt_class_weights(fit_df["group_idx"].astype(int).tolist(), num_groups).to(device)
    label_weights = inverse_sqrt_class_weights(fit_df["label_idx"].astype(int).tolist(), num_labels).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=config.lr, weight_decay=config.weight_decay)
    total_steps = math.ceil(len(fit_loader) / config.grad_accum) * config.epochs
    warmup_steps = int(total_steps * config.warmup_ratio)
    scheduler = get_cosine_schedule_with_warmup(optimizer, warmup_steps, total_steps)

    scaler = torch.cuda.amp.GradScaler(enabled=config.fp16)
    use_autocast = config.fp16 or config.bf16
    amp_dtype = torch.bfloat16 if config.bf16 else torch.float16

    best_dev_f1 = -1.0
    best_state_path = out_dir / "best_state.pt"
    history: list[dict] = []

    for epoch in range(1, config.epochs + 1):
        model.train()
        if epoch <= config.freeze_backbone_epochs:
            for param in model.backbone.parameters():
                param.requires_grad = False
        else:
            for param in model.backbone.parameters():
                param.requires_grad = True

        optimizer.zero_grad(set_to_none=True)
        running_loss = 0.0
        started = time.time()
        for step, batch in enumerate(fit_loader, start=1):
            batch = {k: v.to(device) for k, v in batch.items()}
            with torch.cuda.amp.autocast(enabled=use_autocast, dtype=amp_dtype):
                outputs = model(batch["input_ids"], batch["attention_mask"])
                loss = compute_loss(
                    outputs=outputs,
                    batch=batch,
                    sector_weights=sector_weights,
                    group_weights=group_weights,
                    label_weights=label_weights,
                    multitask_weights=(
                        config.sector_loss_weight,
                        config.group_loss_weight,
                        config.label_loss_weight,
                    ),
                    label_smoothing=config.label_smoothing,
                    use_sample_weights=config.use_sample_weights,
                ) / config.grad_accum

            if config.fp16:
                scaler.scale(loss).backward()
            else:
                loss.backward()
            running_loss += loss.item() * config.grad_accum

            if step % config.grad_accum == 0 or step == len(fit_loader):
                if config.fp16:
                    scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                if config.fp16:
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    optimizer.step()
                scheduler.step()
                optimizer.zero_grad(set_to_none=True)

        dev_f1, dev_acc, dev_top10, _, _ = evaluate(model, dev_loader, device)
        epoch_record = {
            "epoch": epoch,
            "train_loss": round(running_loss / max(1, len(fit_loader)), 6),
            "dev_macro_f1": round(dev_f1, 6),
            "dev_accuracy": round(dev_acc, 6),
            "dev_top10_pass": dev_top10,
            "elapsed_seconds": round(time.time() - started, 1),
        }
        history.append(epoch_record)
        print(
            f"epoch {epoch:02d} | loss {epoch_record['train_loss']:.4f} | "
            f"dev_f1 {dev_f1*100:.2f}% | dev_acc {dev_acc*100:.2f}% | top10 {dev_top10}/10",
            flush=True,
        )
        if dev_f1 > best_dev_f1:
            best_dev_f1 = dev_f1
            torch.save({"model": model.state_dict(), "config": config.__dict__}, best_state_path)

    saved = torch.load(best_state_path, map_location=device)
    model.load_state_dict(saved["model"])
    test_f1, test_acc, test_top10, test_preds, test_labels = evaluate(model, test_loader, device)

    summary = {
        "model_name": config.model_name,
        "text_col": config.text_col,
        "epochs": config.epochs,
        "batch_size": config.batch_size,
        "gradient_accumulation": config.grad_accum,
        "max_len": config.max_len,
        "best_dev_macro_f1": round(best_dev_f1, 6),
        "official_test_macro_f1": round(test_f1, 6),
        "official_test_accuracy": round(test_acc, 6),
        "official_test_top10_pass": int(test_top10),
        "history": history,
    }
    (out_dir / "training_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    np.save(out_dir / "test_preds.npy", np.array(test_preds, dtype=np.int32))
    np.save(out_dir / "test_labels.npy", np.array(test_labels, dtype=np.int32))
    tokenizer.save_pretrained(out_dir / "tokenizer")
    print(json.dumps(summary, indent=2), flush=True)
    return summary


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train multitask segment-aware transformer.")
    parser.add_argument("--model-name", default="answerdotai/ModernBERT-base")
    parser.add_argument("--train-csv", required=True)
    parser.add_argument("--test-csv", required=True)
    parser.add_argument("--text-col", default="text_joint", choices=["text_primary", "text_aux", "text_joint"])
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-len", type=int, default=512)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--eval-batch-size", type=int, default=16)
    parser.add_argument("--grad-accum", type=int, default=4)
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--warmup-ratio", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dev-size", type=float, default=0.10)
    parser.add_argument("--disable-sample-weights", action="store_true")
    parser.add_argument("--sector-loss-weight", type=float, default=0.15)
    parser.add_argument("--group-loss-weight", type=float, default=0.25)
    parser.add_argument("--label-loss-weight", type=float, default=0.60)
    parser.add_argument("--label-smoothing", type=float, default=0.02)
    parser.add_argument("--freeze-backbone-epochs", type=int, default=0)
    parser.add_argument("--gradient-checkpointing", action="store_true")
    parser.add_argument("--bf16", action="store_true")
    parser.add_argument("--fp16", action="store_true")
    return parser


if __name__ == "__main__":
    args = make_parser().parse_args()
    cfg = RunConfig(
        model_name=args.model_name,
        train_csv=args.train_csv,
        test_csv=args.test_csv,
        text_col=args.text_col,
        output_dir=args.output_dir,
        max_len=args.max_len,
        batch_size=args.batch_size,
        eval_batch_size=args.eval_batch_size,
        grad_accum=args.grad_accum,
        epochs=args.epochs,
        lr=args.lr,
        weight_decay=args.weight_decay,
        warmup_ratio=args.warmup_ratio,
        seed=args.seed,
        dev_size=args.dev_size,
        use_sample_weights=not args.disable_sample_weights,
        sector_loss_weight=args.sector_loss_weight,
        group_loss_weight=args.group_loss_weight,
        label_loss_weight=args.label_loss_weight,
        label_smoothing=args.label_smoothing,
        freeze_backbone_epochs=args.freeze_backbone_epochs,
        bf16=args.bf16,
        fp16=args.fp16,
        gradient_checkpointing=args.gradient_checkpointing,
    )
    train(cfg)
