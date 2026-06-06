"""
Minimal Trainer test — 100 rows, no gradient accumulation, log every step.
Tells us whether the Trainer itself is producing bad loss values.
"""
import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"]  = "1"

# pandas before torch
import pandas as pd
import numpy as np
from sklearn.metrics import f1_score

DATA_CSV   = r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\data\task1_train.csv"
MODEL_PATH = r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\models\deberta-v3-small"

print("Loading data...", flush=True)
df = pd.read_csv(DATA_CSV, nrows=200, dtype={"text": str, "label_idx": int})
print(f"Loaded {len(df)} rows, labels: {df['label_idx'].min()} - {df['label_idx'].max()}", flush=True)

import torch
from datasets import Dataset
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    TrainingArguments, Trainer
)

tok = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True, fix_mistral_regex=True)

train_df = df.iloc[:160].rename(columns={"label_idx": "labels"}).reset_index(drop=True)
test_df  = df.iloc[160:].rename(columns={"label_idx": "labels"}).reset_index(drop=True)

def tokenize(batch):
    return tok(batch["text"], truncation=True, padding="max_length", max_length=128)

train_ds = Dataset.from_pandas(train_df[["text", "labels"]])
test_ds  = Dataset.from_pandas(test_df[["text", "labels"]])
train_ds = train_ds.map(tokenize, batched=True)
test_ds  = test_ds.map(tokenize, batched=True)

available_cols = [c for c in ["input_ids", "attention_mask", "labels"] if c in train_ds.column_names]
print("Dataset columns used:", available_cols, flush=True)
print("First labels in dataset:", train_ds["labels"][:5], flush=True)

train_ds.set_format("torch", columns=available_cols)
test_ds.set_format("torch", columns=available_cols)

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_PATH, num_labels=145, ignore_mismatched_sizes=True, local_files_only=True
)

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=1)
    return {"macro_f1": f1_score(labels, preds, average="macro", zero_division=0)}

args = TrainingArguments(
    output_dir="llm_finetuning/results/debug_run",
    num_train_epochs=1,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    gradient_accumulation_steps=1,   # no accumulation
    learning_rate=2e-5,
    bf16=False,
    fp16=False,
    logging_steps=1,                 # log every single step
    eval_strategy="no",
    save_strategy="no",
    report_to="none",
    seed=42,
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=train_ds,
    eval_dataset=test_ds,
    compute_metrics=compute_metrics,
)

print("\nStarting minimal training run...", flush=True)
trainer.train()
print("Done.", flush=True)
