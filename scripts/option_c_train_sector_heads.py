"""Option C — Sector-conditioned L3 head on ModernBERT-large CLS embeddings.

Inputs (produced by the Colab embedding-extraction notebook):
  embeddings_v3/train_cls.npy        (n_train, 1024) float16/32
  embeddings_v3/test_cls.npy         (n_test,  1024) float16/32
  embeddings_v3/train_meta.csv       columns: mstar_code, sector_code, group_code, CompanyId
  embeddings_v3/test_meta.csv        same schema

Output:
  models_v3_cascade/cascade_sector_clf.joblib    sector classifier (LogReg or LinearSVC)
  models_v3_cascade/cascade_l3_per_sector.joblib dict[sector_code] -> classifier
  models_v3_cascade/test_predictions_cascade.csv true_code, pred_code (drop in to analyze_predictions.py)
  models_v3_cascade/training_summary.json

Strategy:
  1. Train one sector classifier on full train embeddings (predict 11 sector codes).
  2. For each sector, train a sector-restricted L3 head on rows of that sector
     (predict the MSTAR code among the codes that exist in that sector).
  3. At inference: predict sector → route to sector-specific L3 head → output MSTAR code.

  Sector accuracy on dev was 86.81% in v3, so the cascade carries a ~13% routing-error
  penalty. The hope is that within-sector classification gains more than that.
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, classification_report
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parent.parent
EMBED_DIR = ROOT / "embeddings_v3"
OUT_DIR = ROOT / "models_v3_cascade"
OUT_DIR.mkdir(exist_ok=True)


def sector_of(code) -> str:
    return str(code)[:3]


def group_of(code) -> str:
    return str(code)[:5]


def train_sector_clf(X, y):
    print(f"  training sector classifier on {len(X)} rows, {len(set(y))} sectors")
    # LogReg with strong regularization is a good default on dense embeddings
    clf = LogisticRegression(
        max_iter=2000,
        C=1.0,
        n_jobs=-1,
        class_weight="balanced",
        solver="lbfgs",
    )
    clf.fit(X, y)
    return clf


def train_l3_per_sector(X, y, sector_codes):
    """Train one L3 classifier per sector, restricted to rows in that sector."""
    by_sector = {}
    sectors = sorted(set(sector_codes))
    for sec in sectors:
        mask = sector_codes == sec
        n = mask.sum()
        n_classes = len(set(y[mask]))
        if n_classes <= 1:
            print(f"    sector {sec}: {n} rows, {n_classes} class — skipping (degenerate)")
            by_sector[sec] = ("constant", y[mask][0] if n > 0 else None)
            continue
        clf = LinearSVC(C=1.0, class_weight="balanced", max_iter=4000, dual="auto")
        clf.fit(X[mask], y[mask])
        train_acc = (clf.predict(X[mask]) == y[mask]).mean()
        print(f"    sector {sec}: {n} rows, {n_classes} L3 classes, train_acc={train_acc:.2%}")
        by_sector[sec] = ("svm", clf)
    return by_sector


def predict_cascade(X, sector_clf, l3_per_sector):
    pred_sectors = sector_clf.predict(X)
    out = np.empty(len(X), dtype=object)
    for sec in set(pred_sectors):
        mask = pred_sectors == sec
        if sec not in l3_per_sector:
            out[mask] = "00000000"  # unknown sector
            continue
        kind, clf = l3_per_sector[sec]
        if kind == "constant":
            out[mask] = clf
        else:
            out[mask] = clf.predict(X[mask])
    return out, pred_sectors


def main():
    print(f"Loading embeddings from {EMBED_DIR}")
    X_train = np.load(EMBED_DIR / "train_cls.npy").astype(np.float32)
    X_test = np.load(EMBED_DIR / "test_cls.npy").astype(np.float32)
    train_meta = pd.read_csv(EMBED_DIR / "train_meta.csv")
    test_meta = pd.read_csv(EMBED_DIR / "test_meta.csv")
    print(f"  train: {X_train.shape}, test: {X_test.shape}")
    assert len(X_train) == len(train_meta)
    assert len(X_test) == len(test_meta)

    train_meta["sector"] = train_meta["mstar_code"].astype(str).apply(sector_of)
    test_meta["sector"] = test_meta["mstar_code"].astype(str).apply(sector_of)

    # ---------- Stage 1: sector classifier ----------
    print("\nStage 1: sector classifier")
    sector_clf = train_sector_clf(X_train, train_meta["sector"].values)
    sector_acc = (sector_clf.predict(X_test) == test_meta["sector"].values).mean()
    print(f"  TEST sector acc: {sector_acc:.4%}")

    # ---------- Stage 2: per-sector L3 heads ----------
    print("\nStage 2: per-sector L3 heads")
    l3_per_sector = train_l3_per_sector(
        X_train, train_meta["mstar_code"].astype(str).values, train_meta["sector"].values
    )

    # ---------- Stage 3: cascade prediction on test ----------
    print("\nStage 3: cascade inference on test")
    pred_codes, pred_sectors = predict_cascade(X_test, sector_clf, l3_per_sector)
    true_codes = test_meta["mstar_code"].astype(str).values
    headline_acc = (pred_codes == true_codes).mean()
    headline_f1 = f1_score(true_codes, pred_codes, average="macro", zero_division=0)
    print(f"\n  CASCADE TEST acc:      {headline_acc:.4%}")
    print(f"  CASCADE TEST macro F1: {headline_f1:.4%}")

    # ---------- Save artifacts ----------
    joblib.dump(sector_clf, OUT_DIR / "cascade_sector_clf.joblib")
    joblib.dump(l3_per_sector, OUT_DIR / "cascade_l3_per_sector.joblib")
    pd.DataFrame({"true_code": true_codes, "pred_code": pred_codes}).to_csv(
        OUT_DIR / "test_predictions_cascade.csv", index=False
    )
    summary = {
        "n_train": len(X_train),
        "n_test": len(X_test),
        "n_sectors_train": int(train_meta["sector"].nunique()),
        "test_sector_acc": float(sector_acc),
        "test_headline_acc": float(headline_acc),
        "test_headline_macro_f1": float(headline_f1),
        "embedding_dim": int(X_train.shape[1]),
    }
    with open(OUT_DIR / "training_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved to {OUT_DIR}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
