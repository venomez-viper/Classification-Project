"""
Inference script for the fine-tuned DeBERTa GECS classifier.

Loads the best checkpoint produced by train_local.py and runs predictions
on a single description, a list of descriptions, or a CSV file.

Works fully offline — no internet connection required.

Usage examples:
    # Single description
    python llm_finetuning/scripts/predict.py --task task1 --text "The company develops semiconductor chips for mobile devices."

    # Batch from CSV (must have a 'text' column or a column you specify)
    python llm_finetuning/scripts/predict.py --task task1 --csv path/to/file.csv --text_col description

    # Output to CSV
    python llm_finetuning/scripts/predict.py --task task1 --csv input.csv --output predictions.csv
"""

import argparse
import json
import os

os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"]  = "1"

import numpy as np
import pandas as pd
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT        = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR    = os.path.join(ROOT, "llm_finetuning", "data")
MODEL_DIR   = os.path.join(ROOT, "llm_finetuning", "models", "deberta-v3-small")
RESULTS_DIR = os.path.join(ROOT, "llm_finetuning", "results")

MAX_LEN     = 128
BATCH_SIZE  = 32   # inference batch — larger is fine, no gradient memory needed


# ── Utilities ─────────────────────────────────────────────────────────────────
def find_best_checkpoint(task: str) -> str:
    """Return the checkpoint directory marked as best in trainer_state.json."""
    ckpt_root = os.path.join(RESULTS_DIR, f"{task}_checkpoints")

    # First preference: trainer_state.json records the best checkpoint path
    for ckpt in sorted(os.listdir(ckpt_root), reverse=True):
        state_path = os.path.join(ckpt_root, ckpt, "trainer_state.json")
        if os.path.exists(state_path):
            with open(state_path) as f:
                state = json.load(f)
            best = state.get("best_model_checkpoint")
            if best and os.path.isdir(best):
                return best

    # Fallback: use the checkpoint with the highest step number
    checkpoints = [
        os.path.join(ckpt_root, d)
        for d in os.listdir(ckpt_root)
        if d.startswith("checkpoint-")
    ]
    if not checkpoints:
        raise FileNotFoundError(
            f"No checkpoints found in {ckpt_root}. "
            "Run train_local.py first."
        )
    return sorted(checkpoints, key=lambda p: int(p.split("-")[-1]))[-1]


# ── Classifier ────────────────────────────────────────────────────────────────
class GECSClassifier:
    """
    Wraps the fine-tuned DeBERTa model for easy inference.

    Parameters
    ----------
    task : str
        'task1' (industry) or 'task2' (subindustry)
    device : str
        'cuda' or 'cpu'. Auto-detected if not provided.
    """

    def __init__(self, task: str, device: str = None):
        self.task   = task
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        checkpoint = find_best_checkpoint(task)
        print(f"Loading checkpoint: {os.path.basename(checkpoint)}")

        with open(os.path.join(DATA_DIR, f"{task}_idx_to_code.json")) as f:
            raw = json.load(f)
        self.idx_to_code = {int(k): str(v) for k, v in raw.items()}
        self.num_labels  = len(self.idx_to_code)

        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, local_files_only=True)
        self.model     = AutoModelForSequenceClassification.from_pretrained(
            checkpoint,
            num_labels=self.num_labels,
            local_files_only=True,
            ignore_mismatched_sizes=True,
        )
        self.model.to(self.device)
        self.model.eval()
        print(f"Model ready on {self.device}. Labels: {self.num_labels}")

    def predict(self, texts: list[str], return_scores: bool = False) -> list[dict]:
        """
        Predict GECS codes for a list of descriptions.

        Parameters
        ----------
        texts : list of str
        return_scores : bool
            If True, include top-3 predictions with confidence scores.

        Returns
        -------
        list of dict with keys: text_snippet, predicted_code, confidence
        """
        results = []

        for start in range(0, len(texts), BATCH_SIZE):
            batch_texts = texts[start : start + BATCH_SIZE]
            inputs = self.tokenizer(
                batch_texts,
                truncation=True,
                padding="max_length",
                max_length=MAX_LEN,
                return_tensors="pt",
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                logits = self.model(**inputs).logits

            probs = torch.softmax(logits, dim=-1).cpu().numpy()

            for i, text in enumerate(batch_texts):
                top_idx   = int(np.argmax(probs[i]))
                top_score = float(probs[i][top_idx])

                result = {
                    "text_snippet"   : text[:120] + "..." if len(text) > 120 else text,
                    "predicted_code" : self.idx_to_code[top_idx],
                    "confidence"     : round(top_score * 100, 2),
                }

                if return_scores:
                    top3_idx = np.argsort(probs[i])[::-1][:3]
                    result["top3"] = [
                        {"code": self.idx_to_code[int(j)], "score": round(float(probs[i][j]) * 100, 2)}
                        for j in top3_idx
                    ]

                results.append(result)

        return results


# ── CLI ────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="GECS classifier inference")
    parser.add_argument("--task",     choices=["task1", "task2"], default="task1")
    parser.add_argument("--text",     type=str,  help="Single description to classify")
    parser.add_argument("--csv",      type=str,  help="Path to input CSV file")
    parser.add_argument("--text_col", type=str,  default="text", help="Column name for descriptions in CSV")
    parser.add_argument("--output",   type=str,  help="Path to save output CSV (batch mode only)")
    parser.add_argument("--top3",     action="store_true", help="Show top 3 predictions with scores")
    args = parser.parse_args()

    classifier = GECSClassifier(task=args.task)

    if args.text:
        results = classifier.predict([args.text], return_scores=args.top3)
        r = results[0]
        print(f"\nPredicted code : {r['predicted_code']}")
        print(f"Confidence     : {r['confidence']}%")
        if args.top3:
            print("Top 3 predictions:")
            for entry in r["top3"]:
                print(f"  {entry['code']}  {entry['score']}%")

    elif args.csv:
        df = pd.read_csv(args.csv)
        if args.text_col not in df.columns:
            raise ValueError(f"Column '{args.text_col}' not found. Available: {list(df.columns)}")

        print(f"Running predictions on {len(df)} rows ...")
        results = classifier.predict(df[args.text_col].fillna("").tolist(), return_scores=args.top3)

        df["predicted_code"] = [r["predicted_code"] for r in results]
        df["confidence"]     = [r["confidence"]     for r in results]

        if args.output:
            df.to_csv(args.output, index=False)
            print(f"Saved to {args.output}")
        else:
            print(df[["predicted_code", "confidence"]].head(20).to_string())

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
