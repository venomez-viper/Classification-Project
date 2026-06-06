"""
Local training script — DeBERTa-v3-small fine-tuning on GECS classification.
Uses a raw PyTorch training loop (no HuggingFace Trainer).

Optimised for RTX 3050 / 4 GB VRAM.
Runs fully offline after download_model.py has been run once.

Usage:
    python llm_finetuning/scripts/train_local.py --task task1
    python llm_finetuning/scripts/train_local.py --task task2
"""

import argparse
import gc
import json
import os
import time

os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"]  = "1"

# pandas MUST be imported and CSVs read before torch on Windows
import pandas as pd
import numpy as np
from sklearn.metrics import f1_score, classification_report

ROOT       = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR   = os.path.join(ROOT, "llm_finetuning", "data")
MODEL_PATH = os.path.join(ROOT, "llm_finetuning", "models", "deberta-v3-small")
RESULTS    = os.path.join(ROOT, "llm_finetuning", "results")
os.makedirs(RESULTS, exist_ok=True)

# ── Hyperparameters ───────────────────────────────────────────────────────────
MAX_LEN    = 128
BATCH_SIZE = 2        # reduced from 4 — frees activation memory for resume runs
GRAD_ACCUM = 8        # doubled to keep effective batch = 16
EPOCHS     = 6
LR         = 3e-5
WARMUP_PCT = 0.1
SEED       = 42
LOG_EVERY  = 50
EVAL_BS    = 4        # reduced from 8 to stay within VRAM during eval
EMPTY_CACHE_EVERY = 200   # more aggressive cache clearing (was 500)

RESUME_LR     = 1e-5   # lower LR for continued fine-tuning — model is already adapted
RESUME_EPOCHS = 6      # 6 more epochs on top of the saved epoch-6 checkpoint

BASELINE   = {"task1": 0.8682, "task2": None}


# ── Data loading ──────────────────────────────────────────────────────────────
def load_data(task):
    # Automatically use the augmented dataset if it exists
    train_file = f"{task}_train_augmented.csv"
    if not os.path.exists(os.path.join(DATA_DIR, train_file)):
        train_file = f"{task}_train.csv"
        
    train_df = pd.read_csv(os.path.join(DATA_DIR, train_file),
                           dtype={"text": str, "label_idx": int})
    test_df  = pd.read_csv(os.path.join(DATA_DIR, f"{task}_test.csv"),
                           dtype={"text": str, "label_idx": int})
    with open(os.path.join(DATA_DIR, f"{task}_idx_to_code.json")) as f:
        idx_to_code = {int(k): v for k, v in json.load(f).items()}
    num_labels = train_df["label_idx"].nunique()
    return train_df, test_df, idx_to_code, num_labels


# ── Dataset ───────────────────────────────────────────────────────────────────
import torch
from torch.utils.data import Dataset as TorchDataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import get_linear_schedule_with_warmup
from transformers.optimization import Adafactor


class GECSDataset(TorchDataset):
    def __init__(self, texts, labels, tokenizer):
        self.encodings = tokenizer(
            texts,
            truncation=True,
            padding="max_length",
            max_length=MAX_LEN,
            return_tensors="pt"
        )
        self.labels = torch.tensor(labels, dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {k: v[idx] for k, v in self.encodings.items()
                if k in ("input_ids", "attention_mask")}
        item["labels"] = self.labels[idx]
        return item


# ── Training loop (with gradient accumulation) ────────────────────────────────
def train_epoch(model, loader, optimizer, scheduler, device,
                epoch, total_opt_steps, class_weights):
    model.train()
    total_loss = 0.0
    window_loss = 0.0
    opt_step = 0
    start = time.time()
    steps_per_epoch = len(loader)
    
    loss_fct = torch.nn.CrossEntropyLoss(weight=class_weights)

    for step, batch in enumerate(loader):
        batch  = {k: v.to(device) for k, v in batch.items()}
        
        # Manually calculate loss to apply class weights
        logits = model(**batch).logits
        loss = loss_fct(logits, batch["labels"]) / GRAD_ACCUM
        
        loss.backward()

        total_loss  += loss.item() * GRAD_ACCUM
        window_loss += loss.item() * GRAD_ACCUM

        is_last_step      = (step + 1) == steps_per_epoch
        is_accum_boundary = (step + 1) % GRAD_ACCUM == 0

        if is_accum_boundary or is_last_step:
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad(set_to_none=True)
            opt_step += 1

            # periodic cache clear inside the epoch — prevents fragmentation OOM
            if device == "cuda" and opt_step % EMPTY_CACHE_EVERY == 0:
                torch.cuda.empty_cache()

            global_opt_step = (epoch - 1) * (steps_per_epoch // GRAD_ACCUM) + opt_step

            if opt_step % LOG_EVERY == 0 or is_last_step:
                # average raw loss over the reporting window
                window_steps = LOG_EVERY * GRAD_ACCUM if opt_step % LOG_EVERY == 0 \
                               else (step + 1) % (LOG_EVERY * GRAD_ACCUM) or LOG_EVERY * GRAD_ACCUM
                avg = window_loss / window_steps
                elapsed = time.time() - start
                pct = global_opt_step / total_opt_steps * 100
                print(f"  Epoch {epoch} | opt-step {opt_step}/{steps_per_epoch // GRAD_ACCUM} | "
                      f"loss {avg:.4f} | lr {scheduler.get_last_lr()[0]:.2e} | "
                      f"{pct:.1f}% done | {elapsed/60:.1f}min", flush=True)
                window_loss = 0.0

    return total_loss / steps_per_epoch


# ── Evaluation ────────────────────────────────────────────────────────────────
def evaluate(model, loader, device):
    model.eval()
    all_preds, all_labels = [], []

    with torch.no_grad():
        for batch in loader:
            batch   = {k: v.to(device) for k, v in batch.items()}
            labels  = batch.pop("labels")
            logits  = model(**batch).logits
            preds   = logits.argmax(dim=-1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    macro_f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)
    return macro_f1, all_preds, all_labels


# ── Main ──────────────────────────────────────────────────────────────────────
def main(task, resume=False):
    print("=" * 60)
    print(f"Training DeBERTa-v3-small on {task}"
          + (" (resuming from checkpoint)" if resume else ""))
    print("=" * 60)

    torch.manual_seed(SEED)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        vram = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"GPU : {torch.cuda.get_device_name(0)} ({vram:.1f} GB VRAM)")
    else:
        print("CPU mode — will be slow")

    print("Loading data ...", flush=True)
    train_df, test_df, idx_to_code, num_labels = load_data(task)
    print(f"Train: {len(train_df)} rows | Test: {len(test_df)} rows | Classes: {num_labels}")

    print("Calculating class weights ...", flush=True)
    counts = train_df["label_idx"].value_counts().sort_index().values
    total_samples = len(train_df)
    class_weights_np = total_samples / (num_labels * counts)
    class_weights = torch.tensor(class_weights_np, dtype=torch.float32).to(device)

    print("Loading tokenizer ...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True,
                                               fix_mistral_regex=True)

    print("Tokenizing ...", flush=True)
    train_ds = GECSDataset(train_df["text"].tolist(), train_df["label_idx"].tolist(), tokenizer)
    test_ds  = GECSDataset(test_df["text"].tolist(),  test_df["label_idx"].tolist(),  tokenizer)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,
                              num_workers=0, pin_memory=False)
    test_loader  = DataLoader(test_ds,  batch_size=EVAL_BS, shuffle=False,
                              num_workers=0, pin_memory=False)

    # when resuming, load the saved best checkpoint instead of the base model
    if resume:
        ckpt_path = os.path.join(RESULTS, f"{task}_best_model")
        if not os.path.isdir(ckpt_path):
            raise FileNotFoundError(
                f"No checkpoint found at {ckpt_path}. Run without --resume first.")
        print(f"Loading checkpoint from {ckpt_path} ...", flush=True)
        model = AutoModelForSequenceClassification.from_pretrained(
            ckpt_path, num_labels=num_labels, local_files_only=True
        )
    else:
        print(f"Loading model ({num_labels} labels) ...", flush=True)
        model = AutoModelForSequenceClassification.from_pretrained(
            MODEL_PATH, num_labels=num_labels,
            ignore_mismatched_sizes=True, local_files_only=True
        )
    model.to(device)
    model.gradient_checkpointing_enable()   # trade compute for VRAM on resume runs

    active_epochs = RESUME_EPOCHS if resume else EPOCHS
    active_lr     = RESUME_LR if resume else LR

    # Adafactor when resuming: stores no fp32 momentum tensors — saves ~500 MB VRAM
    # vs AdamW which keeps m+v for every parameter (~688 MB on deberta-v3-small).
    warmup_steps = 0
    if resume:
        optimizer = Adafactor(
            model.parameters(),
            lr=active_lr,
            scale_parameter=False,
            relative_step=False,
            warmup_init=False,
            weight_decay=0.01,
        )
        scheduler = get_linear_schedule_with_warmup(optimizer, 0,
                        len(train_loader) // GRAD_ACCUM * active_epochs)
    else:
        no_decay = ["bias", "LayerNorm.weight"]
        params = [
            {"params": [p for n, p in model.named_parameters() if not any(nd in n for nd in no_decay)],
             "weight_decay": 0.01},
            {"params": [p for n, p in model.named_parameters() if     any(nd in n for nd in no_decay)],
             "weight_decay": 0.0},
        ]
        optimizer = torch.optim.AdamW(params, lr=active_lr, foreach=False)
        opt_steps_per_epoch = len(train_loader) // GRAD_ACCUM
        total_opt_steps     = opt_steps_per_epoch * active_epochs
        warmup_steps        = int(WARMUP_PCT * total_opt_steps)
        scheduler = get_linear_schedule_with_warmup(optimizer, warmup_steps, total_opt_steps)

    opt_steps_per_epoch = len(train_loader) // GRAD_ACCUM
    total_opt_steps     = opt_steps_per_epoch * active_epochs

    eff_batch = BATCH_SIZE * GRAD_ACCUM
    print(f"\nStarting training — {active_epochs} epochs | physical batch {BATCH_SIZE} | "
          f"effective batch {eff_batch} | lr {active_lr:.0e} | "
          f"opt-steps {total_opt_steps} | warmup {warmup_steps}", flush=True)

    best_f1, best_epoch = 0.0, 0

    for epoch in range(1, active_epochs + 1):
        gc.collect()
        torch.cuda.empty_cache()
        print(f"\n--- Epoch {epoch}/{active_epochs} ---", flush=True)
        avg_loss = train_epoch(model, train_loader, optimizer, scheduler,
                               device, epoch, total_opt_steps, class_weights)

        torch.cuda.empty_cache()
        macro_f1, _, _ = evaluate(model, test_loader, device)
        torch.cuda.empty_cache()
        print(f"  Epoch {epoch} complete | avg loss {avg_loss:.4f} | Macro F1: {macro_f1*100:.2f}%",
              flush=True)

        if macro_f1 > best_f1:
            best_f1    = macro_f1
            best_epoch = epoch
            ckpt = os.path.join(RESULTS, f"{task}_best_model")
            model.save_pretrained(ckpt)
            tokenizer.save_pretrained(ckpt)
            print(f"  New best — saved to {ckpt}", flush=True)

    # Final evaluation using best checkpoint
    print(f"\nLoading best checkpoint (epoch {best_epoch}) ...", flush=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        os.path.join(RESULTS, f"{task}_best_model"),
        num_labels=num_labels, local_files_only=True
    ).to(device)

    final_f1, y_pred, y_true = evaluate(model, test_loader, device)
    baseline = BASELINE[task]

    print("\n" + "=" * 60)
    if baseline:
        delta = final_f1 - baseline
        print(f"  Baseline (TF-IDF + SVM) : {baseline*100:.2f}%")
        print(f"  DeBERTa-v3-small        : {final_f1*100:.2f}%")
        print(f"  Delta                   : {delta*100:+.2f}%")
        print("  Baseline beaten." if delta > 0 else "  Did not beat baseline.")
    else:
        print(f"  DeBERTa-v3-small Macro F1: {final_f1*100:.2f}%")
    print("=" * 60)

    present_labels = sorted(set(y_true) | set(y_pred))
    target_names   = [str(idx_to_code[i]) for i in present_labels]
    per_class      = classification_report(y_true, y_pred, labels=present_labels,
                                           target_names=target_names,
                                           output_dict=True, zero_division=0)
    summary = {
        "task": task, "model": "deberta-v3-small",
        "max_len": MAX_LEN, "epochs": EPOCHS,
        "batch_size": BATCH_SIZE, "grad_accum": GRAD_ACCUM,
        "effective_batch_size": BATCH_SIZE * GRAD_ACCUM,
        "learning_rate": LR, "num_labels": num_labels,
        "baseline_macro_f1": baseline,
        "deberta_macro_f1": round(final_f1, 6),
        "delta": round(final_f1 - baseline, 6) if baseline else None,
        "best_epoch": best_epoch,
        "per_class": per_class,
    }

    out_path = os.path.join(RESULTS, f"{task}_results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=["task1", "task2"], default="task1")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from saved best checkpoint instead of base model")
    args = parser.parse_args()
    main(args.task, resume=args.resume)
