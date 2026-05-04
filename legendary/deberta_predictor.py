from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from legendary.shared import get_label, normalize_code


class DebertaPredictor:
    def __init__(
        self,
        model_path: str | Path = "llm_finetuning/results/task1_best_model",
        tokenizer_path: str | Path = "microsoft/deberta-v3-small",
        idx_map_path: str | Path = "llm_finetuning/data/task1_idx_to_code.json",
    ) -> None:
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_path = str(model_path)
        self.tokenizer_path = str(tokenizer_path)
        self.idx_map_path = Path(idx_map_path)
        self.ready = False
        self.error: str | None = None

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_path, local_files_only=True)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_path,
                local_files_only=True,
            )
            self.model.to(self.device)
            self.model.eval()
            self.idx_to_code = {
                int(k): normalize_code(v)
                for k, v in json.loads(self.idx_map_path.read_text(encoding="utf-8")).items()
            }
            self.ready = True
        except Exception as exc:
            self.error = str(exc)

    def predict(self, text: str, top_n: int = 3) -> dict[str, Any]:
        if not self.ready:
            raise RuntimeError(self.error or "DeBERTa model is not available")

        inputs = self.tokenizer(
            [text],
            truncation=True,
            padding="max_length",
            max_length=512,
            return_tensors="pt",
        )
        inputs = {key: value.to(self.device) for key, value in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits[0]
            probabilities = torch.softmax(logits, dim=-1)
            top_values, top_indices = torch.topk(probabilities, k=min(top_n, probabilities.shape[0]))

        best_index = int(top_indices[0].item())
        best_code = self.idx_to_code.get(best_index, "00000000")
        alternatives = []
        for rank, (probability, index) in enumerate(zip(top_values.tolist(), top_indices.tolist()), start=1):
            code = self.idx_to_code.get(int(index), "00000000")
            alternatives.append(
                {
                    "rank": rank,
                    "code": code,
                    "label": get_label(code),
                    "confidence": round(float(probability) * 100.0, 1),
                }
            )

        return {
            "engine": "DeBERTa",
            "mstar_code": best_code,
            "mstar_label": get_label(best_code),
            "confidence": round(float(top_values[0].item()) * 100.0, 1),
            "alternatives": alternatives,
        }
