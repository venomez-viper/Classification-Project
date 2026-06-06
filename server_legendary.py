"""
TAVSS — Single Inference Server
================================
One server. Two models. One response.

  PRIMARY:  ModernBERT-large (MultiTask, 3-head) — Task 1 industry (145 classes)
  FALLBACK: Segment-Aware SVM cascade            — Task 1 industry (145 classes)
  TASK 2:   Hybrid cascade L4 SVM               — Sub-industry   (428 classes)

All results logged to SQLite. One endpoint: /api/predict

Run:
  python server_legendary.py   → http://localhost:5003
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS

from legendary.explanations import generate_explanation
from legendary.shared import get_label
from legendary.taxonomy_crosswalk import get_cross_taxonomy, load_crosswalk
from scripts.cascade_predict import load_cascade_assets
from scripts.cascade_predict_t2 import cascade_predict_t2, load_t2_hybrid_assets
from scripts.segment_aware_predict import load_segment_aware_assets, predict_segment_aware

app = Flask(__name__)
CORS(app)

ROOT     = Path(__file__).resolve().parent
DB_PATH  = ROOT / "serve" / "predictions.sqlite"

# ── Label / taxonomy data ─────────────────────────────────────────────────────
try:
    TAXONOMY        = json.loads((ROOT / "gecs_taxonomy.json").read_text(encoding="utf-8"))
    TAXONOMY_BY_CODE = {str(r["mstar_code"]): r for r in TAXONOMY}
except Exception:
    TAXONOMY         = []
    TAXONOMY_BY_CODE = {}

try:
    SUBINDUSTRY_LABELS = json.loads((ROOT / "models" / "sub_industry_labels.json").read_text(encoding="utf-8"))
except Exception:
    SUBINDUSTRY_LABELS = {}

CROSSWALK = load_crosswalk()

# ── ModernBERT-large (primary Task 1 model) ───────────────────────────────────
MB_READY = False
MB_ERROR = None
MB_MODEL = None
MB_TOKENIZER = None
MB_INDUSTRY_CLASSES = None   # np.ndarray shape (145,) of 8-digit string codes
MB_SECTOR_TO_IDX    = None   # dict code[:3] → int
MB_GROUP_TO_IDX     = None   # dict code[:5] → int
MB_IND_TO_GROUP     = None   # np.ndarray (145,) group idx per industry
MB_IND_TO_SECTOR    = None   # np.ndarray (145,) sector idx per industry
LAMBDA_GROUP        = 0.30
LAMBDA_SECTOR       = 0.03

_MB_WEIGHTS  = ROOT / "models_v3_modernbert" / "v3_minimal" / "best_model_state.pt"
_MB_TOK_DIR  = ROOT / "models_v3_modernbert" / "v3_minimal"
_MB_CLASSES  = ROOT / "V3 RESULTS -NEW" / "industry_classes.npy"

if _MB_WEIGHTS.exists() and _MB_CLASSES.exists():
    try:
        import torch
        import torch.nn as nn
        import torch.nn.functional as F
        from transformers import AutoModel, AutoTokenizer

        _device = torch.device("cpu")

        from transformers import AutoConfig
        # Only download the config (tiny JSON) — NOT the 1.58GB weights.
        # Our trained state dict provides all weights.
        _mb_config = AutoConfig.from_pretrained(
            "answerdotai/ModernBERT-large", trust_remote_code=True
        )
        _hidden = _mb_config.hidden_size  # 1024 for ModernBERT-large

        class _MultiTaskModernBERT(nn.Module):
            def __init__(self, n_sectors: int, n_groups: int, n_industries: int) -> None:
                super().__init__()
                # Instantiate architecture from config (random weights — replaced by state dict below)
                self.encoder     = AutoModel.from_config(_mb_config, trust_remote_code=True)
                self.norm        = nn.LayerNorm(_hidden)
                self.dropout     = nn.Dropout(0.10)
                self.sector_head   = nn.Linear(_hidden, n_sectors)
                self.group_head    = nn.Linear(_hidden, n_groups)
                self.industry_head = nn.Linear(_hidden, n_industries)

            def forward(self, input_ids, attention_mask):
                out    = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
                pooled = out.pooler_output if getattr(out, "pooler_output", None) is not None else out.last_hidden_state[:, 0]
                pooled = self.dropout(self.norm(pooled))
                return {
                    "sector_logits":   self.sector_head(pooled),
                    "group_logits":    self.group_head(pooled),
                    "industry_logits": self.industry_head(pooled),
                }

        print("Loading ModernBERT-large weights …")
        MB_INDUSTRY_CLASSES = np.load(str(_MB_CLASSES), allow_pickle=True)
        n_ind = len(MB_INDUSTRY_CLASSES)

        # Build sector / group label encoders from industry codes (no separate file needed)
        _sector_classes = sorted(set(c[:3] for c in MB_INDUSTRY_CLASSES))
        _group_classes  = sorted(set(c[:5] for c in MB_INDUSTRY_CLASSES))
        MB_SECTOR_TO_IDX = {c: i for i, c in enumerate(_sector_classes)}
        MB_GROUP_TO_IDX  = {c: i for i, c in enumerate(_group_classes)}
        n_sec = len(_sector_classes)
        n_grp = len(_group_classes)

        MB_IND_TO_GROUP  = np.array([MB_GROUP_TO_IDX[c[:5]]  for c in MB_INDUSTRY_CLASSES], dtype=np.int64)
        MB_IND_TO_SECTOR = np.array([MB_SECTOR_TO_IDX[c[:3]] for c in MB_INDUSTRY_CLASSES], dtype=np.int64)

        _model = _MultiTaskModernBERT(n_sec, n_grp, n_ind)
        _sd    = torch.load(str(_MB_WEIGHTS), map_location="cpu", weights_only=True)
        _model.load_state_dict(_sd, strict=True)
        _model.eval()
        _model.to(_device)

        MB_TOKENIZER = AutoTokenizer.from_pretrained(str(_MB_TOK_DIR), trust_remote_code=True)
        MB_MODEL     = _model

        MB_READY = True
        print(f"  ModernBERT-large OK — {n_ind} industry classes, device=cpu")

    except Exception as exc:
        MB_ERROR = str(exc)
        print(f"  ModernBERT-large FAILED: {exc}")
else:
    MB_ERROR = f"Weights not found at {_MB_WEIGHTS}"
    print(f"  ModernBERT-large skipped: {MB_ERROR}")

# ── SVM cascade (fast fallback for Task 1) ────────────────────────────────────
try:
    CASCADE_ASSETS = load_cascade_assets()
    CASCADE_READY  = True
except Exception as exc:
    CASCADE_ASSETS = None
    CASCADE_READY  = False

try:
    SEGMENT_AWARE_ASSETS = load_segment_aware_assets()
    SEGMENT_AWARE_READY  = True
except Exception as exc:
    SEGMENT_AWARE_ASSETS = None
    SEGMENT_AWARE_READY  = False

# ── Task 2 hybrid cascade ─────────────────────────────────────────────────────
try:
    T2_ASSETS = load_t2_hybrid_assets()
    T2_READY  = True
    T2_ERROR  = None
except Exception as exc:
    T2_ASSETS = None
    T2_READY  = False
    T2_ERROR  = str(exc)

TASK1_READY  = MB_READY or SEGMENT_AWARE_READY or CASCADE_READY
MODEL_VERSION = (
    "modernbert-large-v3-multitask" if MB_READY
    else "task1-segment-aware-svm"  if SEGMENT_AWARE_READY
    else "cascade-svm-fallback"
)

# ── Database ──────────────────────────────────────────────────────────────────
def _connect_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _init_db() -> None:
    with _connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id               TEXT PRIMARY KEY,
                timestamp        TEXT NOT NULL,
                input_text       TEXT NOT NULL,
                task1_code       TEXT,
                task1_label      TEXT,
                task1_confidence REAL,
                task2_code       TEXT,
                task2_label      TEXT,
                task2_confidence REAL,
                model_version    TEXT,
                latency_ms       REAL,
                status           TEXT DEFAULT 'predicted'
            )
        """)
        conn.commit()

def _log_prediction(rec: dict) -> None:
    with _connect_db() as conn:
        conn.execute("""
            INSERT INTO predictions (
                id, timestamp, input_text,
                task1_code, task1_label, task1_confidence,
                task2_code, task2_label, task2_confidence,
                model_version, latency_ms, status
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            rec["id"], rec["timestamp"], rec["input_text"],
            rec.get("task1_code"), rec.get("task1_label"), rec.get("task1_confidence"),
            rec.get("task2_code"), rec.get("task2_label"), rec.get("task2_confidence"),
            rec.get("model_version"), rec.get("latency_ms"), rec.get("status", "predicted"),
        ))
        conn.commit()

_init_db()

# ── Helpers ───────────────────────────────────────────────────────────────────
def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, round((pct / 100.0) * (len(ordered) - 1))))
    return round(float(ordered[idx]), 2)

def _confidence_histogram(values: list[float]) -> dict[str, int]:
    buckets = {f"{s}-{s+10}": 0 for s in range(0, 100, 10)}
    buckets["100"] = 0
    for v in values:
        v = max(0.0, min(100.0, float(v)))
        if v == 100.0:
            buckets["100"] += 1
        else:
            buckets[f"{int(v//10)*10}-{int(v//10)*10+10}"] += 1
    return buckets

def _taxonomy_entry(code: str) -> dict:
    e = TAXONOMY_BY_CODE.get(str(code), {})
    return {
        "code":               str(code),
        "industry_name":      e.get("industry_name") or get_label(code),
        "sector_name":        e.get("sector_name") or "",
        "official_definition": e.get("description") or "",
    }

def _task2_label(code: str | None) -> str:
    return SUBINDUSTRY_LABELS.get(str(code), f"Subindustry {code}") if code else ""

# ── ModernBERT inference ──────────────────────────────────────────────────────
def _predict_modernbert(text: str, top_n: int = 3) -> dict[str, Any]:
    import torch
    import torch.nn.functional as F
    enc = MB_TOKENIZER(
        [text], truncation=True, padding="max_length",
        max_length=512, return_tensors="pt",
    )
    enc = {k: v.to(torch.device("cpu")) for k, v in enc.items()}
    with torch.no_grad():
        out = MB_MODEL(**enc)

    # Hierarchy-aware scoring (dev-tuned lambdas from training)
    ind_logp  = F.log_softmax(out["industry_logits"], dim=-1)   # (1, 145)
    grp_logp  = F.log_softmax(out["group_logits"],    dim=-1)   # (1, 55)
    sec_logp  = F.log_softmax(out["sector_logits"],   dim=-1)   # (1, 11)

    _ig = torch.from_numpy(MB_IND_TO_GROUP)    # (145,)
    _is = torch.from_numpy(MB_IND_TO_SECTOR)   # (145,)

    score = (
        ind_logp
        + LAMBDA_GROUP  * grp_logp[0, _ig].unsqueeze(0)
        + LAMBDA_SECTOR * sec_logp[0, _is].unsqueeze(0)
    )  # (1, 145)

    probs   = score.softmax(dim=-1)[0].cpu().numpy()
    order   = np.argsort(probs)[::-1][:top_n]
    alts    = [
        {
            "rank":       int(r) + 1,
            "code":       str(MB_INDUSTRY_CLASSES[idx]),
            "label":      get_label(str(MB_INDUSTRY_CLASSES[idx])),
            "confidence": round(float(probs[idx]) * 100.0, 1),
        }
        for r, idx in enumerate(order)
    ]
    best = int(order[0])
    return {
        "code":        str(MB_INDUSTRY_CLASSES[best]),
        "confidence":  round(float(probs[best]) * 100.0, 1),
        "alternatives": alts,
        "engine":      "ModernBERT-large",
    }

# ── SVM cascade inference (fallback) ─────────────────────────────────────────
def _predict_svm(company_text: str, segment_text: str) -> dict[str, Any]:
    if SEGMENT_AWARE_READY and SEGMENT_AWARE_ASSETS is not None:
        r = predict_segment_aware(
            company_text=company_text,
            segment_text=segment_text,
            assets=SEGMENT_AWARE_ASSETS,
        )
        return {
            "code":        r["mstar_code"],
            "confidence":  r["confidence"],
            "alternatives": [
                {"rank": a["rank"], "code": a["code"],
                 "label": get_label(a["code"]), "confidence": a["confidence"]}
                for a in r.get("alternatives", [])
            ],
            "engine": "Segment-Aware SVM Cascade",
        }
    # bare cascade fallback (no segment awareness)
    from scripts.cascade_predict import cascade_predict
    r = cascade_predict(company_text, CASCADE_ASSETS, top_n=3)
    return {
        "code":       r["mstar_code"],
        "confidence": r["confidence"],
        "alternatives": [
            {"rank": a["rank"], "code": a["label"],
             "label": get_label(a["label"]), "confidence": a["confidence"]}
            for a in r.get("alternatives", {}).get("code", [])
        ],
        "engine": "SVM Cascade (bare)",
    }

# ── Unified Task 1 prediction ─────────────────────────────────────────────────
def _predict_task1(company_text: str, segment_text: str) -> dict[str, Any]:
    if MB_READY:
        return _predict_modernbert(company_text, top_n=3)
    if SEGMENT_AWARE_READY or CASCADE_READY:
        return _predict_svm(company_text, segment_text)
    raise RuntimeError("No Task 1 model available.")

# ── Task 2 prediction ─────────────────────────────────────────────────────────
def _predict_task2(segment_text: str, full_text: str) -> dict | None:
    if not T2_READY or T2_ASSETS is None:
        return None
    r = cascade_predict_t2(segment_text=segment_text, full_text=full_text, assets=T2_ASSETS, top_n=3)
    sub_code = r["sub_code"]
    return {
        "code":              sub_code,
        "subindustry_name":  _task2_label(sub_code),
        "confidence":        round(float(r["confidence"]) / 100.0, 4),
        "confidence_percent": r["confidence"],
        "constrained_by_task1": True,
        "parent_mstar_code": r["mstar_code"],
        "alternatives": [
            {
                "code":              alt["label"],
                "subindustry_name":  _task2_label(alt["label"]),
                "confidence":        round(float(alt["confidence"]) / 100.0, 4),
                "confidence_percent": alt["confidence"],
            }
            for alt in r["alternatives"]["sub"]
        ],
    }

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return "TAVSS server online", 200

@app.get("/health")
def health():
    return jsonify({
        "status":          "ok" if TASK1_READY else "degraded",
        "ok":              TASK1_READY,
        "model_version":   MODEL_VERSION,
        "modernbert_ready": MB_READY,
        "modernbert_error": MB_ERROR,
        "svm_cascade_ready": CASCADE_READY,
        "segment_aware_ready": SEGMENT_AWARE_READY,
        "task2_ready":     T2_READY,
        "task2_error":     T2_ERROR,
        "crosswalk_entries": len(CROSSWALK),
        "taxonomy_entries":  len(TAXONOMY_BY_CODE),
    }), (200 if TASK1_READY else 503)

def _handle_predict(payload: dict) -> tuple[dict, int]:
    if not TASK1_READY:
        return {"error": "No Task 1 model is available."}, 503

    company_text = str(payload.get("company_text") or payload.get("text") or "").strip()
    segment_text = str(payload.get("segment_text") or company_text).strip()
    include_reasoning = bool(payload.get("include_reasoning", False))

    if not company_text:
        return {"error": "company_text is required."}, 400

    started      = time.perf_counter()
    prediction_id = str(uuid.uuid4())

    t1_started = time.perf_counter()
    t1_raw     = _predict_task1(company_text, segment_text)
    t1_ms      = (time.perf_counter() - t1_started) * 1000.0

    code     = t1_raw["code"]
    taxonomy = _taxonomy_entry(code)
    label    = taxonomy["industry_name"]
    conf     = t1_raw["confidence"]

    explanation = generate_explanation(company_text, label, code, t1_raw["engine"]) if include_reasoning else {"text": None, "engine": None}
    taxonomy_map = get_cross_taxonomy(code, CROSSWALK)

    alternatives = [
        {
            "code":             alt["code"],
            "industry_name":    alt["label"],
            "confidence":       round(float(alt["confidence"]) / 100.0, 4),
            "confidence_percent": alt["confidence"],
        }
        for alt in t1_raw.get("alternatives", [])
    ]

    t2_started = time.perf_counter()
    task2 = task2_error = None
    try:
        task2 = _predict_task2(segment_text, company_text)
    except Exception as exc:
        task2_error = str(exc)
    t2_ms = (time.perf_counter() - t2_started) * 1000.0

    total_ms = (time.perf_counter() - started) * 1000.0

    response = {
        "prediction_id": prediction_id,
        "success":       True,
        "engine":        t1_raw["engine"],
        "model_version": MODEL_VERSION,
        "task1": {
            "code":               code,
            "industry_name":      label,
            "sector_name":        taxonomy["sector_name"],
            "official_definition": taxonomy["official_definition"],
            "confidence":         round(conf / 100.0, 4),
            "confidence_percent": conf,
        },
        "task2":        task2,
        "task2_error":  task2_error,
        "alternatives": alternatives,
        "reasoning":    explanation["text"] if include_reasoning else None,
        "taxonomy_map": taxonomy_map,
        "route_reason": f"Primary model: {t1_raw['engine']}",
        "trace": {
            "task1_ms": round(t1_ms, 2),
            "task2_ms": round(t2_ms, 2),
            "total_ms": round(total_ms, 2),
        },
        # Flat fields for frontend compatibility
        "mstar_code":     code,
        "mstar_label":    label,
        "confidence_t1":  conf,
        "alternatives_t1": [
            {"rank": i + 1, "code": a["code"],
             "label": a["industry_name"], "confidence": a["confidence_percent"]}
            for i, a in enumerate(alternatives)
        ],
        "sub_code":  task2["code"]             if task2 else None,
        "sub_label": task2["subindustry_name"] if task2 else None,
        "confidence_t2": task2["confidence_percent"] if task2 else None,
        "alternatives_t2": [
            {"rank": i+1, "label": a["subindustry_name"],
             "code": a["code"], "confidence": a["confidence_percent"]}
            for i, a in enumerate(task2.get("alternatives", []))
        ] if task2 else [],
    }

    _log_prediction({
        "id":        prediction_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_text": company_text,
        "task1_code": code,
        "task1_label": label,
        "task1_confidence": conf,
        "task2_code":  task2["code"]             if task2 else None,
        "task2_label": task2["subindustry_name"] if task2 else None,
        "task2_confidence": task2["confidence_percent"] if task2 else None,
        "model_version": MODEL_VERSION,
        "latency_ms": round(total_ms, 2),
    })

    return response, 200

# Single canonical prediction endpoint — all aliases point here
@app.post("/api/predict")
@app.post("/api/predict_legendary")
@app.post("/api/predict_routed")
@app.post("/predict")
def predict():
    payload = request.get_json(silent=True) or {}
    body, status = _handle_predict(payload)
    return jsonify(body), status

@app.get("/history")
def history():
    limit = min(200, max(1, int(request.args.get("limit", 50))))
    with _connect_db() as conn:
        rows = conn.execute("""
            SELECT id, timestamp, input_text, task1_code, task1_label, task1_confidence,
                   task2_code, task2_label, task2_confidence, model_version, latency_ms, status
            FROM predictions ORDER BY timestamp DESC LIMIT ?
        """, (limit,)).fetchall()
    return jsonify({"items": [dict(r) for r in rows]})

@app.get("/metrics")
def metrics():
    with _connect_db() as conn:
        rows = conn.execute("SELECT latency_ms, task1_confidence, task1_code FROM predictions").fetchall()
    latencies    = [float(r["latency_ms"]) for r in rows if r["latency_ms"] is not None]
    confidences  = [float(r["task1_confidence"]) for r in rows if r["task1_confidence"] is not None]
    top_classes: dict[str, int] = {}
    for r in rows:
        if r["task1_code"]:
            top_classes[r["task1_code"]] = top_classes.get(r["task1_code"], 0) + 1
    return jsonify({
        "total_predictions": len(rows),
        "latency_ms": {
            "p50": _percentile(latencies, 50),
            "p95": _percentile(latencies, 95),
            "p99": _percentile(latencies, 99),
        },
        "confidence_histogram": _confidence_histogram(confidences),
        "top_predicted_classes": [
            {"code": c, "label": get_label(c), "count": n}
            for c, n in sorted(top_classes.items(), key=lambda x: x[1], reverse=True)[:10]
        ],
    })

@app.post("/feedback")
@app.post("/api/feedback")
def feedback():
    payload       = request.get_json(silent=True) or {}
    prediction_id = str(payload.get("prediction_id", "")).strip()
    status        = str(payload.get("status", "reviewed")).strip() or "reviewed"
    if not prediction_id:
        return jsonify({"error": "prediction_id is required."}), 400
    with _connect_db() as conn:
        updated = conn.execute(
            "UPDATE predictions SET status = ? WHERE id = ?",
            (status, prediction_id),
        ).rowcount
        conn.commit()
    if not updated:
        return jsonify({"error": "prediction_id not found."}), 404
    return jsonify({"success": True, "prediction_id": prediction_id, "status": status})

if __name__ == "__main__":
    port = int(__import__("os").environ.get("PORT", 5003))
    try:
        from waitress import serve
        print(f"TAVSS server starting on http://localhost:{port}")
        serve(app, host="0.0.0.0", port=port)
    except ImportError:
        print(f"Dev server starting on http://localhost:{port}")
        app.run(debug=False, port=port)
