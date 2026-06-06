"""
train_cascade_v4_embeddings.py
==============================
Sentence-embedding cascade for GECS Task 1.

What changes vs V3:
  • Uses all-MiniLM-L6-v2 sentence embeddings (semantic, not bag-of-words)
  • Encodes segment text + long profile separately, then concatenates
  • Uses the CASE-STANDARD row-level 80/20 split (what task1_train/test.csv represents)
  • Compares flat 145-class SVM vs 3-level cascade — picks the winner
  • Caches embeddings to embeddings_v4/ so we never re-encode

Run:
    python scripts/train_cascade_v4_embeddings.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack as sparse_hstack
from sklearn.metrics import f1_score
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import breezeml.classifiers as bc

EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"   # 384-dim, CPU-fast
RAW_CSV   = ROOT / "data/raw/task1_gecs_classification_final (2).csv"
TRAIN_CSV = ROOT / "llm_finetuning/data/task1_train.csv"
TEST_CSV  = ROOT / "llm_finetuning/data/task1_test.csv"
EMB_DIR   = ROOT / "embeddings_v4"
OUT_DIR   = ROOT / "models_v4"

MAX_ITER  = 5000


# ── Cleaning ──────────────────────────────────────────────────────────────────

_BP = re.compile(r"\bThe [Cc]ompan(?:y|ies)\b", re.IGNORECASE)

def clean(t: Any) -> str:
    return re.sub(r"\s{2,}", " ", _BP.sub(" ", str(t))).strip()


def norm_code(v: Any) -> str:
    return str(int(v)).zfill(8)


# ── Encoder helper ────────────────────────────────────────────────────────────

def encode_or_load(name: str, texts: list[str], model) -> np.ndarray:
    EMB_DIR.mkdir(parents=True, exist_ok=True)
    path = EMB_DIR / f"{name}.npy"
    if path.exists():
        emb = np.load(path)
        if len(emb) == len(texts):
            print(f"  [cached] {name}: {emb.shape}")
            return emb
        print(f"  [stale] {name}: cached {len(emb)} != {len(texts)}, re-encoding")
    print(f"  encoding {name} ({len(texts):,} texts) …")
    t0 = time.time()
    emb = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    dt = time.time() - t0
    print(f"  done in {dt:.1f}s ({len(texts)/dt:.1f} texts/s)")
    np.save(path, emb)
    return emb


# ── Cascade artifact helpers (same shape as V3) ───────────────────────────────

def fit_artifact(X_tr, y_tr) -> dict[str, Any]:
    unique = sorted(set(str(v) for v in y_tr))
    if len(unique) == 1:
        return {"type": "constant", "value": unique[0]}
    model = LinearSVC(class_weight="balanced", dual=False, max_iter=MAX_ITER)
    model.fit(X_tr, y_tr)
    return {"type": "svm", "model": model}


def _softmax(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=np.float64)
    a -= a.max()
    e = np.exp(a)
    return e / e.sum()


def predict_artifact(art: dict, Xi) -> tuple[str, float]:
    if art["type"] == "constant":
        return str(art["value"]), 100.0
    m = art["model"]
    s = m.decision_function(Xi)
    classes = np.asarray(m.classes_, dtype=str)
    margins = np.asarray(s[0], dtype=np.float64) if np.ndim(s) > 1 \
              else np.array([-s[0], s[0]], dtype=np.float64)
    p = _softmax(margins)
    best = int(np.argmax(p))
    return str(classes[best]), round(float(p[best]) * 100, 1)


# ── Eval helpers ──────────────────────────────────────────────────────────────

def report(true_codes, preds, true_sectors=None, sector_preds=None,
           true_groups=None, group_preds=None, label="result"):
    f1 = f1_score(true_codes, preds, average="macro", zero_division=0)
    acc = sum(p == t for p, t in zip(preds, true_codes)) / len(true_codes)
    print(f"\n  {label}")
    print(f"    Macro F1   : {f1*100:.2f}%")
    print(f"    Accuracy   : {acc*100:.2f}%")
    if sector_preds is not None:
        sa = sum(p == t for p, t in zip(sector_preds, true_sectors)) / len(true_sectors)
        print(f"    L1 sector  : {sa*100:.2f}%")
    if group_preds is not None:
        ga = sum(p == t for p, t in zip(group_preds, true_groups)) / len(true_groups)
        print(f"    L2 group   : {ga*100:.2f}%")
    cf = Counter(true_codes)
    top10 = [c for c, _ in cf.most_common(10)]
    f1s = f1_score(true_codes, preds, average=None, labels=top10, zero_division=0)
    n_pass = int(sum(1 for v in f1s if v > 0.85))
    print(f"    Top-10 pass: {n_pass}/10 (target > 85% each)")
    for c, v in zip(top10, f1s):
        flag = "PASS" if v > 0.85 else "FAIL"
        print(f"      [{flag}] {c}: {v*100:.1f}%  n={cf[c]}")
    return f1, n_pass


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load splits + raw join for full features
    print("Loading data …")
    raw   = pd.read_csv(RAW_CSV)
    raw["combined"] = (
        raw["LongProfile"].fillna("") + " " +
        raw["SegmentName"].fillna("") + " " +
        raw["SegmentDescription"].fillna("")
    ).str.replace(r"\s+", " ", regex=True).str.strip()

    train = pd.read_csv(TRAIN_CSV)
    test  = pd.read_csv(TEST_CSV)

    # Join back to raw to get original columns. Many-to-one is OK because
    # if multiple raw rows have identical combined text, they have identical
    # LongProfile/SegmentName/SegDesc too.
    raw_dedup = raw.drop_duplicates("combined", keep="first")
    train = train.merge(
        raw_dedup[["combined", "LongProfile", "SegmentName", "SegmentDescription",
                   "revenue_share", "is_largest_share_segment"]],
        left_on="text", right_on="combined", how="left",
    )
    test = test.merge(
        raw_dedup[["combined", "LongProfile", "SegmentName", "SegmentDescription",
                   "revenue_share", "is_largest_share_segment"]],
        left_on="text", right_on="combined", how="left",
    )
    # Fallback for unmatched rows: use combined text as both
    train["LongProfile"] = train["LongProfile"].fillna(train["text"])
    train["SegmentName"] = train["SegmentName"].fillna("")
    train["SegmentDescription"] = train["SegmentDescription"].fillna(train["text"])
    train["revenue_share"] = train["revenue_share"].fillna(0.5)
    train["is_largest_share_segment"] = train["is_largest_share_segment"].fillna(False).astype(float)

    test["LongProfile"] = test["LongProfile"].fillna(test["text"])
    test["SegmentName"] = test["SegmentName"].fillna("")
    test["SegmentDescription"] = test["SegmentDescription"].fillna(test["text"])
    test["revenue_share"] = test["revenue_share"].fillna(0.5)
    test["is_largest_share_segment"] = test["is_largest_share_segment"].fillna(False).astype(float)

    train["code"] = train["mstar_code"].map(norm_code)
    train["sector"] = train["code"].str[:3]
    train["group"]  = train["code"].str[:5]
    test["code"]  = test["mstar_code"].map(norm_code)
    test["sector"]  = test["code"].str[:3]
    test["group"]  = test["code"].str[:5]

    print(f"  train: {len(train):,}  test: {len(test):,}  classes: {train['code'].nunique()}")

    # 2. Build text fields for encoding
    seg_train = (train["SegmentName"].astype(str) + ". " +
                 train["SegmentDescription"].astype(str)).map(clean)
    seg_test  = (test["SegmentName"].astype(str) + ". " +
                 test["SegmentDescription"].astype(str)).map(clean)
    long_train = train["LongProfile"].astype(str).map(clean)
    long_test  = test["LongProfile"].astype(str).map(clean)

    # 3. Encode
    print(f"\nLoading encoder {EMB_MODEL} …")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMB_MODEL, device="cpu")

    print("\nEncoding (cached on disk):")
    E_seg_tr  = encode_or_load("seg_train",  seg_train.tolist(),  model)
    E_seg_te  = encode_or_load("seg_test",   seg_test.tolist(),   model)
    E_long_tr = encode_or_load("long_train", long_train.tolist(), model)
    E_long_te = encode_or_load("long_test",  long_test.tolist(),  model)

    # 4. Numerical features (scaled)
    scaler = MinMaxScaler(feature_range=(0, 1), clip=True)
    num_cols = ["revenue_share", "is_largest_share_segment"]
    N_tr = scaler.fit_transform(train[num_cols].values)
    N_te = scaler.transform(test[num_cols].values)

    # 5. Build dense feature matrix:  [segment_emb | long_emb | numerical]
    X_tr = np.hstack([E_seg_tr, E_long_tr, N_tr]).astype(np.float32)
    X_te = np.hstack([E_seg_te, E_long_te, N_te]).astype(np.float32)
    print(f"\n  feature dim: {X_tr.shape[1]}  (seg=384 + long=384 + num=2)")

    # 6. Flat 145-class SVM (the ceiling, no cascade error propagation)
    print("\nTraining FLAT LinearSVC (145 classes) via BreezeML …")
    flat_pipe, flat_report = bc.linear_svm(
        X=X_tr, y=train["code"].values,
        X_test=X_te, y_test=test["code"].values,
        max_iter=MAX_ITER,
    )
    flat_clf = flat_pipe.named_steps["model"]
    flat_preds = flat_clf.predict(X_te)
    flat_f1, flat_pass = report(
        test["code"].tolist(), list(flat_preds),
        label="FLAT (no cascade)"
    )

    # 7. Cascade: L1 sector → L2 group → L3 code
    print("\nTraining CASCADE …")

    print("  L1 sector …")
    L1 = fit_artifact(X_tr, train["sector"].values)

    print("  L2 group per sector …")
    L2: dict[str, Any] = {}
    for sector, grp in train.groupby("sector"):
        idx = grp.index.values
        L2[str(sector)] = fit_artifact(X_tr[idx], grp["group"].values)

    print("  L3 code per group …")
    L3: dict[str, Any] = {}
    for group, grp in train.groupby("group"):
        idx = grp.index.values
        L3[str(group)] = fit_artifact(X_tr[idx], grp["code"].values)

    # Cascade evaluation
    print("\nEvaluating CASCADE …")
    cascade_preds, sector_preds, group_preds = [], [], []
    for i in range(X_te.shape[0]):
        Xi = X_te[i:i+1]
        sec, _ = predict_artifact(L1, Xi)
        l2 = L2.get(sec) or L2[max(L2.keys())]
        grp, _ = predict_artifact(l2, Xi)
        l3 = L3.get(grp)
        if l3 is None:
            grp = train[train["sector"] == sec]["group"].mode().iloc[0]
            l3 = L3[grp]
        code, _ = predict_artifact(l3, Xi)
        sector_preds.append(sec)
        group_preds.append(grp)
        cascade_preds.append(code)

    cas_f1, cas_pass = report(
        test["code"].tolist(), cascade_preds,
        true_sectors=test["sector"].tolist(), sector_preds=sector_preds,
        true_groups=test["group"].tolist(),   group_preds=group_preds,
        label="CASCADE"
    )

    # 8. Save best
    print("\n" + "=" * 60)
    print("FINAL RESULTS — Sentence Embeddings + LinearSVC")
    print("=" * 60)
    print(f"  Flat   : Macro F1 = {flat_f1*100:.2f}%   top-10 pass = {flat_pass}/10")
    print(f"  Cascade: Macro F1 = {cas_f1*100:.2f}%   top-10 pass = {cas_pass}/10")
    winner = "flat" if flat_f1 >= cas_f1 else "cascade"
    print(f"  Winner : {winner.upper()}")
    print(f"  Target : >= 75.00%   {'PASS' if max(flat_f1, cas_f1) >= 0.75 else 'FAIL'}")

    # Save artifacts
    joblib.dump(flat_clf, OUT_DIR / "flat_svm.joblib")
    joblib.dump(L1,       OUT_DIR / "cascade_L1.joblib")
    joblib.dump(L2,       OUT_DIR / "cascade_L2.joblib")
    joblib.dump(L3,       OUT_DIR / "cascade_L3.joblib")
    joblib.dump(scaler,   OUT_DIR / "num_scaler.pkl")

    summary = {
        "version": "v4-embeddings",
        "encoder": EMB_MODEL,
        "split":   "row-level 80/20 (case standard)",
        "train_rows": int(len(train)),
        "test_rows":  int(len(test)),
        "feature_dim": int(X_tr.shape[1]),
        "flat_macro_f1":   round(float(flat_f1)*100, 2),
        "cascade_macro_f1":round(float(cas_f1)*100, 2),
        "flat_top10_pass":   int(flat_pass),
        "cascade_top10_pass":int(cas_pass),
        "winner": winner,
        "target_75_passed": bool(max(flat_f1, cas_f1) >= 0.75),
    }
    (OUT_DIR / "training_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"\n  Saved to {OUT_DIR}")


if __name__ == "__main__":
    main()
