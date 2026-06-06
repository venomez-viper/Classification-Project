"""
Local inference server for the fine-tuned DeBERTa GECS classifier.

Loads both Task 1 (145 industry codes) and Task 2 (407 subindustry codes)
and returns both predictions in a single API call.

Works like Ollama — one command starts it, then it accepts API requests
from anywhere on the machine until you stop it.

Usage:
    python llm_finetuning/scripts/serve.py
    python llm_finetuning/scripts/serve.py --port 8001

Endpoints:
    POST /classify          — classify a single description (industry + subindustry)
    POST /classify/batch    — classify multiple descriptions at once
    GET  /health            — check server and which models are loaded
    GET  /info              — model info, label counts, loaded tasks
"""

import argparse
import json
import os
import time

os.environ["TRANSFORMERS_OFFLINE"] = "1"

import numpy as np
import torch
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(ROOT, "llm_finetuning", "data")
RESULTS  = os.path.join(ROOT, "llm_finetuning", "results")
MAX_LEN  = 128


# ── Request / Response models ─────────────────────────────────────────────────
class ClassifyRequest(BaseModel):
    text: str
    top_k: int = 3

class ClassifyBatchRequest(BaseModel):
    texts: list[str]
    top_k: int = 3

class Prediction(BaseModel):
    code: str
    score: float

class TaskResult(BaseModel):
    predicted_code: str
    confidence: float
    top_k: list[Prediction]

class ClassifyResponse(BaseModel):
    industry: TaskResult                    # Task 1 — 145 GECS industry codes
    subindustry: TaskResult | None = None   # Task 2 — 407 subindustry codes (None if not trained yet)
    latency_ms: float

class BatchResponse(BaseModel):
    results: list[ClassifyResponse]
    total_latency_ms: float


# ── Single-task model wrapper ─────────────────────────────────────────────────
class SingleClassifier:
    def __init__(self, task: str, device: str):
        self.task   = task
        self.device = device

        model_path = os.path.join(RESULTS, f"{task}_best_model")
        if not os.path.isdir(model_path):
            raise FileNotFoundError(model_path)

        with open(os.path.join(DATA_DIR, f"{task}_idx_to_code.json")) as f:
            self.idx_to_code = {int(k): str(v) for k, v in json.load(f).items()}
        self.num_labels = len(self.idx_to_code)

        self.tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
        self.model     = AutoModelForSequenceClassification.from_pretrained(
            model_path, num_labels=self.num_labels, local_files_only=True
        ).to(device)
        self.model.eval()

    def predict(self, texts: list[str], top_k: int) -> list[TaskResult]:
        enc = self.tokenizer(
            texts, truncation=True, padding="max_length",
            max_length=MAX_LEN, return_tensors="pt"
        )
        enc = {k: v.to(self.device) for k, v in enc.items()
               if k in ("input_ids", "attention_mask")}

        with torch.no_grad():
            probs = torch.softmax(self.model(**enc).logits, dim=-1).cpu().numpy()

        results = []
        for i in range(len(texts)):
            top_idx = np.argsort(probs[i])[::-1][:top_k]
            results.append(TaskResult(
                predicted_code=self.idx_to_code[int(top_idx[0])],
                confidence=round(float(probs[i][top_idx[0]]) * 100, 2),
                top_k=[
                    Prediction(code=self.idx_to_code[int(j)],
                               score=round(float(probs[i][j]) * 100, 2))
                    for j in top_idx
                ]
            ))
        return results


# ── Combined classifier (loads both tasks) ────────────────────────────────────
class GECSClassifier:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Device: {self.device}", flush=True)

        print("Loading Task 1 (industry, 145 classes) ...", flush=True)
        self.task1 = SingleClassifier("task1", self.device)
        print(f"  Task 1 ready — {self.task1.num_labels} classes", flush=True)

        print("Loading Task 2 (subindustry, 407 classes) ...", flush=True)
        try:
            self.task2 = SingleClassifier("task2", self.device)
            print(f"  Task 2 ready — {self.task2.num_labels} classes", flush=True)
        except FileNotFoundError:
            self.task2 = None
            print("  Task 2 not trained yet — /classify will return industry only", flush=True)

    def predict(self, texts: list[str], top_k: int = 3) -> list[ClassifyResponse]:
        t0         = time.perf_counter()
        industry   = self.task1.predict(texts, top_k)
        subindustry = self.task2.predict(texts, top_k) if self.task2 else [None] * len(texts)
        latency    = round((time.perf_counter() - t0) * 1000 / len(texts), 1)

        return [
            ClassifyResponse(
                industry=industry[i],
                subindustry=subindustry[i],
                latency_ms=latency
            )
            for i in range(len(texts))
        ]


# ── App setup ─────────────────────────────────────────────────────────────────
app        = FastAPI(title="GECS Classifier", version="2.0",
                     description="Classifies company descriptions into Morningstar GECS codes.")
classifier = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status"          : "ok",
        "device"          : classifier.device,
        "task1_loaded"    : classifier.task1 is not None,
        "task2_loaded"    : classifier.task2 is not None,
        "task1_labels"    : classifier.task1.num_labels,
        "task2_labels"    : classifier.task2.num_labels if classifier.task2 else None,
    }


@app.get("/info")
def info():
    return {
        "model"          : "deberta-v3-small",
        "tasks"          : {
            "task1": {"description": "GECS Industry", "num_labels": classifier.task1.num_labels},
            "task2": {"description": "GECS Subindustry",
                      "num_labels": classifier.task2.num_labels if classifier.task2 else "not trained yet"},
        },
        "max_length"     : MAX_LEN,
        "device"         : classifier.device,
    }


@app.post("/classify", response_model=ClassifyResponse)
def classify(req: ClassifyRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text cannot be empty")
    return classifier.predict([req.text], top_k=req.top_k)[0]


@app.post("/classify/batch", response_model=BatchResponse)
def classify_batch(req: ClassifyBatchRequest):
    if not req.texts:
        raise HTTPException(status_code=400, detail="texts list cannot be empty")
    if len(req.texts) > 256:
        raise HTTPException(status_code=400, detail="Maximum 256 texts per batch")

    t0      = time.perf_counter()
    results = classifier.predict(req.texts, top_k=req.top_k)
    latency = round((time.perf_counter() - t0) * 1000, 1)

    return BatchResponse(results=results, total_latency_ms=latency)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    args = parser.parse_args()

    print("Starting GECS classifier server ...", flush=True)
    classifier = GECSClassifier()

    print(f"\nServer running at  http://{args.host}:{args.port}")
    print(f"Interactive docs   http://{args.host}:{args.port}/docs")
    print("Press Ctrl+C to stop.\n")

    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
