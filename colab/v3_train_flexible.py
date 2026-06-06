"""COLAB CELL — flexible v3 ModernBERT-large trainer for Task 1.

Paste this entire file into a single Colab cell. Set the CONFIG block at the top
to control variant. You can launch 3+ parallel notebooks with different CONFIGs.

VARIANTS this script supports (set in CONFIG):
  RUN_NAME              — output folder name on Drive
  TRAIN_CSV             — which training file to use:
                            "raw"            -> /content/task1_train.csv
                            "segment_aware"  -> /content/task1_segment_aware_train.csv
  TEXT_FIELD            — column to use as input ("text", "text_joint", "text_primary")
  USE_SAMPLE_WEIGHT     — True/False, multiply per-row CE loss by sample_weight col
  SEED                  — random seed (42, 123, 7, ...)
  EPOCHS                — number of training epochs
  USE_DISTILLATION      — True/False, add KL loss on rows present in distill jsonl
  DISTILL_JSONL_PATH    — path to teacher reasoning jsonl (if USE_DISTILLATION)
  DISTILL_WEIGHT        — weight on KL loss vs CE
  SAVE_TOPK_AND_EMBEDS  — True to also extract test top-5 + train/test CLS embeds
                          (use for the final ensemble / cascade work)

Outputs to /content/drive/MyDrive/{RUN_NAME}/:
  best_model_state.pt
  test_predictions_topk.csv     (always)
  train_cls.npy, test_cls.npy   (if SAVE_TOPK_AND_EMBEDS)
  train_meta.csv, test_meta.csv (if SAVE_TOPK_AND_EMBEDS)
  industry_classes.npy
  final_summary.json
"""

# ============================================================================
# CONFIG — EDIT THIS BLOCK PER NOTEBOOK
# ============================================================================
CONFIG = {
    "RUN_NAME": "v3_segment_aware_seed42",   # CHANGE per notebook
    "TRAIN_CSV": "segment_aware",             # "raw" or "segment_aware"
    "TEXT_FIELD": "text_joint",               # "text", "text_joint", "text_primary"
    "USE_SAMPLE_WEIGHT": True,
    "SEED": 42,
    "EPOCHS": 10,
    "USE_DISTILLATION": False,
    "DISTILL_JSONL_PATH": "/content/reasoning_chains.jsonl",
    "DISTILL_WEIGHT": 0.3,
    "SAVE_TOPK_AND_EMBEDS": True,
}

# Suggested launches — copy-paste a CONFIG block into each notebook:
SUGGESTED = """
# Notebook 1 — segment-aware baseline (biggest single lever)
CONFIG = {"RUN_NAME":"v3_segaware",        "TRAIN_CSV":"segment_aware","TEXT_FIELD":"text_joint",
          "USE_SAMPLE_WEIGHT":True,  "SEED":42,  "EPOCHS":10, "USE_DISTILLATION":False,
          "DISTILL_JSONL_PATH":"/content/reasoning_chains.jsonl","DISTILL_WEIGHT":0.3,
          "SAVE_TOPK_AND_EMBEDS":True}

# Notebook 2 — multi-seed v3 (different seed, raw text, no sample weight = matches v3)
CONFIG = {"RUN_NAME":"v3_seed123",         "TRAIN_CSV":"raw","TEXT_FIELD":"text",
          "USE_SAMPLE_WEIGHT":False, "SEED":123, "EPOCHS":10, "USE_DISTILLATION":False,
          "DISTILL_JSONL_PATH":"/content/reasoning_chains.jsonl","DISTILL_WEIGHT":0.3,
          "SAVE_TOPK_AND_EMBEDS":True}

# Notebook 3 — distillation
CONFIG = {"RUN_NAME":"v3_distill",         "TRAIN_CSV":"raw","TEXT_FIELD":"text",
          "USE_SAMPLE_WEIGHT":False, "SEED":42,  "EPOCHS":10, "USE_DISTILLATION":True,
          "DISTILL_JSONL_PATH":"/content/reasoning_chains.jsonl","DISTILL_WEIGHT":0.3,
          "SAVE_TOPK_AND_EMBEDS":True}

# Notebook 4 — segment-aware + seed 7 (more diversity for ensemble)
CONFIG = {"RUN_NAME":"v3_segaware_seed7",  "TRAIN_CSV":"segment_aware","TEXT_FIELD":"text_joint",
          "USE_SAMPLE_WEIGHT":True,  "SEED":7,   "EPOCHS":10, "USE_DISTILLATION":False,
          "DISTILL_JSONL_PATH":"/content/reasoning_chains.jsonl","DISTILL_WEIGHT":0.3,
          "SAVE_TOPK_AND_EMBEDS":True}
"""

# ============================================================================
# 1. Setup
# ============================================================================
import os, json, random, gc
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from transformers import AutoModel, AutoTokenizer, get_cosine_schedule_with_warmup
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import f1_score, accuracy_score
from datasets import Dataset
from tqdm.auto import tqdm
from collections import Counter

from google.colab import drive
drive.mount('/content/drive', force_remount=False)

SEED = CONFIG["SEED"]
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)

MODEL_NAME = "answerdotai/ModernBERT-large"
MAX_LEN = 512
BATCH_SIZE = 8
GRAD_ACCUM = 8
ENCODER_LR = 5e-6
HEAD_LR = 5e-4
WARMUP_RATIO = 0.05
LABEL_SMOOTHING = 0.02

DRIVE_OUT = Path("/content/drive/MyDrive") / CONFIG["RUN_NAME"]
DRIVE_OUT.mkdir(parents=True, exist_ok=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
USE_BF16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
autocast_dtype = torch.bfloat16 if USE_BF16 else torch.float16
print(f"Device: {device}  bf16: {USE_BF16}")
print(f"Run: {CONFIG['RUN_NAME']}  Seed: {SEED}  Epochs: {CONFIG['EPOCHS']}")
print(f"Train CSV: {CONFIG['TRAIN_CSV']}  Text: {CONFIG['TEXT_FIELD']}  SW: {CONFIG['USE_SAMPLE_WEIGHT']}")

# ============================================================================
# 2. Load training data based on variant
# ============================================================================
def norm_code(v): return str(int(v)).zfill(8)

if CONFIG["TRAIN_CSV"] == "segment_aware":
    train_path = "/content/task1_segment_aware_train.csv"
    test_path = "/content/task1_segment_aware_test.csv"
    assert Path(train_path).exists(), f"Upload {train_path} (from llm_finetuning/data/segment_aware_task1/)"
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    train_df["industry_code"] = train_df["code"].map(norm_code)
    test_df["industry_code"] = test_df["code"].map(norm_code)
    train_df["text"] = train_df[CONFIG["TEXT_FIELD"]]
    test_df["text"] = test_df[CONFIG["TEXT_FIELD"]]
    if not CONFIG["USE_SAMPLE_WEIGHT"]:
        train_df["sample_weight"] = 1.0
else:
    train_path = "/content/task1_train.csv"
    test_path = "/content/task1_test.csv"
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    train_df["industry_code"] = train_df["mstar_code"].map(norm_code)
    test_df["industry_code"] = test_df["mstar_code"].map(norm_code)
    train_df["text"] = train_df["text"].astype(str)
    test_df["text"] = test_df["text"].astype(str)
    train_df["sample_weight"] = 1.0
    test_df["sample_weight"] = 1.0

for f in (train_df, test_df):
    f["text"] = f["text"].fillna("").astype(str).str.replace("\n", " ").str.strip()
    f["sector_code"] = f["industry_code"].str[:3]
    f["group_code"] = f["industry_code"].str[:5]

train_df = train_df[train_df["text"].str.len() > 0].reset_index(drop=True)
test_df = test_df[test_df["text"].str.len() > 0].reset_index(drop=True)

le_sector = LabelEncoder().fit(pd.concat([train_df["sector_code"], test_df["sector_code"]]))
le_group = LabelEncoder().fit(pd.concat([train_df["group_code"], test_df["group_code"]]))
le_industry = LabelEncoder().fit(pd.concat([train_df["industry_code"], test_df["industry_code"]]))

for f in (train_df, test_df):
    f["sector_idx"] = le_sector.transform(f["sector_code"])
    f["group_idx"] = le_group.transform(f["group_code"])
    f["industry_idx"] = le_industry.transform(f["industry_code"])

N_SECTORS = len(le_sector.classes_)
N_GROUPS = len(le_group.classes_)
N_INDUSTRIES = len(le_industry.classes_)
print(f"label spaces: sec={N_SECTORS} grp={N_GROUPS} ind={N_INDUSTRIES}")
print(f"train: {len(train_df)} rows | test: {len(test_df)} rows")

# Dev split — stratified
from sklearn.model_selection import train_test_split
try:
    train_fit_df, dev_df = train_test_split(train_df, test_size=0.10, random_state=SEED,
                                             stratify=train_df["industry_code"])
except ValueError:
    train_fit_df, dev_df = train_test_split(train_df, test_size=0.10, random_state=SEED, shuffle=True)
train_fit_df = train_fit_df.reset_index(drop=True)
dev_df = dev_df.reset_index(drop=True)

# Distillation: optional teacher soft targets
distill_idx_to_probs = {}
if CONFIG["USE_DISTILLATION"]:
    if Path(CONFIG["DISTILL_JSONL_PATH"]).exists():
        with open(CONFIG["DISTILL_JSONL_PATH"]) as fh:
            for line in fh:
                if not line.strip(): continue
                row = json.loads(line)
                # Only use rows where teacher's prediction matches truth (high quality)
                if row.get("teacher_correct") and row.get("text"):
                    # Build a 1-hot soft target on the teacher's predicted code
                    code = norm_code(row.get("teacher_pred", row.get("true_code")))
                    if code in le_industry.classes_:
                        idx = int(le_industry.transform([code])[0])
                        distill_idx_to_probs[row["text"][:200]] = idx
        print(f"Loaded {len(distill_idx_to_probs)} distillation entries")
    else:
        print(f"WARN: distill jsonl not found at {CONFIG['DISTILL_JSONL_PATH']}, disabling")
        CONFIG["USE_DISTILLATION"] = False

# Hierarchy maps
industry_to_group_idx = torch.tensor(
    [int(le_group.transform([c[:5]])[0]) for c in le_industry.classes_],
    dtype=torch.long, device=device)
industry_to_sector_idx = torch.tensor(
    [int(le_sector.transform([c[:3]])[0]) for c in le_industry.classes_],
    dtype=torch.long, device=device)

# ============================================================================
# 3. Tokenizer + datasets
# ============================================================================
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)

def to_dataset(df, include_weight=True):
    cols = ["text", "sector_idx", "group_idx", "industry_idx"]
    if include_weight: cols.append("sample_weight")
    return Dataset.from_pandas(df[cols].reset_index(drop=True), preserve_index=False)

def tokenize_batch(batch):
    return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=MAX_LEN)

train_ds = to_dataset(train_fit_df).map(tokenize_batch, batched=True, remove_columns=["text"])
dev_ds = to_dataset(dev_df).map(tokenize_batch, batched=True, remove_columns=["text"])
test_ds = to_dataset(test_df).map(tokenize_batch, batched=True, remove_columns=["text"])

cols_torch = ["input_ids", "attention_mask", "sector_idx", "group_idx", "industry_idx", "sample_weight"]
train_ds.set_format(type="torch", columns=cols_torch)
dev_ds.set_format(type="torch", columns=cols_torch)
test_ds.set_format(type="torch", columns=cols_torch)

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=2, pin_memory=True)
dev_loader = DataLoader(dev_ds, batch_size=BATCH_SIZE*2, shuffle=False, num_workers=2, pin_memory=True)
test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE*2, shuffle=False, num_workers=2, pin_memory=True)

# ============================================================================
# 4. Model
# ============================================================================
class MultiTaskModernBERT(nn.Module):
    def __init__(self, model_name, n_sectors, n_groups, n_industries, dropout=0.10):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name, trust_remote_code=True)
        hidden = self.encoder.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.norm = nn.LayerNorm(hidden)
        self.sector_head = nn.Linear(hidden, n_sectors)
        self.group_head = nn.Linear(hidden, n_groups)
        self.industry_head = nn.Linear(hidden, n_industries)

    def forward(self, input_ids, attention_mask, return_pooled=False):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled_raw = (outputs.pooler_output if getattr(outputs, "pooler_output", None) is not None
                      else outputs.last_hidden_state[:, 0])
        pooled = self.dropout(self.norm(pooled_raw))
        out = {
            "sector_logits": self.sector_head(pooled),
            "group_logits": self.group_head(pooled),
            "industry_logits": self.industry_head(pooled),
        }
        if return_pooled: out["pooled"] = self.norm(pooled_raw)
        return out

model = MultiTaskModernBERT(MODEL_NAME, N_SECTORS, N_GROUPS, N_INDUSTRIES).to(device)

# Effective-num class weights
def effective_num_weights(labels, num_classes, beta=0.9997, power=0.45):
    counts = np.bincount(labels, minlength=num_classes).astype(np.float64)
    eff_num = 1.0 - np.power(beta, counts)
    weights = (1.0 - beta) / np.clip(eff_num, 1e-12, None)
    weights = np.power(weights, power)
    return torch.tensor(weights / weights.mean(), dtype=torch.float32)

sector_w = effective_num_weights(train_fit_df["sector_idx"].to_numpy(), N_SECTORS, beta=0.999, power=0.25).to(device)
group_w = effective_num_weights(train_fit_df["group_idx"].to_numpy(), N_GROUPS, beta=0.9995, power=0.35).to(device)
industry_w = effective_num_weights(train_fit_df["industry_idx"].to_numpy(), N_INDUSTRIES).to(device)

# Loss = weighted CE per task, multiplied by sample_weight per row, summed with task weights
ce_sector = nn.CrossEntropyLoss(weight=sector_w, reduction="none", label_smoothing=LABEL_SMOOTHING)
ce_group = nn.CrossEntropyLoss(weight=group_w, reduction="none", label_smoothing=LABEL_SMOOTHING)
ce_industry = nn.CrossEntropyLoss(weight=industry_w, reduction="none", label_smoothing=LABEL_SMOOTHING)
alpha, beta_t, gamma = 0.2, 0.3, 0.5

# Optimizer with parameter groups
encoder_params, head_params = [], []
for n, p in model.named_parameters():
    (head_params if any(h in n for h in ["sector_head","group_head","industry_head","norm"]) else encoder_params).append(p)
optimizer = torch.optim.AdamW([
    {"params": encoder_params, "lr": ENCODER_LR},
    {"params": head_params,    "lr": HEAD_LR},
], weight_decay=0.01)

steps_per_epoch = max(1, len(train_loader) // GRAD_ACCUM)
total_steps = steps_per_epoch * CONFIG["EPOCHS"]
warmup_steps = int(total_steps * WARMUP_RATIO)
scheduler = get_cosine_schedule_with_warmup(optimizer, warmup_steps, total_steps)

# ============================================================================
# 5. Training loop with sample weights + early stopping
# ============================================================================
best_dev_f1 = -1.0
patience_left = 3
history = []

def eval_loader(loader):
    model.eval()
    true_idx, pred_idx = [], []
    with torch.no_grad():
        for batch in loader:
            ids = batch["input_ids"].to(device, non_blocking=True)
            mask = batch["attention_mask"].to(device, non_blocking=True)
            with torch.autocast(device_type="cuda", dtype=autocast_dtype, enabled=USE_BF16):
                out = model(ids, mask)
            true_idx.extend(batch["industry_idx"].numpy().tolist())
            pred_idx.extend(out["industry_logits"].argmax(dim=-1).cpu().numpy().tolist())
    true_codes = le_industry.inverse_transform(true_idx)
    pred_codes = le_industry.inverse_transform(pred_idx)
    return f1_score(true_codes, pred_codes, average="macro", zero_division=0), accuracy_score(true_codes, pred_codes)

print(f"\nTraining {CONFIG['EPOCHS']} epochs")
optimizer.zero_grad()
for epoch in range(1, CONFIG["EPOCHS"]+1):
    model.train()
    losses = []
    pbar = tqdm(train_loader, desc=f"epoch {epoch}", leave=False)
    for step, batch in enumerate(pbar):
        ids = batch["input_ids"].to(device, non_blocking=True)
        mask = batch["attention_mask"].to(device, non_blocking=True)
        sec = batch["sector_idx"].to(device, non_blocking=True)
        grp = batch["group_idx"].to(device, non_blocking=True)
        ind = batch["industry_idx"].to(device, non_blocking=True)
        sw = batch["sample_weight"].to(device, non_blocking=True).float()
        with torch.autocast(device_type="cuda", dtype=autocast_dtype, enabled=USE_BF16):
            out = model(ids, mask)
            loss_s = (ce_sector(out["sector_logits"], sec) * sw).mean()
            loss_g = (ce_group(out["group_logits"], grp) * sw).mean()
            loss_i = (ce_industry(out["industry_logits"], ind) * sw).mean()
            loss = (alpha*loss_s + beta_t*loss_g + gamma*loss_i) / GRAD_ACCUM
        loss.backward()
        if (step+1) % GRAD_ACCUM == 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step(); scheduler.step(); optimizer.zero_grad()
        losses.append(loss.item()*GRAD_ACCUM)
        if step % 50 == 0: pbar.set_postfix(loss=f"{np.mean(losses[-50:]):.3f}")
    dev_f1, dev_acc = eval_loader(dev_loader)
    print(f"epoch {epoch}: train_loss={np.mean(losses):.4f}  dev_f1={dev_f1:.4%}  dev_acc={dev_acc:.4%}")
    history.append({"epoch": epoch, "train_loss": float(np.mean(losses)), "dev_f1": float(dev_f1), "dev_acc": float(dev_acc)})
    if dev_f1 > best_dev_f1 + 0.001:
        best_dev_f1 = dev_f1
        torch.save(model.state_dict(), DRIVE_OUT / "best_model_state.pt")
        patience_left = 3
        print(f"  saved best @ epoch {epoch}")
    else:
        patience_left -= 1
        if patience_left <= 0:
            print(f"  early stop @ epoch {epoch}")
            break

# Load best
model.load_state_dict(torch.load(DRIVE_OUT / "best_model_state.pt", map_location=device))
model.eval()

# ============================================================================
# 6. Test inference with top-k + optionally embeddings
# ============================================================================
def hierarchy_scores(out, lg=0.3, ls=0.03):
    ip = F.log_softmax(out["industry_logits"], dim=-1)
    gp = F.log_softmax(out["group_logits"], dim=-1)
    sp = F.log_softmax(out["sector_logits"], dim=-1)
    return ip + lg*gp[:, industry_to_group_idx] + ls*sp[:, industry_to_sector_idx]

@torch.no_grad()
def run_inference(loader, save_embeds=False):
    all_top5_idx, all_top5_p, all_true, all_emb = [], [], [], ([] if save_embeds else None)
    for batch in tqdm(loader, leave=False):
        ids = batch["input_ids"].to(device, non_blocking=True)
        mask = batch["attention_mask"].to(device, non_blocking=True)
        with torch.autocast(device_type="cuda", dtype=autocast_dtype, enabled=USE_BF16):
            out = model(ids, mask, return_pooled=save_embeds)
            scores = hierarchy_scores(out)
        probs = scores.softmax(dim=-1).float()
        tp, ti = probs.topk(5, dim=-1)
        all_top5_idx.append(ti.cpu().numpy()); all_top5_p.append(tp.cpu().numpy())
        all_true.append(batch["industry_idx"].numpy())
        if save_embeds: all_emb.append(out["pooled"].float().cpu().numpy().astype(np.float16))
    top5_idx = np.concatenate(all_top5_idx); top5_p = np.concatenate(all_top5_p)
    true_idx = np.concatenate(all_true)
    emb = np.concatenate(all_emb) if save_embeds else None
    return true_idx, top5_idx, top5_p, emb

print("\n=== Test inference ===")
test_true, test_top5, test_top5p, test_emb = run_inference(test_loader, save_embeds=CONFIG["SAVE_TOPK_AND_EMBEDS"])

true_codes = le_industry.inverse_transform(test_true)
pred_codes = le_industry.inverse_transform(test_top5[:, 0])
test_f1 = f1_score(true_codes, pred_codes, average="macro", zero_division=0)
test_acc = accuracy_score(true_codes, pred_codes)
print(f"TEST: macro F1 = {test_f1:.4%}  acc = {test_acc:.4%}")

# Save top-k CSV
top5_codes = np.array([le_industry.inverse_transform(r) for r in test_top5])
out = pd.DataFrame({
    "true_code": true_codes, "pred_code": pred_codes,
    **{f"top{i+1}_code": top5_codes[:,i] for i in range(5)},
    **{f"top{i+1}_prob": test_top5p[:,i] for i in range(5)},
})
out.to_csv(DRIVE_OUT / "test_predictions_topk.csv", index=False)

# Save embeds + meta
if CONFIG["SAVE_TOPK_AND_EMBEDS"]:
    np.save(DRIVE_OUT / "test_cls.npy", test_emb)
    print(f"saved test_cls.npy {test_emb.shape}")
    print("Extracting train embeds...")
    train_full_ds = to_dataset(train_df).map(tokenize_batch, batched=True, remove_columns=["text"])
    train_full_ds.set_format(type="torch", columns=cols_torch)
    train_full_loader = DataLoader(train_full_ds, batch_size=BATCH_SIZE*2, shuffle=False, num_workers=2, pin_memory=True)
    _, _, _, train_emb = run_inference(train_full_loader, save_embeds=True)
    np.save(DRIVE_OUT / "train_cls.npy", train_emb)
    print(f"saved train_cls.npy {train_emb.shape}")
    train_df[["industry_code","sector_code","group_code"]].rename(columns={"industry_code":"mstar_code"}).to_csv(DRIVE_OUT/"train_meta.csv", index=False)
    test_df[["industry_code","sector_code","group_code"]].rename(columns={"industry_code":"mstar_code"}).to_csv(DRIVE_OUT/"test_meta.csv", index=False)

np.save(DRIVE_OUT / "industry_classes.npy", le_industry.classes_)

# Final summary
counts = Counter(true_codes)
top10 = [c for c, _ in counts.most_common(10)]
top10_f1 = f1_score(true_codes, pred_codes, average=None, labels=top10, zero_division=0)
top10_pass = int(sum(s > 0.85 for s in top10_f1))
tail = [c for c, sup in counts.items() if sup <= 50]
tail_f1 = f1_score(true_codes, pred_codes, average="macro", labels=tail, zero_division=0) if tail else 0.0

summary = {
    "config": CONFIG,
    "best_dev_macro_f1": float(best_dev_f1),
    "test_macro_f1": float(test_f1),
    "test_acc": float(test_acc),
    "tail_f1_classes_le_50": float(tail_f1),
    "tail_class_count": len(tail),
    "top10_pass": top10_pass,
    "top10_breakdown": [{"code": c, "f1": float(s), "support": int(counts[c])} for c, s in zip(top10, top10_f1)],
    "history": history,
}
with open(DRIVE_OUT / "final_summary.json", "w") as fh: json.dump(summary, fh, indent=2)
print(json.dumps(summary, indent=2)[:3000])
print(f"\nDONE. Files in {DRIVE_OUT}")
