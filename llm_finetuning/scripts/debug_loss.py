import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import pandas as pd
import numpy as np

DATA_CSV   = r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\data\task1_train.csv"
MODEL_PATH = r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\models\deberta-v3-small"

print("Loading data...", flush=True)
df = pd.read_csv(DATA_CSV, dtype={"text": str, "label_idx": int})
print(f"Rows: {len(df)} | NaN texts: {df['text'].isna().sum()} | NaN labels: {df['label_idx'].isna().sum()}", flush=True)

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

tok = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True, fix_mistral_regex=True)
print(f"Vocab size: {tok.vocab_size}", flush=True)

# Check token IDs from a batch of 8 (same as training batch)
texts  = df["text"].iloc[:8].tolist()
labels = torch.tensor(df["label_idx"].iloc[:8].tolist(), dtype=torch.long)
enc    = tok(texts, truncation=True, padding="max_length", max_length=128, return_tensors="pt")

print(f"input_ids shape : {enc['input_ids'].shape}", flush=True)
print(f"input_ids min   : {enc['input_ids'].min().item()}", flush=True)
print(f"input_ids max   : {enc['input_ids'].max().item()}", flush=True)
print(f"any -1 ids      : {(enc['input_ids'] == -1).any().item()}", flush=True)
print(f"labels          : {labels.tolist()}", flush=True)

# Check if any token ID is out of vocab range
out_of_range = (enc["input_ids"] < 0) | (enc["input_ids"] >= tok.vocab_size)
print(f"out-of-range IDs: {out_of_range.any().item()}", flush=True)

# Forward pass
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_PATH, num_labels=145, ignore_mismatched_sizes=True, local_files_only=True
)
model.train()  # training mode this time

output = model(input_ids=enc["input_ids"], attention_mask=enc["attention_mask"], labels=labels)
print(f"\nLoss (train mode): {output.loss.item():.4f}", flush=True)

# Backward pass
output.loss.backward()
total_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
print(f"Grad norm after clip: {total_norm:.4f}", flush=True)

# Check if any param is NaN after backward
nan_params = [(n, p) for n, p in model.named_parameters() if p.grad is not None and torch.isnan(p.grad).any()]
print(f"Params with NaN grad: {len(nan_params)}", flush=True)
if nan_params:
    print("  First 3:", [n for n, _ in nan_params[:3]])
