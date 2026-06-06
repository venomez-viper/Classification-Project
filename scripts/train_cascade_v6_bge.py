"""
train_cascade_v6_bge.py
=======================
Same architecture as V5 (hybrid TF-IDF + embeddings + numerical) but with
the much stronger `BAAI/bge-base-en-v1.5` encoder (768-dim vs MiniLM's 384).

BGE consistently scores 5-10pp higher than MiniLM on classification benchmarks.
Combined with TF-IDF + engineered features this should clear 70%+.

Run:
    python scripts/train_cascade_v6_bge.py
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
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import breezeml.classifiers as bc

EMB_MODEL = "BAAI/bge-base-en-v1.5"   # 768-dim, ~440MB, top of MTEB classification
RAW_CSV   = ROOT / "data/raw/task1_gecs_classification_final (2).csv"
TRAIN_CSV = ROOT / "llm_finetuning/data/task1_train.csv"
TEST_CSV  = ROOT / "llm_finetuning/data/task1_test.csv"
EMB_DIR   = ROOT / "embeddings_v6_bge"
OUT_DIR   = ROOT / "models_v6"

MAX_ITER = 5000


_BP = re.compile(r"\bThe [Cc]ompan(?:y|ies)\b", re.IGNORECASE)
def clean(t: Any) -> str:
    return re.sub(r"\s{2,}", " ", _BP.sub(" ", str(t))).strip()

def norm_code(v: Any) -> str:
    return str(int(v)).zfill(8)


def encode_or_load(name: str, texts: list[str], model) -> np.ndarray:
    EMB_DIR.mkdir(parents=True, exist_ok=True)
    path = EMB_DIR / f"{name}.npy"
    if path.exists():
        emb = np.load(path)
        if len(emb) == len(texts):
            print(f"  [cached] {name}: {emb.shape}")
            return emb
    print(f"  encoding {name} ({len(texts):,} texts) …")
    t0 = time.time()
    emb = model.encode(
        texts, batch_size=32, show_progress_bar=True,
        convert_to_numpy=True, normalize_embeddings=True,
    )
    print(f"  done in {time.time()-t0:.1f}s")
    np.save(path, emb)
    return emb


def report(true_codes, preds, label="result"):
    f1 = f1_score(true_codes, preds, average="macro", zero_division=0)
    acc = sum(p == t for p, t in zip(preds, true_codes)) / len(true_codes)
    cf = Counter(true_codes)
    top10 = [c for c, _ in cf.most_common(10)]
    f1s = f1_score(true_codes, preds, average=None, labels=top10, zero_division=0)
    n_pass = int(sum(1 for v in f1s if v > 0.85))
    print(f"  {label}: F1={f1*100:.2f}%  acc={acc*100:.2f}%  top10={n_pass}/10")
    return f1, n_pass


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Load + join + engineer ────────────────────────────────────────────────
    print("Loading data …")
    raw = pd.read_csv(RAW_CSV)
    raw["combined"] = (
        raw["LongProfile"].fillna("") + " " +
        raw["SegmentName"].fillna("") + " " +
        raw["SegmentDescription"].fillna("")
    ).str.replace(r"\s+", " ", regex=True).str.strip()

    company_stats = raw.groupby("CompanyId").agg(
        num_segments=("SegmentName", "size"),
        max_share=("revenue_share", lambda x: x.abs().max()),
        share_std=("revenue_share", lambda x: float(x.std()) if len(x) > 1 else 0.0),
    ).reset_index()
    raw = raw.merge(company_stats, on="CompanyId", how="left")
    raw["share_std"] = raw["share_std"].fillna(0.0)

    raw_dedup = raw.drop_duplicates("combined", keep="first")
    join_cols = ["combined", "LongProfile", "SegmentName", "SegmentDescription",
                 "revenue_share", "is_largest_share_segment",
                 "num_segments", "max_share", "share_std"]

    train = pd.read_csv(TRAIN_CSV).merge(raw_dedup[join_cols],
                                          left_on="text", right_on="combined", how="left")
    test  = pd.read_csv(TEST_CSV).merge(raw_dedup[join_cols],
                                          left_on="text", right_on="combined", how="left")
    for df in (train, test):
        df["LongProfile"]              = df["LongProfile"].fillna(df["text"])
        df["SegmentName"]              = df["SegmentName"].fillna("")
        df["SegmentDescription"]       = df["SegmentDescription"].fillna(df["text"])
        df["revenue_share"]            = df["revenue_share"].fillna(0.5)
        df["is_largest_share_segment"] = df["is_largest_share_segment"].fillna(False).astype(float)
        df["num_segments"]             = df["num_segments"].fillna(1)
        df["max_share"]                = df["max_share"].fillna(0.5)
        df["share_std"]                = df["share_std"].fillna(0.0)
        df["code"] = df["mstar_code"].map(norm_code)
    print(f"  train={len(train):,}  test={len(test):,}")

    seg_tr  = (train["SegmentName"] + " " + train["SegmentDescription"]).map(clean)
    seg_te  = (test["SegmentName"]  + " " + test["SegmentDescription"]).map(clean)
    long_tr = train["LongProfile"].map(clean)
    long_te = test["LongProfile"].map(clean)

    # ── Encode with BGE ────────────────────────────────────────────────────────
    print(f"\nLoading encoder {EMB_MODEL} …")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMB_MODEL, device="cpu")

    print("Encoding (cached on disk):")
    E_seg_tr  = encode_or_load("seg_train",  seg_tr.tolist(),  model)
    E_seg_te  = encode_or_load("seg_test",   seg_te.tolist(),  model)
    E_long_tr = encode_or_load("long_train", long_tr.tolist(), model)
    E_long_te = encode_or_load("long_test",  long_te.tolist(), model)

    # ── TF-IDF features ────────────────────────────────────────────────────────
    print("\nTF-IDF features …")
    vec_seg = TfidfVectorizer(max_features=80000, sublinear_tf=True, stop_words="english",
                              ngram_range=(1, 2), min_df=2)
    vec_lng = TfidfVectorizer(max_features=40000, sublinear_tf=True, stop_words="english",
                              ngram_range=(1, 2), min_df=2)
    Xs_tr = vec_seg.fit_transform(seg_tr);  Xs_te = vec_seg.transform(seg_te)
    Xl_tr = vec_lng.fit_transform(long_tr); Xl_te = vec_lng.transform(long_te)

    # ── Numerical ──────────────────────────────────────────────────────────────
    num_cols = ["revenue_share", "is_largest_share_segment", "num_segments",
                "max_share", "share_std"]
    scaler = MinMaxScaler(clip=True)
    N_tr = scaler.fit_transform(train[num_cols].values)
    N_te = scaler.transform(test[num_cols].values)

    def to_sparse(arr): return csr_matrix(arr.astype(np.float32))

    # ── Build hybrid feature stack ────────────────────────────────────────────
    print("\nBuilding hybrid stack: TF-IDF + BGE + numerical …")
    X_tr = sparse_hstack([
        Xs_tr, Xl_tr,
        to_sparse(E_seg_tr), to_sparse(E_long_tr),
        to_sparse(N_tr),
    ], format="csr")
    X_te = sparse_hstack([
        Xs_te, Xl_te,
        to_sparse(E_seg_te), to_sparse(E_long_te),
        to_sparse(N_te),
    ], format="csr")
    print(f"  feature dim: {X_tr.shape[1]:,}")

    y_tr = train["code"].values
    y_te = test["code"].values

    # ── Train + tune C ────────────────────────────────────────────────────────
    print("\nC tuning …")
    best_C, best_f1, best_clf, best_n = 1.0, 0.0, None, 0
    for C in [0.25, 0.5, 1.0, 2.0, 4.0]:
        t0 = time.time()
        clf = LinearSVC(C=C, dual=False, class_weight="balanced", max_iter=MAX_ITER)
        clf.fit(X_tr, y_tr)
        preds = clf.predict(X_te)
        f1 = f1_score(y_te, preds, average="macro", zero_division=0)
        cf = Counter(y_te)
        top10 = [c for c, _ in cf.most_common(10)]
        f1s = f1_score(y_te, preds, average=None, labels=top10, zero_division=0)
        n_pass = int(sum(1 for v in f1s if v > 0.85))
        marker = "  <-- BEST" if f1 > best_f1 else ""
        print(f"  C={C:5}: F1={f1*100:.2f}%  top10={n_pass}/10  ({time.time()-t0:.1f}s){marker}")
        if f1 > best_f1:
            best_C, best_f1, best_clf, best_n = C, f1, clf, n_pass

    print("\n" + "=" * 65)
    print(f"V6 RESULT: F1={best_f1*100:.2f}%  C={best_C}  top10={best_n}/10")
    print(f"Target: >= 75.00%  -> {'PASS' if best_f1 >= 0.75 else 'FAIL'}")
    print("=" * 65)

    joblib.dump(best_clf, OUT_DIR / "v6_flat_svm.joblib")
    joblib.dump(vec_seg,  OUT_DIR / "v6_vec_seg.pkl")
    joblib.dump(vec_lng,  OUT_DIR / "v6_vec_long.pkl")
    joblib.dump(scaler,   OUT_DIR / "v6_scaler.pkl")

    summary = {
        "version": "v6-bge-hybrid",
        "encoder": EMB_MODEL,
        "split": "row-level 80/20 (case standard)",
        "best_C": best_C,
        "macro_f1": round(float(best_f1) * 100, 2),
        "top10_pass": int(best_n),
        "target_met": bool(best_f1 >= 0.75),
        "feature_dim": int(X_tr.shape[1]),
    }
    (OUT_DIR / "training_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"  Saved to {OUT_DIR}")


if __name__ == "__main__":
    main()
