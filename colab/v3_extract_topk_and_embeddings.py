"""COLAB CELL — re-run v3 inference with top-5 + extract CLS embeddings.

Paste this entire file into a single new Colab cell, on a fresh runtime with the
same task1_train.csv / task1_test.csv uploaded to /content/.

Requires:
  /content/task1_train.csv
  /content/task1_test.csv
  /content/drive/MyDrive/v3_minimal/best_model_state.pt   (your saved checkpoint)

Outputs (saved to /content/drive/MyDrive/v3_minimal/):
  test_predictions_topk.csv      — true_code, pred_code, top1..top5 codes & probs
  train_cls.npy                  — (n_train, 1024) float16 CLS embeddings
  test_cls.npy                   — (n_test,  1024) float16 CLS embeddings
  train_meta.csv                 — mstar_code, sector_code, group_code per row
  test_meta.csv                  — same schema
  industry_classes.npy           — label-encoder class order (idx -> mstar_code)

Total runtime on Colab Pro+ A100: ~10-15 min (mostly inference).
"""
# ============================================================================
# 1. Setup
# ============================================================================
import os, json, gc
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from transformers import AutoModel, AutoTokenizer
from sklearn.preprocessing import LabelEncoder
from datasets import Dataset
from tqdm.auto import tqdm

from google.colab import drive
drive.mount('/content/drive', force_remount=False)

# ============================================================================
# 2. Paths / config — must match training
# ============================================================================
MODEL_NAME = "answerdotai/ModernBERT-large"
MAX_LEN = 512
BATCH_SIZE = 16  # bigger than training because no gradients

DRIVE_DIR = Path("/content/drive/MyDrive/v3_minimal")
DRIVE_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT = Path("/content/drive/MyDrive/best_model_state_v3.pt")  # where you saved it

# Tuned hierarchy weights from your v3 run
LAMBDA_GROUP = 0.3
LAMBDA_SECTOR = 0.03

assert CHECKPOINT.exists(), f"Missing checkpoint at {CHECKPOINT}"
assert Path("/content/task1_train.csv").exists(), "Upload task1_train.csv first"
assert Path("/content/task1_test.csv").exists(), "Upload task1_test.csv first"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("device:", device, "| checkpoint:", CHECKPOINT)

# ============================================================================
# 3. Rebuild label encoders deterministically from CSVs (same as training)
# ============================================================================
def norm_code(value):
    return str(int(value)).zfill(8)

def clean_text(value):
    text = str(value or "").replace("\n", " ")
    return " ".join(text.split())

train_df = pd.read_csv("/content/task1_train.csv")
test_df = pd.read_csv("/content/task1_test.csv")

for frame in (train_df, test_df):
    frame["text"] = frame["text"].map(clean_text)
    frame["industry_code"] = frame["mstar_code"].map(norm_code)
    frame["sector_code"] = frame["industry_code"].str[:3]
    frame["group_code"] = frame["industry_code"].str[:5]

train_df = (
    train_df[train_df["text"].str.len() > 0]
    .drop_duplicates(subset=["text", "industry_code"])
    .reset_index(drop=True)
    .copy()
)
test_df = test_df[test_df["text"].str.len() > 0].reset_index(drop=True).copy()

le_sector = LabelEncoder().fit(pd.concat([train_df["sector_code"], test_df["sector_code"]]))
le_group = LabelEncoder().fit(pd.concat([train_df["group_code"], test_df["group_code"]]))
le_industry = LabelEncoder().fit(pd.concat([train_df["industry_code"], test_df["industry_code"]]))

for frame in (train_df, test_df):
    frame["sector_idx"] = le_sector.transform(frame["sector_code"])
    frame["group_idx"] = le_group.transform(frame["group_code"])
    frame["industry_idx"] = le_industry.transform(frame["industry_code"])

N_SECTORS = len(le_sector.classes_)
N_GROUPS = len(le_group.classes_)
N_INDUSTRIES = len(le_industry.classes_)
print(f"label spaces: sectors={N_SECTORS} groups={N_GROUPS} industries={N_INDUSTRIES}")
print(f"train: {len(train_df)} rows | test: {len(test_df)} rows")

# Hierarchy mapping for inference
industry_to_group_idx = []
industry_to_sector_idx = []
for code in le_industry.classes_:
    industry_to_group_idx.append(int(le_group.transform([code[:5]])[0]))
    industry_to_sector_idx.append(int(le_sector.transform([code[:3]])[0]))
industry_to_group_idx = torch.tensor(industry_to_group_idx, dtype=torch.long, device=device)
industry_to_sector_idx = torch.tensor(industry_to_sector_idx, dtype=torch.long, device=device)

# ============================================================================
# 4. Tokenize
# ============================================================================
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)

def to_dataset(df):
    return Dataset.from_pandas(
        df[["text", "sector_idx", "group_idx", "industry_idx"]],
        preserve_index=False,
    )

train_ds = to_dataset(train_df)
test_ds = to_dataset(test_df)

def tokenize_batch(batch):
    return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=MAX_LEN)

train_ds = train_ds.map(tokenize_batch, batched=True, remove_columns=["text"])
test_ds = test_ds.map(tokenize_batch, batched=True, remove_columns=["text"])

cols = ["input_ids", "attention_mask", "sector_idx", "group_idx", "industry_idx"]
train_ds.set_format(type="torch", columns=cols)
test_ds.set_format(type="torch", columns=cols)

# CRITICAL: shuffle=False so embeddings stay aligned to train_df / test_df row order
train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=2, pin_memory=True)
test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=2, pin_memory=True)

# ============================================================================
# 5. Model — must match training architecture exactly
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
        pooled_raw = (
            outputs.pooler_output
            if getattr(outputs, "pooler_output", None) is not None
            else outputs.last_hidden_state[:, 0]
        )
        pooled = self.dropout(self.norm(pooled_raw))
        out = {
            "sector_logits": self.sector_head(pooled),
            "group_logits": self.group_head(pooled),
            "industry_logits": self.industry_head(pooled),
        }
        if return_pooled:
            # Return the post-norm vector (input to heads) — what we want for cascade
            out["pooled"] = self.norm(pooled_raw)
        return out

model = MultiTaskModernBERT(MODEL_NAME, N_SECTORS, N_GROUPS, N_INDUSTRIES).to(device)
state = torch.load(CHECKPOINT, map_location=device)
missing, unexpected = model.load_state_dict(state, strict=False)
print(f"loaded checkpoint. missing keys: {len(missing)}, unexpected: {len(unexpected)}")
if missing:   print("  missing:", missing[:5])
if unexpected:print("  unexpected:", unexpected[:5])
model.eval()

# ============================================================================
# 6. Inference + embedding extraction in a single forward pass
# ============================================================================
def hierarchy_scores(outputs, lg=0.0, ls=0.0):
    industry_logp = F.log_softmax(outputs["industry_logits"], dim=-1)
    group_logp = F.log_softmax(outputs["group_logits"], dim=-1)
    sector_logp = F.log_softmax(outputs["sector_logits"], dim=-1)
    return industry_logp + lg * group_logp[:, industry_to_group_idx] + ls * sector_logp[:, industry_to_sector_idx]

@torch.no_grad()
def run(loader, save_embeddings=False):
    all_top5_idx, all_top5_prob, all_true = [], [], []
    all_embeds = [] if save_embeddings else None
    for batch in tqdm(loader, leave=False):
        ids = batch["input_ids"].to(device, non_blocking=True)
        mask = batch["attention_mask"].to(device, non_blocking=True)
        with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
            outputs = model(ids, mask, return_pooled=save_embeddings)
            scores = hierarchy_scores(outputs, LAMBDA_GROUP, LAMBDA_SECTOR)
        probs = scores.softmax(dim=-1).float()
        top5_prob, top5_idx = probs.topk(5, dim=-1)
        all_top5_idx.append(top5_idx.cpu().numpy())
        all_top5_prob.append(top5_prob.cpu().numpy())
        all_true.append(batch["industry_idx"].numpy())
        if save_embeddings:
            all_embeds.append(outputs["pooled"].float().cpu().numpy().astype(np.float16))
    top5_idx = np.concatenate(all_top5_idx, axis=0)
    top5_prob = np.concatenate(all_top5_prob, axis=0)
    true_idx = np.concatenate(all_true, axis=0)
    if save_embeddings:
        embeds = np.concatenate(all_embeds, axis=0)
    else:
        embeds = None
    return true_idx, top5_idx, top5_prob, embeds

# Test set: predictions + embeddings
print("\n=== TEST inference ===")
test_true, test_top5, test_top5p, test_embeds = run(test_loader, save_embeddings=True)
print(f"test embeds: {test_embeds.shape} {test_embeds.dtype}")

# Train set: embeddings only (don't need top5 for cascade training)
print("\n=== TRAIN embedding extraction ===")
_, _, _, train_embeds = run(train_loader, save_embeddings=True)
print(f"train embeds: {train_embeds.shape} {train_embeds.dtype}")

# ============================================================================
# 7. Save everything to Drive
# ============================================================================
DRIVE_DIR.mkdir(parents=True, exist_ok=True)

# Top-5 predictions table
true_codes = le_industry.inverse_transform(test_true)
pred_codes = le_industry.inverse_transform(test_top5[:, 0])  # argmax = first col
top5_codes = np.array([le_industry.inverse_transform(row) for row in test_top5])
out_df = pd.DataFrame({
    "true_code": true_codes,
    "pred_code": pred_codes,
    "top1_code": top5_codes[:, 0], "top1_prob": test_top5p[:, 0],
    "top2_code": top5_codes[:, 1], "top2_prob": test_top5p[:, 1],
    "top3_code": top5_codes[:, 2], "top3_prob": test_top5p[:, 2],
    "top4_code": top5_codes[:, 3], "top4_prob": test_top5p[:, 3],
    "top5_code": top5_codes[:, 4], "top5_prob": test_top5p[:, 4],
})
out_df.to_csv(DRIVE_DIR / "test_predictions_topk.csv", index=False)
print(f"saved {DRIVE_DIR / 'test_predictions_topk.csv'}")

# Embeddings
np.save(DRIVE_DIR / "train_cls.npy", train_embeds)
np.save(DRIVE_DIR / "test_cls.npy", test_embeds)
np.save(DRIVE_DIR / "industry_classes.npy", le_industry.classes_)
print(f"saved train_cls.npy ({train_embeds.shape}) test_cls.npy ({test_embeds.shape})")

# Metadata aligned to embedding row order
train_meta = train_df[["industry_code", "sector_code", "group_code"]].rename(
    columns={"industry_code": "mstar_code"}
)
test_meta = test_df[["industry_code", "sector_code", "group_code"]].rename(
    columns={"industry_code": "mstar_code"}
)
train_meta.to_csv(DRIVE_DIR / "train_meta.csv", index=False)
test_meta.to_csv(DRIVE_DIR / "test_meta.csv", index=False)
print(f"saved train_meta.csv ({len(train_meta)}) test_meta.csv ({len(test_meta)})")

# Quick sanity: re-evaluate from saved predictions to confirm we reproduce 71.03%
from sklearn.metrics import f1_score
sanity_f1 = f1_score(true_codes, pred_codes, average="macro", zero_division=0)
sanity_acc = (true_codes == pred_codes).mean()
print(f"\nSANITY: reproduced macro F1 = {sanity_f1:.4%}, acc = {sanity_acc:.4%}")
print(f"        (your v3 final_summary said 71.0324% F1, 72.2590% acc)")

print("\nDONE. Now download these from Drive to your Windows project folder:")
for f in ["test_predictions_topk.csv", "train_cls.npy", "test_cls.npy",
          "train_meta.csv", "test_meta.csv", "industry_classes.npy"]:
    print(f"  {DRIVE_DIR / f}")
