"""
train_cascade_v11_gte_large.py
==============================
Top-of-MTEB encoder: Alibaba-NLP/gte-large-en-v1.5 (1024-dim).
This model is state-of-the-art for its size class on classification.

Architecture: BERT + RoPE + GLU. ~670 MB. Runs on CPU.
Expected gain: +3-5pp over MiniLM/BGE-base.

Strategy:
  1. Encode seg + long with gte-large (cached to disk)
  2. Stack: TF-IDF + gte-large + MiniLM + BGE + fine-tuned + numerical
  3. Train calibrated LogReg (best classifier from V10 likely)
  4. Compare to V8 baseline (68.42%)

Run:
    python scripts/train_cascade_v11_gte_large.py
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
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV   = ROOT / "data/raw/task1_gecs_classification_final (2).csv"
TRAIN_CSV = ROOT / "llm_finetuning/data/task1_train.csv"
TEST_CSV  = ROOT / "llm_finetuning/data/task1_test.csv"
EMB_DIR   = ROOT / "embeddings_v11_gte"
OUT_DIR   = ROOT / "models_v11"

# Top-of-MTEB encoder for its size class. Uses BERT + RoPE + GLU backbone.
EMB_MODEL = "Alibaba-NLP/gte-large-en-v1.5"
MAX_SEQ_LEN = 512    # the model supports 8192 but 512 is enough and 16x faster

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
            print(f"  [cached] {name}: {emb.shape}", flush=True)
            return emb
    print(f"  encoding {name} ({len(texts):,} texts) …", flush=True)
    t0 = time.time()
    emb = model.encode(
        texts, batch_size=16, show_progress_bar=True,
        convert_to_numpy=True, normalize_embeddings=True,
    )
    print(f"  done in {(time.time()-t0)/60:.1f} min", flush=True)
    np.save(path, emb)
    return emb


def report(true_codes, preds, label):
    f1 = f1_score(true_codes, preds, average="macro", zero_division=0)
    cf = Counter(true_codes)
    top10 = [c for c, _ in cf.most_common(10)]
    f1s = f1_score(true_codes, preds, average=None, labels=top10, zero_division=0)
    n_pass = int(sum(1 for v in f1s if v > 0.85))
    print(f"  {label:50s} F1={f1*100:6.2f}%  top10={n_pass}/10", flush=True)
    return f1, n_pass


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Load data ─────────────────────────────────────────────────────────────
    print("Loading data …", flush=True)
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
    print(f"  train={len(train):,}  test={len(test):,}", flush=True)

    seg_tr = (train["SegmentName"] + ". " + train["SegmentDescription"]).map(clean)
    seg_te = (test["SegmentName"]  + ". " + test["SegmentDescription"]).map(clean)
    long_tr = train["LongProfile"].map(clean)
    long_te = test["LongProfile"].map(clean)

    # ── Encode with gte-large ─────────────────────────────────────────────────
    print(f"\nLoading encoder {EMB_MODEL} …", flush=True)
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMB_MODEL, device="cpu", trust_remote_code=True)
    model.max_seq_length = MAX_SEQ_LEN

    print("Encoding (cached on disk):", flush=True)
    Eg_seg_tr = encode_or_load("seg_train",  seg_tr.tolist(),  model)
    Eg_seg_te = encode_or_load("seg_test",   seg_te.tolist(),  model)
    Eg_lng_tr = encode_or_load("long_train", long_tr.tolist(), model)
    Eg_lng_te = encode_or_load("long_test",  long_te.tolist(), model)
    del model

    # ── Build TF-IDF ──────────────────────────────────────────────────────────
    print("\nTF-IDF features …", flush=True)
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

    # ── Discover other cached embeddings ──────────────────────────────────────
    extra = []
    for label, ed, prefix_pairs in [
        ("minilm", ROOT / "embeddings_v4",     [("seg_train", "seg_test"), ("long_train", "long_test")]),
        ("bge",    ROOT / "embeddings_v6_bge", [("seg_train", "seg_test"), ("long_train", "long_test")]),
        ("ftuned", ROOT / "models_v9",         [("ft_train", "ft_test")]),
    ]:
        for tr_n, te_n in prefix_pairs:
            tr_p = ed / f"{tr_n}.npy"; te_p = ed / f"{te_n}.npy"
            if tr_p.exists() and te_p.exists():
                a = np.load(tr_p); b = np.load(te_p)
                extra.append((f"{label}_{tr_n}", a, b))
                print(f"  found {label} {tr_n}: {a.shape}", flush=True)

    def to_sparse(arr): return csr_matrix(arr.astype(np.float32))

    # ── Build feature variants and test each ──────────────────────────────────
    y_tr = train["code"].values
    y_te = test["code"].values

    print("\n" + "=" * 70, flush=True)
    print("V11 — feature variants × calibrated classifiers", flush=True)
    print("=" * 70, flush=True)

    results = {}

    def run_variant(name, X_tr, X_te):
        print(f"\n--- {name}  (dim={X_tr.shape[1]:,}) ---", flush=True)
        # 1. LinearSVC C=1
        clf = LinearSVC(C=1.0, dual=False, class_weight="balanced", max_iter=MAX_ITER)
        t0 = time.time()
        clf.fit(X_tr, y_tr)
        preds = clf.predict(X_te)
        f1_l, n_l = report(y_te.tolist(), list(preds), f"LinearSVC ({time.time()-t0:.0f}s)")
        # 2. CalibratedSVC sigmoid
        cal = CalibratedClassifierCV(LinearSVC(C=1.0, dual=False, class_weight="balanced",
                                                max_iter=MAX_ITER),
                                      method="sigmoid", cv=3, n_jobs=-1)
        t0 = time.time()
        cal.fit(X_tr, y_tr)
        preds = cal.predict(X_te)
        f1_s, n_s = report(y_te.tolist(), list(preds), f"CalibratedSVC sigmoid ({time.time()-t0:.0f}s)")
        # 3. CalibratedSVC isotonic
        cal = CalibratedClassifierCV(LinearSVC(C=1.0, dual=False, class_weight="balanced",
                                                max_iter=MAX_ITER),
                                      method="isotonic", cv=3, n_jobs=-1)
        t0 = time.time()
        cal.fit(X_tr, y_tr)
        preds = cal.predict(X_te)
        f1_i, n_i = report(y_te.tolist(), list(preds), f"CalibratedSVC isotonic ({time.time()-t0:.0f}s)")
        return {
            "linearsvc":          {"f1": float(f1_l), "top10": n_l},
            "calibrated_sigmoid": {"f1": float(f1_s), "top10": n_s},
            "calibrated_isotonic":{"f1": float(f1_i), "top10": n_i},
        }

    # Variant A: gte-large alone + numerical
    Xa_tr = sparse_hstack([to_sparse(Eg_seg_tr), to_sparse(Eg_lng_tr), to_sparse(N_tr)], format="csr")
    Xa_te = sparse_hstack([to_sparse(Eg_seg_te), to_sparse(Eg_lng_te), to_sparse(N_te)], format="csr")
    results["A_gte_only"] = run_variant("A) gte-large + numerical", Xa_tr, Xa_te)

    # Variant B: gte-large + TF-IDF + numerical
    Xb_tr = sparse_hstack([Xs_tr, Xl_tr, to_sparse(Eg_seg_tr), to_sparse(Eg_lng_tr), to_sparse(N_tr)], format="csr")
    Xb_te = sparse_hstack([Xs_te, Xl_te, to_sparse(Eg_seg_te), to_sparse(Eg_lng_te), to_sparse(N_te)], format="csr")
    results["B_gte_tfidf"] = run_variant("B) gte-large + TF-IDF + numerical", Xb_tr, Xb_te)

    # Variant C: gte-large + TF-IDF + ALL other encoders + numerical (ULTIMATE STACK)
    parts_tr = [Xs_tr, Xl_tr, to_sparse(Eg_seg_tr), to_sparse(Eg_lng_tr)]
    parts_te = [Xs_te, Xl_te, to_sparse(Eg_seg_te), to_sparse(Eg_lng_te)]
    for name, a, b in extra:
        parts_tr.append(to_sparse(a))
        parts_te.append(to_sparse(b))
    parts_tr.append(to_sparse(N_tr))
    parts_te.append(to_sparse(N_te))
    Xc_tr = sparse_hstack(parts_tr, format="csr")
    Xc_te = sparse_hstack(parts_te, format="csr")
    results["C_ultimate"] = run_variant("C) ULTIMATE STACK (all encoders + TF-IDF + numerical)",
                                          Xc_tr, Xc_te)

    # ── Final ranking ─────────────────────────────────────────────────────────
    print("\n" + "=" * 70, flush=True)
    print("V11 RANKING — every (variant × classifier)", flush=True)
    print("=" * 70, flush=True)
    flat_results = []
    for variant, by_clf in results.items():
        for clf_name, r in by_clf.items():
            flat_results.append((f"{variant} / {clf_name}", r["f1"], r["top10"]))
    flat_results.sort(key=lambda x: -x[1])
    for name, f1, n in flat_results:
        marker = "<-- BEST" if f1 == flat_results[0][1] else ""
        print(f"  {name:55s} F1={f1*100:6.2f}%  top10={n}/10  {marker}", flush=True)

    best_name, best_f1, best_n = flat_results[0]
    print(f"\n  Winner: {best_name}", flush=True)
    print(f"  Macro F1: {best_f1*100:.2f}%   Target >= 75%: {'PASS' if best_f1 >= 0.75 else 'FAIL'}", flush=True)
    print(f"  Top-10 pass: {best_n}/10  (target >=8: {'PASS' if best_n >= 8 else 'FAIL'})", flush=True)

    summary = {
        "version": "v11-gte-large",
        "encoder": EMB_MODEL,
        "encoders_stacked": ["gte-large"] + [n for n, _, _ in extra],
        "results": {f"{v}/{c}": r for v, by in results.items() for c, r in by.items()},
        "winner": best_name,
        "best_f1": round(float(best_f1) * 100, 2),
        "best_top10": int(best_n),
        "target_met": bool(best_f1 >= 0.75),
    }
    (OUT_DIR / "training_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"  Saved to {OUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
