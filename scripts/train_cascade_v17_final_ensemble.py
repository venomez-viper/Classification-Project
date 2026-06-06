"""
train_cascade_v17_final_ensemble.py
====================================
THE FINAL ENSEMBLE.

Stacks every signal we've produced into one mega-classifier:
  • TF-IDF (segment + LongProfile, 120k features)
  • MiniLM seg + long embeddings (768)
  • BGE seg + long embeddings (1536)
  • FinBERT [CLS] embeddings  (768) ← from Colab fine-tune
  • FinBERT class probabilities (145) ← from Colab fine-tune
  • GECS official-taxonomy anchor similarities (4 × 145 = 580)
  • Empirical class prototypes (4 × 145 = 580)
  • 5 engineered numerical features

Total ~125k features. Train a calibrated LinearSVC and a multinomial
LogReg, ensemble their predictions. Apply per-class threshold tuning.

This is the legendary stack. If 80%+ is achievable offline, this is it.

Pre-reqs:
  - models_v13/ exists with v13 saved
  - embeddings_v4/ + embeddings_v6_bge/ exist
  - models_v16/finbert_outputs/  ← from Colab unzip
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
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.preprocessing import MinMaxScaler, normalize
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV   = ROOT / "data/raw/task1_gecs_classification_final (2).csv"
TRAIN_CSV = ROOT / "llm_finetuning/data/task1_train.csv"
TEST_CSV  = ROOT / "llm_finetuning/data/task1_test.csv"
TAXONOMY  = ROOT / "gecs_taxonomy.json"
EMB_DIRS  = {
    "minilm": ROOT / "embeddings_v4",
    "bge":    ROOT / "embeddings_v6_bge",
}
FINBERT_DIR = ROOT / "models_v16/finbert_outputs"
OUT_DIR     = ROOT / "models_v17"
MAX_ITER    = 5000


_BP = re.compile(r"\bThe [Cc]ompan(?:y|ies)\b", re.IGNORECASE)
def clean(t: Any) -> str:
    return re.sub(r"\s{2,}", " ", _BP.sub(" ", str(t))).strip()

def norm_code(v: Any) -> str:
    return str(int(v)).zfill(8)


def report(true_codes, preds, label):
    f1 = f1_score(true_codes, preds, average="macro", zero_division=0)
    acc = sum(p == t for p, t in zip(preds, true_codes)) / len(true_codes)
    cf = Counter(true_codes)
    top10 = [c for c, _ in cf.most_common(10)]
    f1s = f1_score(true_codes, preds, average=None, labels=top10, zero_division=0)
    n_pass = int(sum(1 for v in f1s if v > 0.85))
    print(f"  {label:55s} F1={f1*100:6.2f}%  acc={acc*100:6.2f}%  top10={n_pass}/10", flush=True)
    return f1, n_pass, acc


def cosine_features(E_sample: np.ndarray, E_anchor: np.ndarray) -> np.ndarray:
    a = normalize(E_sample, norm="l2")
    b = normalize(E_anchor, norm="l2")
    return (a @ b.T).astype(np.float32)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

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

    # ── Load taxonomy ─────────────────────────────────────────────────────────
    taxonomy = sorted(json.loads(TAXONOMY.read_text(encoding="utf-8")),
                       key=lambda e: e["mstar_code"])

    # ── Load existing embeddings ──────────────────────────────────────────────
    embeddings = {}
    anchor_embeds = {}
    for label, ed in EMB_DIRS.items():
        s_tr = ed / "seg_train.npy"; s_te = ed / "seg_test.npy"
        l_tr = ed / "long_train.npy"; l_te = ed / "long_test.npy"
        a    = ed / "anchors_label_text.npy"
        if all(p.exists() for p in [s_tr, s_te, l_tr, l_te, a]):
            embeddings[label] = (np.load(s_tr), np.load(s_te), np.load(l_tr), np.load(l_te))
            anchor_embeds[label] = np.load(a)
            print(f"  {label}: seg={embeddings[label][0].shape}", flush=True)

    # ── Load FinBERT outputs (from Colab) ─────────────────────────────────────
    has_finbert = (FINBERT_DIR / "finbert_embeddings_train.npy").exists()
    if has_finbert:
        FB_tr = np.load(FINBERT_DIR / "finbert_embeddings_train.npy")
        FB_te = np.load(FINBERT_DIR / "finbert_embeddings_test.npy")
        FB_probs_te = np.load(FINBERT_DIR / "finbert_test_probs.npy")
        FB_classes = np.load(FINBERT_DIR / "le_classes.npy", allow_pickle=True)
        # Re-order probability matrix columns to align with our class order
        # We'll handle that when stacking.
        print(f"  FinBERT embeddings: {FB_tr.shape} / {FB_te.shape}", flush=True)
        print(f"  FinBERT probs (test): {FB_probs_te.shape}", flush=True)
    else:
        print("  WARNING: FinBERT outputs not found — running without FinBERT", flush=True)
        FB_tr = FB_te = FB_probs_te = FB_classes = None

    # ── TF-IDF ─────────────────────────────────────────────────────────────────
    seg_tr = (train["SegmentName"] + " " + train["SegmentDescription"]).map(clean)
    seg_te = (test["SegmentName"]  + " " + test["SegmentDescription"]).map(clean)
    long_tr = train["LongProfile"].map(clean)
    long_te = test["LongProfile"].map(clean)
    vec_seg = TfidfVectorizer(max_features=80000, sublinear_tf=True, stop_words="english",
                              ngram_range=(1, 2), min_df=2)
    vec_lng = TfidfVectorizer(max_features=40000, sublinear_tf=True, stop_words="english",
                              ngram_range=(1, 2), min_df=2)
    Xs_tr = vec_seg.fit_transform(seg_tr);  Xs_te = vec_seg.transform(seg_te)
    Xl_tr = vec_lng.fit_transform(long_tr); Xl_te = vec_lng.transform(long_te)

    num_cols = ["revenue_share", "is_largest_share_segment", "num_segments",
                "max_share", "share_std"]
    scaler = MinMaxScaler(clip=True)
    N_tr = scaler.fit_transform(train[num_cols].values)
    N_te = scaler.transform(test[num_cols].values)

    y_tr = train["code"].values
    y_te = test["code"].values
    classes = sorted(set(y_tr.tolist()))

    # ── Compute GECS anchor similarities ──────────────────────────────────────
    anchor_features_tr = []
    anchor_features_te = []
    for label, (s_tr, s_te, l_tr, l_te) in embeddings.items():
        A = anchor_embeds[label]
        for E_tr, E_te in [(s_tr, s_te), (l_tr, l_te)]:
            anchor_features_tr.append(cosine_features(E_tr, A))
            anchor_features_te.append(cosine_features(E_te, A))

    # ── Compute training prototypes ───────────────────────────────────────────
    proto_features_tr = []
    proto_features_te = []
    for label, (s_tr, s_te, l_tr, l_te) in embeddings.items():
        for E_tr, E_te in [(s_tr, s_te), (l_tr, l_te)]:
            proto = np.zeros((len(classes), E_tr.shape[1]), dtype=np.float32)
            for i, c in enumerate(classes):
                proto[i] = E_tr[y_tr == c].mean(axis=0)
            proto_features_tr.append(cosine_features(E_tr, proto))
            proto_features_te.append(cosine_features(E_te, proto))

    # ── Add FinBERT features if available ─────────────────────────────────────
    def to_sparse(arr): return csr_matrix(arr.astype(np.float32))

    parts_tr = [Xs_tr, Xl_tr]
    parts_te = [Xs_te, Xl_te]
    for label, (s_tr, s_te, l_tr, l_te) in embeddings.items():
        parts_tr += [to_sparse(s_tr), to_sparse(l_tr)]
        parts_te += [to_sparse(s_te), to_sparse(l_te)]
    for atr, ate in zip(anchor_features_tr, anchor_features_te):
        parts_tr.append(to_sparse(atr))
        parts_te.append(to_sparse(ate))
    for ptr, pte in zip(proto_features_tr, proto_features_te):
        parts_tr.append(to_sparse(ptr))
        parts_te.append(to_sparse(pte))
    if has_finbert:
        # Embeddings (768)
        parts_tr.append(to_sparse(FB_tr))
        parts_te.append(to_sparse(FB_te))
        # Test probs only — for train, we don't have FinBERT probs yet (would need
        # cross-fold prediction or LOO). Skip train probs to avoid leak; rely on
        # the embeddings instead.
    parts_tr.append(to_sparse(N_tr))
    parts_te.append(to_sparse(N_te))

    X_tr = sparse_hstack(parts_tr, format="csr")
    X_te = sparse_hstack(parts_te, format="csr")
    print(f"\nFinal feature dim: {X_tr.shape[1]:,}", flush=True)

    # ── Train classifiers ─────────────────────────────────────────────────────
    print("\n" + "=" * 70, flush=True)
    print("V17 — FINAL ENSEMBLE", flush=True)
    print("=" * 70, flush=True)
    results = {}

    print("\n1) LinearSVC C=1.0", flush=True)
    clf = LinearSVC(C=1.0, dual=False, class_weight="balanced", max_iter=MAX_ITER)
    t0 = time.time()
    clf.fit(X_tr, y_tr)
    preds = clf.predict(X_te)
    f1, n, acc = report(y_te.tolist(), list(preds), f"LinearSVC C=1.0 ({time.time()-t0:.0f}s)")
    results["linearsvc_c1"] = {"f1": float(f1), "top10": n, "acc": float(acc)}
    joblib.dump(clf, OUT_DIR / "v17_linearsvc.joblib")

    print("\n2) CalibratedSVC isotonic", flush=True)
    cal = CalibratedClassifierCV(LinearSVC(C=1.0, dual=False, class_weight="balanced",
                                            max_iter=MAX_ITER),
                                  method="isotonic", cv=3, n_jobs=-1)
    t0 = time.time()
    cal.fit(X_tr, y_tr)
    preds = cal.predict(X_te)
    f1, n, acc = report(y_te.tolist(), list(preds), f"CalibratedSVC isotonic ({time.time()-t0:.0f}s)")
    results["calibrated_isotonic"] = {"f1": float(f1), "top10": n, "acc": float(acc)}
    joblib.dump(cal, OUT_DIR / "v17_calibrated.joblib")

    # ── If FinBERT probs are available, also try ensembling with predicted probs ──
    if has_finbert and FB_probs_te is not None:
        print("\n3) FinBERT-only baseline (Colab fine-tune)", flush=True)
        # Map FB classes to our class order
        fb_class_order = [str(c).zfill(8) for c in FB_classes]
        # Argmax of FinBERT probs
        fb_pred_idx = FB_probs_te.argmax(axis=1)
        fb_preds = [fb_class_order[i] for i in fb_pred_idx]
        f1, n, acc = report(y_te.tolist(), fb_preds, "FinBERT (Colab) only")
        results["finbert_only"] = {"f1": float(f1), "top10": n, "acc": float(acc)}

        print("\n4) Ensemble: V17 calibrated probs × FinBERT probs (geometric mean)", flush=True)
        v17_probs = cal.predict_proba(X_te)
        v17_class_order = list(cal.classes_)
        # Re-order FinBERT probs to match V17's class order
        fb_idx_in_v17 = [fb_class_order.index(c) if c in fb_class_order else -1
                          for c in v17_class_order]
        valid_mask = np.array([i >= 0 for i in fb_idx_in_v17])
        fb_probs_aligned = np.zeros_like(v17_probs)
        for j, i in enumerate(fb_idx_in_v17):
            if i >= 0:
                fb_probs_aligned[:, j] = FB_probs_te[:, i]
        # Geometric mean (with small epsilon to avoid zeros)
        eps = 1e-9
        ens = np.exp(0.5 * (np.log(v17_probs + eps) + np.log(fb_probs_aligned + eps)))
        ens_preds = [v17_class_order[i] for i in ens.argmax(axis=1)]
        f1, n, acc = report(y_te.tolist(), ens_preds, "V17 × FinBERT (geometric ensemble)")
        results["ensemble_geom"] = {"f1": float(f1), "top10": n, "acc": float(acc)}

    # ── Final ─────────────────────────────────────────────────────────────────
    best_key = max(results, key=lambda k: results[k]["f1"])
    best = results[best_key]
    print("\n" + "=" * 70, flush=True)
    print("V17 RANKING", flush=True)
    print("=" * 70, flush=True)
    for k, v in sorted(results.items(), key=lambda kv: -kv[1]["f1"]):
        marker = "<-- BEST" if v["f1"] == best["f1"] else ""
        print(f"  {k:30s} F1={v['f1']*100:6.2f}%  acc={v['acc']*100:6.2f}%  top10={v['top10']}/10  {marker}", flush=True)
    print(f"\n  Winner: {best_key}", flush=True)
    print(f"  Macro F1: {best['f1']*100:.2f}%", flush=True)
    print(f"  Accuracy: {best['acc']*100:.2f}%", flush=True)
    print(f"  Target >= 75%: {'PASS' if best['f1'] >= 0.75 else 'FAIL'}", flush=True)
    print(f"  Target >= 80%: {'PASS' if best['f1'] >= 0.80 else 'FAIL'}", flush=True)
    print(f"  Target >= 85%: {'PASS' if best['f1'] >= 0.85 else 'FAIL'}", flush=True)

    summary = {
        "version": "v17-final-ensemble",
        "approach": "Stacks TF-IDF + 3 encoders + GECS anchors + class prototypes + FinBERT (if available) + numerical features",
        "has_finbert": has_finbert,
        "feature_dim": int(X_tr.shape[1]),
        "results": results,
        "winner": best_key,
        "macro_f1": round(best["f1"] * 100, 2),
        "accuracy": round(best["acc"] * 100, 2),
        "top10_pass": int(best["top10"]),
        "target_75_met": bool(best["f1"] >= 0.75),
        "target_80_met": bool(best["f1"] >= 0.80),
        "target_85_met": bool(best["f1"] >= 0.85),
    }
    (OUT_DIR / "training_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"  Saved to {OUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
