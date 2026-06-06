"""
One-time model download script.

Downloads microsoft/deberta-v3-small weights into llm_finetuning/models/deberta-v3-small/
After this runs, the training script never needs an internet connection.

Usage:
    python llm_finetuning/scripts/download_model.py
"""

import os
from huggingface_hub import snapshot_download

ROOT      = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAVE_PATH = os.path.join(ROOT, "llm_finetuning", "models", "deberta-v3-small")
HF_ID     = "microsoft/deberta-v3-small"

os.makedirs(SAVE_PATH, exist_ok=True)

print(f"Downloading {HF_ID} ...")
print(f"Saving to   {SAVE_PATH}")
print("(One-time download of ~175 MB — safetensors format)")
print()

# snapshot_download pulls all files directly to disk without loading them —
# avoids any torch.load security restrictions entirely
snapshot_download(
    repo_id=HF_ID,
    local_dir=SAVE_PATH,
    ignore_patterns=["*.msgpack", "*.h5", "flax_model*", "tf_model*", "rust_model*"],
)

print()
print("Done. The training script will load from this local folder.")
print(f"Path: {SAVE_PATH}")
