"""Convert best_model_state.pt from float32 to float16 — halves file size."""
import torch
from pathlib import Path

src = Path("models_v3_modernbert/v3_minimal/best_model_state.pt")
dst = Path("hf_space_modernbert/models/best_model_state.pt")

print(f"Loading {src} ({src.stat().st_size/1e9:.2f} GB) ...")
sd = torch.load(str(src), map_location="cpu", weights_only=True)

print("Converting to float16 ...")
sd_fp16 = {k: v.half() if v.is_floating_point() else v for k, v in sd.items()}

print(f"Saving to {dst} ...")
torch.save(sd_fp16, str(dst))
print(f"Done — {dst.stat().st_size/1e9:.2f} GB")
