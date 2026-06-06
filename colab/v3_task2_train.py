"""COLAB CELL — Task 2 ModernBERT-large multi-task trainer.

4 heads: sector (3-digit) → group (5-digit) → industry (8-digit) → sub_industry (11-digit).
Same architecture pattern as T1, separate label spaces.

Set CONFIG block. Launch parallel notebooks with different seeds for ensemble.

Outputs to /content/drive/MyDrive/{RUN_NAME}/:
  best_model_state.pt
  test_predictions_topk.csv
  subindustry_classes.npy
  final_summary.json
"""
# ============================================================================
# CONFIG
# ============================================================================
CONFIG = {
    "RUN_NAME": "v3_t2_segaware_seed42",
    "USE_SEGMENT_AWARE": True,    # True: use llm_finetuning/data/segment_aware_task2/
    "USE_SAMPLE_WEIGHT": True,
    "SEED": 42,
    "EPOCHS": 12,                 # T2 has fewer rows + more classes, more epochs help
    "SAVE_TOPK_AND_EMBEDS": True,
}

SUGGESTED = """
# T2 Notebook 1 — segment-aware seed=42
CONFIG = {"RUN_NAME":"v3_t2_seed42",  "USE_SEGMENT_AWARE":True, "USE_SAMPLE_WEIGHT":True, "SEED":42,  "EPOCHS":12, "SAVE_TOPK_AND_EMBEDS":True}
# T2 Notebook 2 — segment-aware seed=123
CONFIG = {"RUN_NAME":"v3_t2_seed123", "USE_SEGMENT_AWARE":True, "USE_SAMPLE_WEIGHT":True, "SEED":123, "EPOCHS":12, "SAVE_TOPK_AND_EMBEDS":True}
# T2 Notebook 3 — segment-aware seed=7
CONFIG = {"RUN_NAME":"v3_t2_seed7",   "USE_SEGMENT_AWARE":True, "USE_SAMPLE_WEIGHT":True, "SEED":7,   "EPOCHS":12, "SAVE_TOPK_AND_EMBEDS":True}
"""

# ============================================================================
import os, json, random
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
from sklearn.model_selection import train_test_split
from datasets import Dataset
from tqdm.auto import tqdm
from collections import Counter

from google.colab import drive
drive.mount('/content/drive', force_remount=False)

SEED = CONFIG["SEED"]
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)

MODEL_NAME = "answerdotai/ModernBERT-large"
MAX_LEN = 384  # T2 segment text shorter than T1 joint
BATCH_SIZE = 12
GRAD_ACCUM = 6
ENCODER_LR = 5e-6
HEAD_LR = 5e-4
WARMUP_RATIO = 0.05
LABEL_SMOOTHING = 0.02

DRIVE_OUT = Path("/content/drive/MyDrive") / CONFIG["RUN_NAME"]
DRIVE_OUT.mkdir(parents=True, exist_ok=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
USE_BF16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
ad = torch.bfloat16 if USE_BF16 else torch.float16
print(f"Device: {device} bf16: {USE_BF16}  Run: {CONFIG['RUN_NAME']}  Seed: {SEED}")

# ============================================================================
# Data
# ============================================================================
def norm_subcode(v):
    if pd.isna(v): return ""
    s = str(v).strip()
    if s.endswith(".0"): s = s[:-2]
    digits = "".join(ch for ch in s if ch.isdigit())
    return digits.zfill(10) if digits else ""

if CONFIG["USE_SEGMENT_AWARE"]:
    train_path = "/content/segment_aware_t2_train.csv"
    test_path = "/content/segment_aware_t2_test.csv"
    assert Path(train_path).exists(), "Upload segment_aware_task2 files (rename to segment_aware_t2_*.csv)"
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    train_df["text"] = train_df["text"].fillna("").astype(str)
    test_df["text"] = test_df["text"].fillna("").astype(str)
    train_df["sub_code"] = train_df["sub_code"].map(norm_subcode)
    test_df["sub_code"] = test_df["sub_code"].map(norm_subcode)
    if not CONFIG["USE_SAMPLE_WEIGHT"]:
        train_df["sample_weight"] = 1.0
else:
    train_df = pd.read_csv("/content/task2_train.csv")
    test_df = pd.read_csv("/content/task2_test.csv")
    train_df["sub_code"] = train_df["sub_code"].map(norm_subcode)
    test_df["sub_code"] = test_df["sub_code"].map(norm_subcode)
    train_df["sample_weight"] = 1.0
    test_df["sample_weight"] = 1.0

for f in (train_df, test_df):
    f["industry_code"] = f["sub_code"].str[:8]
    f["sector_code"] = f["sub_code"].str[:3]
    f["group_code"] = f["sub_code"].str[:5]
    f["text"] = f["text"].str.replace("\n", " ").str.strip()

train_df = train_df[train_df["text"].str.len() > 0].reset_index(drop=True)
test_df = test_df[test_df["text"].str.len() > 0].reset_index(drop=True)

# Label encoders span train ∪ test
le_sec = LabelEncoder().fit(pd.concat([train_df["sector_code"], test_df["sector_code"]]))
le_grp = LabelEncoder().fit(pd.concat([train_df["group_code"], test_df["group_code"]]))
le_ind = LabelEncoder().fit(pd.concat([train_df["industry_code"], test_df["industry_code"]]))
le_sub = LabelEncoder().fit(pd.concat([train_df["sub_code"], test_df["sub_code"]]))

for f in (train_df, test_df):
    f["sec_idx"] = le_sec.transform(f["sector_code"])
    f["grp_idx"] = le_grp.transform(f["group_code"])
    f["ind_idx"] = le_ind.transform(f["industry_code"])
    f["sub_idx"] = le_sub.transform(f["sub_code"])

N_SEC, N_GRP, N_IND, N_SUB = len(le_sec.classes_), len(le_grp.classes_), len(le_ind.classes_), len(le_sub.classes_)
print(f"label spaces: sec={N_SEC} grp={N_GRP} ind={N_IND} sub={N_SUB}")
print(f"train: {len(train_df)}  test: {len(test_df)}")

# Stratified dev
try:
    train_fit, dev = train_test_split(train_df, test_size=0.10, random_state=SEED, stratify=train_df["sub_code"])
except ValueError:
    train_fit, dev = train_test_split(train_df, test_size=0.10, random_state=SEED, shuffle=True)
train_fit = train_fit.reset_index(drop=True); dev = dev.reset_index(drop=True)

# Hierarchy maps
sub_to_ind_idx = torch.tensor([int(le_ind.transform([c[:8]])[0]) for c in le_sub.classes_], dtype=torch.long, device=device)
sub_to_grp_idx = torch.tensor([int(le_grp.transform([c[:5]])[0]) for c in le_sub.classes_], dtype=torch.long, device=device)
sub_to_sec_idx = torch.tensor([int(le_sec.transform([c[:3]])[0]) for c in le_sub.classes_], dtype=torch.long, device=device)

# ============================================================================
# Tokenizer + datasets
# ============================================================================
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)

def to_ds(df):
    return Dataset.from_pandas(df[["text","sec_idx","grp_idx","ind_idx","sub_idx","sample_weight"]].reset_index(drop=True), preserve_index=False)

def tok(b):
    return tokenizer(b["text"], truncation=True, padding="max_length", max_length=MAX_LEN)

train_ds = to_ds(train_fit).map(tok, batched=True, remove_columns=["text"])
dev_ds = to_ds(dev).map(tok, batched=True, remove_columns=["text"])
test_ds = to_ds(test_df).map(tok, batched=True, remove_columns=["text"])

cols = ["input_ids","attention_mask","sec_idx","grp_idx","ind_idx","sub_idx","sample_weight"]
for d in (train_ds, dev_ds, test_ds): d.set_format(type="torch", columns=cols)

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=2, pin_memory=True)
dev_loader = DataLoader(dev_ds, batch_size=BATCH_SIZE*2, shuffle=False, num_workers=2, pin_memory=True)
test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE*2, shuffle=False, num_workers=2, pin_memory=True)

# ============================================================================
# Model — 4 heads
# ============================================================================
class T2MultiTask(nn.Module):
    def __init__(self, name, n_sec, n_grp, n_ind, n_sub, dropout=0.10):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(name, trust_remote_code=True)
        h = self.encoder.config.hidden_size
        self.norm = nn.LayerNorm(h); self.dropout = nn.Dropout(dropout)
        self.sec_head = nn.Linear(h, n_sec)
        self.grp_head = nn.Linear(h, n_grp)
        self.ind_head = nn.Linear(h, n_ind)
        self.sub_head = nn.Linear(h, n_sub)
    def forward(self, ids, mask, return_pooled=False):
        o = self.encoder(input_ids=ids, attention_mask=mask)
        pr = o.pooler_output if getattr(o,"pooler_output",None) is not None else o.last_hidden_state[:,0]
        p = self.dropout(self.norm(pr))
        out = {"sec_logits":self.sec_head(p),"grp_logits":self.grp_head(p),
               "ind_logits":self.ind_head(p),"sub_logits":self.sub_head(p)}
        if return_pooled: out["pooled"] = self.norm(pr)
        return out

model = T2MultiTask(MODEL_NAME, N_SEC, N_GRP, N_IND, N_SUB).to(device)

def eff_w(labels, n, beta=0.9997, power=0.45):
    cnt = np.bincount(labels, minlength=n).astype(np.float64)
    en = 1.0 - np.power(beta, cnt); w = (1.0-beta)/np.clip(en,1e-12,None)
    w = np.power(w, power)
    return torch.tensor(w/w.mean(), dtype=torch.float32)

w_sec = eff_w(train_fit["sec_idx"].values, N_SEC, 0.999, 0.25).to(device)
w_grp = eff_w(train_fit["grp_idx"].values, N_GRP, 0.9995, 0.35).to(device)
w_ind = eff_w(train_fit["ind_idx"].values, N_IND, 0.9997, 0.45).to(device)
w_sub = eff_w(train_fit["sub_idx"].values, N_SUB, 0.9997, 0.55).to(device)

ce_sec = nn.CrossEntropyLoss(weight=w_sec, reduction="none", label_smoothing=LABEL_SMOOTHING)
ce_grp = nn.CrossEntropyLoss(weight=w_grp, reduction="none", label_smoothing=LABEL_SMOOTHING)
ce_ind = nn.CrossEntropyLoss(weight=w_ind, reduction="none", label_smoothing=LABEL_SMOOTHING)
ce_sub = nn.CrossEntropyLoss(weight=w_sub, reduction="none", label_smoothing=LABEL_SMOOTHING)
A,B,C,D = 0.10, 0.15, 0.25, 0.50  # task weights

enc_p, head_p = [], []
for n,p in model.named_parameters():
    (head_p if any(h in n for h in ["_head","norm"]) else enc_p).append(p)
opt = torch.optim.AdamW([{"params":enc_p,"lr":ENCODER_LR},{"params":head_p,"lr":HEAD_LR}], weight_decay=0.01)
sched = get_cosine_schedule_with_warmup(opt, int(len(train_loader)//GRAD_ACCUM*CONFIG["EPOCHS"]*WARMUP_RATIO),
                                         len(train_loader)//GRAD_ACCUM*CONFIG["EPOCHS"])

# ============================================================================
# Training
# ============================================================================
def eval_(loader):
    model.eval(); t,p = [],[]
    with torch.no_grad():
        for b in loader:
            ids = b["input_ids"].to(device,non_blocking=True); m = b["attention_mask"].to(device,non_blocking=True)
            with torch.autocast(device_type="cuda",dtype=ad,enabled=USE_BF16): o = model(ids,m)
            t.extend(b["sub_idx"].numpy().tolist()); p.extend(o["sub_logits"].argmax(-1).cpu().numpy().tolist())
    tc = le_sub.inverse_transform(t); pc = le_sub.inverse_transform(p)
    return f1_score(tc,pc,average="macro",zero_division=0), accuracy_score(tc,pc)

best_f1 = -1.0; patience=3; history=[]
print(f"\nTraining {CONFIG['EPOCHS']} epochs...")
opt.zero_grad()
for ep in range(1, CONFIG["EPOCHS"]+1):
    model.train(); losses=[]
    for step, b in enumerate(tqdm(train_loader, desc=f"ep{ep}", leave=False)):
        ids = b["input_ids"].to(device,non_blocking=True); m=b["attention_mask"].to(device,non_blocking=True)
        sec=b["sec_idx"].to(device,non_blocking=True); grp=b["grp_idx"].to(device,non_blocking=True)
        ind=b["ind_idx"].to(device,non_blocking=True); sub=b["sub_idx"].to(device,non_blocking=True)
        sw=b["sample_weight"].to(device,non_blocking=True).float()
        with torch.autocast(device_type="cuda",dtype=ad,enabled=USE_BF16):
            o = model(ids,m)
            ls=(ce_sec(o["sec_logits"],sec)*sw).mean()
            lg=(ce_grp(o["grp_logits"],grp)*sw).mean()
            li=(ce_ind(o["ind_logits"],ind)*sw).mean()
            lu=(ce_sub(o["sub_logits"],sub)*sw).mean()
            loss=(A*ls+B*lg+C*li+D*lu)/GRAD_ACCUM
        loss.backward()
        if (step+1)%GRAD_ACCUM==0:
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
            opt.step(); sched.step(); opt.zero_grad()
        losses.append(loss.item()*GRAD_ACCUM)
    df1, dac = eval_(dev_loader)
    print(f"ep{ep}: loss={np.mean(losses):.4f}  dev_f1={df1:.4%}  dev_acc={dac:.4%}")
    history.append({"epoch":ep,"train_loss":float(np.mean(losses)),"dev_f1":float(df1),"dev_acc":float(dac)})
    if df1 > best_f1+0.001:
        best_f1=df1; torch.save(model.state_dict(), DRIVE_OUT/"best_model_state.pt"); patience=3
        print(f"  saved best @ {ep}")
    else:
        patience -= 1
        if patience<=0: print(f"  early stop @ {ep}"); break

model.load_state_dict(torch.load(DRIVE_OUT/"best_model_state.pt", map_location=device)); model.eval()

# ============================================================================
# Test inference + top-5
# ============================================================================
def hierarchy_scores(o, lg=0.0, li=0.0, ls=0.0):
    sp = F.log_softmax(o["sub_logits"],dim=-1)
    ip = F.log_softmax(o["ind_logits"],dim=-1)
    gp = F.log_softmax(o["grp_logits"],dim=-1)
    se = F.log_softmax(o["sec_logits"],dim=-1)
    return sp + li*ip[:,sub_to_ind_idx] + lg*gp[:,sub_to_grp_idx] + ls*se[:,sub_to_sec_idx]

@torch.no_grad()
def run_inf(loader, save_emb=False):
    t5i, t5p, tr, em = [], [], [], ([] if save_emb else None)
    for b in tqdm(loader, leave=False):
        ids=b["input_ids"].to(device,non_blocking=True); m=b["attention_mask"].to(device,non_blocking=True)
        with torch.autocast(device_type="cuda",dtype=ad,enabled=USE_BF16):
            o = model(ids,m,return_pooled=save_emb); s = hierarchy_scores(o, lg=0.10, li=0.15, ls=0.05)
        pr = s.softmax(dim=-1).float()
        tp, ti = pr.topk(5, dim=-1)
        t5i.append(ti.cpu().numpy()); t5p.append(tp.cpu().numpy())
        tr.append(b["sub_idx"].numpy())
        if save_emb: em.append(o["pooled"].float().cpu().numpy().astype(np.float16))
    return np.concatenate(tr), np.concatenate(t5i), np.concatenate(t5p), (np.concatenate(em) if save_emb else None)

print("\n=== Test ===")
true, top5, top5p, emb = run_inf(test_loader, save_emb=CONFIG["SAVE_TOPK_AND_EMBEDS"])
true_codes = le_sub.inverse_transform(true)
pred_codes = le_sub.inverse_transform(top5[:,0])
test_f1 = f1_score(true_codes, pred_codes, average="macro", zero_division=0)
test_acc = accuracy_score(true_codes, pred_codes)
print(f"TEST sub-industry: F1 = {test_f1:.4%}  acc = {test_acc:.4%}")

top5_codes = np.array([le_sub.inverse_transform(r) for r in top5])
out = pd.DataFrame({
    "true_code": true_codes, "pred_code": pred_codes,
    **{f"top{i+1}_code": top5_codes[:,i] for i in range(5)},
    **{f"top{i+1}_prob": top5p[:,i] for i in range(5)},
})
out.to_csv(DRIVE_OUT/"test_predictions_topk.csv", index=False)
np.save(DRIVE_OUT/"subindustry_classes.npy", le_sub.classes_)
if CONFIG["SAVE_TOPK_AND_EMBEDS"]:
    np.save(DRIVE_OUT/"test_cls.npy", emb)

counts = Counter(true_codes)
top10 = [c for c,_ in counts.most_common(10)]
top10_f1 = f1_score(true_codes, pred_codes, average=None, labels=top10, zero_division=0)
top10_pass = int(sum(s>0.85 for s in top10_f1))
summary = {"config":CONFIG, "best_dev_f1":float(best_f1), "test_macro_f1":float(test_f1),
           "test_acc":float(test_acc), "top10_pass":top10_pass,
           "top10_breakdown":[{"code":c,"f1":float(s),"support":int(counts[c])} for c,s in zip(top10,top10_f1)],
           "history":history}
with open(DRIVE_OUT/"final_summary.json","w") as fh: json.dump(summary, fh, indent=2)
print(json.dumps(summary,indent=2)[:2500])
print(f"\nDONE. {DRIVE_OUT}")
