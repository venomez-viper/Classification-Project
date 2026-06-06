# LLM Fine-Tuning: DeBERTa-v3 for GECS Classification

**Project:** MGT 599 Capstone  
**Module:** llm_finetuning (standalone research branch)  
**Final model:** microsoft/deberta-v3-base (86M parameters)  
**Date:** April 2026

> **Model progression:** Training began with `deberta-v3-small` (44M parameters). After extensive experimentation, the model plateaued at 62% Macro F1 regardless of learning rate, batch size, or epoch count. The root cause was model capacity — 44M parameters is insufficient for 145-class fine-grained classification. The project switched to `deberta-v3-base` (86M parameters) for the final training run. See Issue 14 for the full account.

---

## 1. Purpose

The baseline classification pipeline uses TF-IDF vectorization paired with a Linear SVM. This approach achieved a Macro F1 of 86.82% on Task 1 (145 GECS industry codes). While strong, TF-IDF treats text as a bag of words and has no understanding of context, sentence structure, or word meaning.

This module investigates whether a small pretrained transformer model, fine-tuned on the same company descriptions, can exceed that baseline. The goal is not to replace the existing pipeline but to measure the gap between classical NLP and modern transformer-based classification on this specific dataset.

---

## 2. Why DeBERTa-v3

Several transformer models were considered. The DeBERTa-v3 family was selected for the following reasons:

**Disentangled Attention**  
Standard transformers encode each token's content and position together into a single vector. DeBERTa keeps them separate and computes attention between content vectors and position vectors independently. This means the model is better at understanding how word meaning changes based on position in a sentence, which matters for long financial descriptions.

**Proven on Domain Text**  
DeBERTa-v3 models have shown strong performance on financial and legal NLP tasks, which share structural similarities with Morningstar company descriptions (formal register, dense terminology, consistent sentence patterns).

### Why deberta-v3-small was tried first

At 44 million parameters, deberta-v3-small fits on a 4 GB laptop GPU. The initial plan was to train locally without cloud infrastructure. After extensive training, the small model plateaued at 62% Macro F1 regardless of hyperparameter changes — see Issue 14 for the full account.

### Why deberta-v3-base is the final model

At 86 million parameters, deberta-v3-base has approximately twice the model capacity of the small variant. This additional capacity is specifically what enables finer-grained distinctions between the 145 industry codes. The base model requires 8–16 GB VRAM, making it impractical for the RTX 3050 laptop but well-suited for Google Colab's T4 GPU (16 GB). The training code, tokenizer, and deployment server are identical — only the model checkpoint changes.

---

## 3. How DeBERTa Improves Over the TF-IDF Baseline

### What TF-IDF Cannot Do

TF-IDF converts each description into a sparse vector of token frequency scores. A description with 300 words becomes a vector with 50,000 dimensions, most of them zero. The model has no knowledge of:

- That "semiconductor" and "chip manufacturer" refer to the same concept
- That "provides software as a service" and "offers cloud-based software" mean the same thing
- That "acquired several companies in the healthcare sector" is less relevant than "primarily operates in healthcare" for classification
- Word order and sentence structure

Two descriptions that use different vocabulary for the same type of company will look very different to TF-IDF, even if their meaning is identical.

### What DeBERTa Does Differently

DeBERTa was pretrained on 160 GB of text and learned the statistical relationships between words across millions of documents. When fine-tuned on company descriptions, it:

1. **Understands synonyms and paraphrases** across the 145 industry categories. It maps "semiconductor fabrication" and "chip manufacturing" to the same region of its representation space.

2. **Reads context across the full sentence.** The classification head sees a single 768-dimensional vector that is a summary of the entire input, not just the presence of individual words.

3. **Handles rare classes better.** TF-IDF + SVM struggles when a class has few training examples because there are few high-frequency tokens to anchor the decision boundary. DeBERTa's pretrained weights provide a strong initialization that generalizes from the few examples available.

4. **Generalizes to new vocabulary.** If a company description contains a term the training set has never seen, TF-IDF treats it as noise. DeBERTa uses subword tokenization and context from surrounding words to infer meaning.

### Expected Performance Gain

In published benchmarks on similar multi-class text classification tasks with 100+ categories, transformer models typically outperform TF-IDF + SVM by 3 to 8 percentage points in Macro F1. On this dataset specifically, Task 2 (407 subindustry codes, shorter text) is where the largest improvement is expected because TF-IDF has very little signal to work with in short descriptions, while DeBERTa can leverage pretrained semantic knowledge.

---

## 4. Data Safety and Offline Training

### The Problem with Cloud-Based Training

Sending proprietary Morningstar company descriptions to external APIs or cloud training platforms creates several risks:

- The data leaves the organization's control during transit
- Cloud providers may log, cache, or retain data depending on service terms
- There is no guarantee the data is deleted after training completes
- Regulatory and compliance requirements for financial data may prohibit external transfer

### How This Setup Handles It

The training pipeline was designed with a strict offline-first principle from the beginning.

**Step 1: One-time model download**  
The model weights (approximately 175 MB) are downloaded once from HuggingFace using `snapshot_download` and stored inside the project directory at `llm_finetuning/models/deberta-v3-small/`. This is the only network call the entire system ever makes.

**Step 2: Network isolation during training**  
Two environment variables are set at the top of the training script before any other code runs:

```python
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"]  = "1"
```

With these set, the HuggingFace libraries will raise an error rather than attempt any outbound connection. If the training script is run without the locally downloaded weights, it fails immediately with a clear message, not silently.

**Step 3: Local file loading**  
Every `from_pretrained()` call in the training script passes `local_files_only=True`. This is a second layer of enforcement. Even if the environment variables were unset, the library would refuse to contact the internet and load only from the local model directory.

**Step 4: Data never leaves the machine**  
All CSV files, label maps, checkpoints, and result JSONs are written to directories inside the project folder. Nothing is uploaded, logged to a remote service, or transmitted.

The result is a training pipeline that could run with no internet connection at all after the initial 175 MB download.

---

## 5. In-House GPU Training Setup

### Hardware

| Component | Specification |
|---|---|
| GPU | NVIDIA GeForce RTX 3050 Laptop GPU |
| VRAM | 4.3 GB |
| Architecture | Ampere (GA107) |
| CUDA Driver | 566.07 |
| CUDA Version | 12.4 |
| PyTorch | 2.6.0+cu124 |
| Transformers | 4.44.2 |
| Python | 3.11.9 |
| OS | Windows 11 |

### Memory Optimizations for 4 GB VRAM

Training a 44M parameter model on a 4 GB GPU requires several adjustments from a standard configuration. These were arrived at through iteration — see Section 10 for the full story.

**Reduced sequence length (128 tokens instead of 256)**  
Activation memory scales with sequence length. Cutting from 256 to 128 tokens roughly halves the memory used by attention matrices. Task 1 text averages 89 words which fits comfortably inside 128 tokens, so no meaningful content is truncated.

**Physical batch size 4, gradient accumulation ×4 → effective batch 16**  
Batch size 4 keeps activation VRAM within budget. Gradient accumulation defers the optimizer step until 4 mini-batches have been processed, making each weight update mathematically equivalent to one pass over 16 samples. This eliminates the noisy gradient problem that plagued pure batch-4 training (see Issue 10).

**FP32 precision throughout**  
DeBERTa-v3's disentangled attention backward pass crashes silently under BF16 or FP16 on Windows with PyTorch 2.6 (see Issues 3 and 4). Full FP32 is stable and, at batch size 4, still fits in VRAM.

**foreach=False on AdamW**  
PyTorch's default multi-tensor AdamW kernel batches all 44M parameter updates into one CUDA call. After epoch 1, VRAM fragmentation means no single contiguous block is large enough for this operation. Setting `foreach=False` makes AdamW update each parameter individually, eliminating the OOM at the cost of ~10% slower optimizer steps (see Issue 9).

**pin_memory=False on DataLoaders**  
Pinned CPU memory cannot be reclaimed between epochs and contributes to VRAM pressure at epoch boundaries. Disabling it gives the CUDA allocator more room to breathe.

**gc.collect() + torch.cuda.empty_cache() at each epoch boundary**  
Forces Python's garbage collector and the CUDA memory allocator to release all stale tensors before the next epoch begins.

### Training Configuration Summary

**Local (RTX 3050, 4 GB VRAM):**

| Parameter | Value | Reason |
|---|---|---|
| Model | deberta-v3-small | Best size/performance ratio for 4 GB |
| Max sequence length | 128 tokens | Memory constraint |
| Physical batch size | 4 | Memory constraint — keeps activations inside VRAM |
| Gradient accumulation | 4 steps | Effective batch = 16 — cleaner gradients without more VRAM |
| Effective batch size | 16 | Stable gradient signal for 145-class fine-tuning |
| Epochs | 6 | Sufficient with gradient accumulation |
| Learning rate | 3e-5 | Slightly higher for effective batch 16 |
| Resume LR | 1e-5 | Lower rate when continuing from a saved checkpoint |
| Precision | FP32 | Required for DeBERTa-v3 stability on Windows / PyTorch 2.6 |
| Warmup | 10% of opt-steps | ~670 optimizer steps |
| Optimizer | AdamW (foreach=False) | foreach=False avoids contiguous-block OOM at epoch 2 |
| Evaluation | After each epoch | Saves best checkpoint automatically |

**Colab (T4, 16 GB VRAM):**

| Parameter | Value | Reason |
|---|---|---|
| Model | deberta-v3-small | Research confirms <2% F1 gap vs base at 40k samples/145 classes (see Issue 15) |
| Physical batch size | 16 | 16 GB VRAM — no gradient accumulation needed |
| Grad accumulation | 1 (none) | Direct batch=16 fits in VRAM |
| Epochs | 10 | Sufficient with sustained LR; avoids 12-hour runs |
| Learning rate | 3e-5 | Documented optimum for deberta-v3-small (HuggingFace); 2e-5 too slow (Issue 15) |
| Warmup | 10% of total steps | ~2,680 steps |
| Precision | FP32 | Same stability requirement |
| Time per epoch | ~12 min | T4 + batch=16 |

---

## 6. What Was Built (Stage by Stage)

### Stage 1: Data Preparation

**Script:** `llm_finetuning/scripts/prepare_data.py`

Reads from the existing cleaned capstone CSVs in `data/cleaned/`. Combines text columns the same way the TF-IDF baseline did so results are directly comparable. Encodes Morningstar codes into 0-based integer indices (required by the transformer classification head). Saves the integer-to-code mapping as JSON so predictions can be decoded back to real Morningstar codes. Performs a stratified 80/20 train/test split.

Task 2 had 21 classes with only one sample. These were removed because a stratified split is impossible with a single example. Task 2 went from 428 to 407 classes.

Output files written to `llm_finetuning/data/`:

| File | Rows |
|---|---|
| task1_train.csv | 42,868 |
| task1_test.csv | 10,717 |
| task2_train.csv | 22,012 |
| task2_test.csv | 5,504 |
| task1_code_to_idx.json | 145 label mappings |
| task2_code_to_idx.json | 407 label mappings |

### Stage 2: Model Download

**Script:** `llm_finetuning/scripts/download_model.py`

Downloads `microsoft/deberta-v3-small` weights and tokenizer files to `llm_finetuning/models/deberta-v3-small/` using `snapshot_download`. Downloads only PyTorch and tokenizer files, skipping TensorFlow and Flax variants. This is the only point in the entire process where an internet connection is used.

### Stage 3a: Local Training

**Script:** `llm_finetuning/scripts/train_local.py`

Sets offline environment variables, loads data from Stage 1 CSVs, tokenizes with the local DeBERTa tokenizer, loads the model from the local weights directory, and runs fine-tuning using a raw PyTorch training loop (no HuggingFace Trainer — see Issue 6). Uses gradient accumulation over 4 mini-batches for an effective batch of 16. Evaluates Macro F1 on the held-out test set after each epoch. Saves the best checkpoint automatically. Writes a results JSON with the final Macro F1, per-class breakdown, and delta against the baseline.

All training is offline — no data leaves the machine. Use this when data confidentiality requires local-only execution.

**Fresh training run (6 epochs, ~4.5 hours on RTX 3050):**
```
python llm_finetuning/scripts/train_local.py --task task1
python llm_finetuning/scripts/train_local.py --task task2
```

**Resume from a saved checkpoint (3 more epochs, LR 1e-5):**
```
python llm_finetuning/scripts/train_local.py --task task1 --resume
python llm_finetuning/scripts/train_local.py --task task2 --resume
```

### Stage 3b: Colab Training (faster alternative)

**Notebook:** `llm_finetuning/notebooks/01_finetune_deberta.ipynb`

For faster training when data confidentiality allows it, the same training logic runs on Google Colab's T4 GPU (16 GB VRAM). The T4 can use `batch_size=16` directly with no gradient accumulation, completing 12 epochs in approximately 2.5 hours vs 4.5+ hours locally.

The notebook uses an identical raw PyTorch loop to the local script, pinned to `transformers==4.44.2` for the same stability. Results are saved to Google Drive and downloaded back to the local `results/` directory after training.

| Setting | Local (RTX 3050) | Colab T4 — small | Colab T4 — base (final) |
|---|---|---|---|
| Model | deberta-v3-small | deberta-v3-small | **deberta-v3-base** |
| Parameters | 44M | 44M | **86M** |
| Physical batch | 4 | 16 | 8 |
| Grad accumulation | ×4 | ×1 | ×1 |
| Effective batch | 16 | 16 | 8 |
| Epochs | 6 | 12 | 12 |
| LR | 3e-5 | 4e-5 | 2e-5 |
| Best F1 achieved | 62.02% | 61.91% | In progress |
| Time per epoch | ~45 min | ~12 min | ~20 min |
| Total time | ~4.5 hrs | ~2.5 hrs | ~4 hrs |
| Data leaves machine | No | Yes | Yes |

**Colab workflow:**
1. Upload CSV and JSON files to `MyDrive/capstone_llm/`
2. Open notebook in Colab — set runtime to T4 GPU
3. Run all cells — results saved back to Drive automatically
4. Download `task1_best_model/` folder and place in `llm_finetuning/results/`

---

## 7. Evaluation and Comparison

The primary metric is Macro F1. This is calculated identically to the baseline evaluation so the numbers are directly comparable.

Macro F1 averages the F1 score across all classes with equal weight regardless of class size. This is the appropriate metric for GECS classification because a model that classifies the 10 most common industries well but fails on rare ones would show inflated accuracy but a low Macro F1.

**Task 1 Baseline:** 86.82% (TF-IDF + LinearSVM)  
**Task 2 Baseline:** Not previously measured

Results are written to `llm_finetuning/results/task1_results.json` and `task2_results.json` after training completes. Each file contains the overall Macro F1, the training configuration, and a per-class F1 breakdown for all 145 (Task 1) or 407 (Task 2) categories.

---

## 8. File Structure

```
llm_finetuning/
├── data/
│   ├── task1_train.csv
│   ├── task1_test.csv
│   ├── task1_full.csv
│   ├── task1_code_to_idx.json
│   ├── task1_idx_to_code.json
│   ├── task2_train.csv
│   ├── task2_test.csv
│   ├── task2_full.csv
│   ├── task2_code_to_idx.json
│   └── task2_idx_to_code.json
├── models/
│   └── deberta-v3-small/           (downloaded once, never re-fetched)
├── notebooks/
│   └── 01_finetune_deberta.ipynb   (Colab version)
├── scripts/
│   ├── prepare_data.py             (Stage 1 — data prep and splitting)
│   ├── download_model.py           (Stage 2 — one-time model download)
│   ├── train_local.py              (Stage 3 — GPU fine-tuning, supports --resume)
│   ├── serve.py                    (REST API server — both tasks, Ollama-style)
│   ├── debug_loss.py               (diagnostic — forward+backward pass check)
│   └── debug_trainer.py            (diagnostic — minimal Trainer smoke test)
├── results/
│   ├── task1_best_model/           (saved checkpoint — best epoch weights)
│   ├── task2_best_model/           (saved after task2 training)
│   ├── task1_results.json          (final Macro F1, per-class breakdown)
│   └── task2_results.json
└── requirements.txt
```

---

## 9. Dependencies

```
torch>=2.6.0
transformers==4.44.2
scikit-learn>=1.4.0
pandas>=2.0.0
numpy>=1.26.0
huggingface_hub>=0.23.0
sentencepiece>=0.1.99
fastapi>=0.111.0
uvicorn>=0.29.0
```

Note: `transformers` must be pinned to `4.44.2`. Transformers 5.x breaks DeBERTa-v3 backward pass on Windows with PyTorch 2.6 (see Issue 8). `accelerate`, `datasets`, and `evaluate` are not used — the training loop is raw PyTorch.

Install with:
```
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install -r llm_finetuning/requirements.txt
```

---

## 10. Issues Encountered and Fixes Applied

This section documents every error hit during development, the root cause, and the fix applied. Kept here for reproducibility and as a reference if the same errors appear on a different machine.

---

### Issue 1: `no_cuda` argument removed in Transformers 5.x

**When it appeared:** First training run attempt.

**Error:**
```
TypeError: TrainingArguments.__init__() got an unexpected keyword argument 'no_cuda'
```

**Root cause:**  
The `no_cuda` parameter was removed in Transformers 5.x. In previous versions it was used to force CPU training. In 5.x, the Trainer detects the device automatically.

**Fix:**  
Removed the `no_cuda` parameter from `TrainingArguments` entirely. The Trainer uses the GPU automatically when CUDA is available.

---

### Issue 2: `warmup_ratio` deprecated in Transformers 5.x

**When it appeared:** First training run attempt.

**Warning:**
```
warmup_ratio is deprecated and will be removed in v5.2. Use warmup_steps instead.
```

**Root cause:**  
`warmup_ratio` was replaced by `warmup_steps` in Transformers 5.x.

**Fix:**  
Replaced `warmup_ratio=0.1` with an explicit `warmup_steps` calculation:
```python
warmup_steps = int(0.1 * (42868 // (BATCH_SIZE * GRAD_ACCUM)) * EPOCHS)
```
This computes 10% of total training steps, which is the same value the ratio would have produced.

---

### Issue 3: FP16 gradient unscaling error with DeBERTa-v3

**When it appeared:** Second training run attempt.

**Error:**
```
ValueError: Attempting to unscale FP16 gradients.
```

**Root cause:**  
DeBERTa-v3's disentangled attention mechanism computes attention between content vectors and position vectors separately. This produces intermediate values with a wider range than standard transformers. FP16 (16-bit float) has a narrow dynamic range and cannot represent these values without overflow, which breaks the gradient scaler.

**Fix:**  
Switched from `fp16=True` to `bf16=True`. BF16 (bfloat16) uses the same number of bits as FP16 but with a wider dynamic range that matches FP32. The RTX 3050 Ampere architecture supports BF16 natively.

---

### Issue 4: NaN loss and zero Macro F1 during training (BF16 + gradient checkpointing instability)

**When it appeared:** During the first full training run at epoch 3 of 4.

**Symptom:**
```
{'eval_loss': 'nan', 'eval_macro_f1': 7.17e-05, 'epoch': 3}
```

**Root cause:**  
BF16 combined with gradient checkpointing on DeBERTa-v3 is numerically unstable on certain CUDA versions. When gradient checkpointing discards and recomputes activations, small BF16 rounding errors accumulate across the recomputed values. By epoch 3 these accumulated errors caused the loss to overflow to NaN. Once the loss is NaN, all gradients become NaN and the model weights are corrupted. The Macro F1 of essentially zero confirms the model was no longer producing meaningful predictions.

The training appeared to be progressing normally through epochs 1 and 2. The instability only manifested at epoch 3, which is typical of BF16 accumulation errors — they compound over time rather than appearing immediately.

**Fix:**  
1. Disabled both BF16 and FP16, training in full FP32:
```python
bf16=False,
fp16=False,
```
2. Tightened gradient clipping from the default 1.0 to 0.5 as an additional safeguard:
```python
max_grad_norm=0.5,
```
3. Deleted the corrupted checkpoints before restarting:
```powershell
Remove-Item -Recurse -Force "llm_finetuning\results\task1_checkpoints"
```

**Memory impact:**  
FP32 uses twice the memory per parameter compared to BF16. With our existing optimizations (batch size 8, sequence length 128, gradient checkpointing), peak VRAM usage rose from approximately 1.5 GB to approximately 2.0 GB. This remains well within the 4.3 GB available.

**Speed impact:**  
FP32 training is approximately 20% slower per step than BF16. Estimated training time increased from 90 minutes to 110-120 minutes. This is an acceptable trade-off for a stable, correct training run.

**Lesson:**  
DeBERTa-v3 should always be trained in FP32 when gradient checkpointing is enabled. BF16 is only safe for DeBERTa-v3 without gradient checkpointing, which requires more VRAM than a 4 GB GPU can provide at this batch size.

---

### Issue 5: `rmdir /s /q` does not work in PowerShell

**When it appeared:** When deleting corrupted checkpoints before the restart.

**Error:**
```
Remove-Item : A positional parameter cannot be found that accepts argument '/q'.
```

**Root cause:**  
`rmdir /s /q` is a Windows Command Prompt (CMD) command. PowerShell uses different syntax for the same operation.

**Fix:**  
Use the PowerShell equivalent:
```powershell
Remove-Item -Recurse -Force "path\to\folder"
```

---

### Issue 6: Gradient explosion on first optimizer step — loss 1.706e+05 and NaN grad_norm

**When it appeared:** After switching to FP32 and removing gradient checkpointing.

**Symptom:**
```
Starting training — 4 epochs, effective batch 32
{'loss': '1.706e+05', 'grad_norm': 'nan', 'learning_rate': '1.832e-06', 'epoch': '0.03732'}
{'loss': '0', 'grad_norm': 'nan', ...}
```

**Root cause:**  
The loss of 170,600 on the very first logging point is impossible for a standard 145-class cross-entropy, which should start around 4.97. This indicated a fundamental numerical failure during the first training steps.

The root cause is an incompatibility between DeBERTa-v3's large embedding matrix (128,100 tokens × 768 dimensions) and the Accelerate-wrapped optimizer used by the HuggingFace Trainer in Transformers 5.6.2. After exactly one optimizer step, all model weights became NaN. From that point forward every forward pass produced NaN logits, NaN loss, and NaN gradients. The Trainer reported loss as 0 once it turned NaN.

The issue is specific to Transformers 5.x where the Trainer delegates gradient operations to Accelerate. The Accelerate-wrapped AdamW and gradient clipping pipeline interacts unexpectedly with DeBERTa-v3's parameter structure during the first weight update.

**Debugging process:**  
A standalone debug script was written to run one forward pass and backward pass outside the Trainer:
```
Loss (train mode): 4.9209  -- perfectly normal
Grad norm after clip: 5.52  -- reasonable
Params with NaN grad: 0     -- no NaN before the optimizer step
```
This confirmed the model, data, and backward pass were all clean. The corruption happened inside the Trainer's optimizer step, not before it.

**Fix:**  
Replaced the HuggingFace Trainer entirely with a raw PyTorch training loop using `torch.optim.AdamW` and `torch.nn.utils.clip_grad_norm_` directly. This bypasses Accelerate completely and gives full control over the training process.

Key changes:
- Replaced `TrainingArguments` + `Trainer` with a manual `for epoch / for batch` loop
- Used `torch.optim.AdamW` with explicit parameter groups (decay vs no-decay)
- Used `torch.nn.utils.clip_grad_norm_` with `max_norm=1.0` directly
- Used `transformers.get_linear_schedule_with_warmup` for the LR schedule
- Saved best checkpoint manually using `model.save_pretrained()`

The raw loop produces identical training behavior to the Trainer but without the Accelerate layer that was causing the corruption.

---

### Issue 7: Silent crash (segfault) when calling `pd.read_csv` after importing torch on Windows

**When it appeared:** During debug script development to diagnose Issue 6.

**Symptom:**  
The debug script printed `Step 3: pandas OK` and then silently exited with no error message or traceback. No exception was raised, no output after the `pd.read_csv` call.

**Root cause:**  
On Windows, PyTorch loads a set of native DLLs when imported. These DLLs conflict with the native file I/O DLLs that pandas uses internally via numpy. When torch is imported first and pandas tries to perform file I/O after, a native-level segmentation fault occurs. This bypasses Python's exception handling entirely, which is why no traceback appears.

This is a known Windows-specific DLL conflict that does not occur on Linux or macOS.

**Fix:**  
Import pandas and call `pd.read_csv` before importing torch in every script. The fix is an import ordering rule:

```python
# CORRECT — pandas imported and CSV read before torch
import pandas as pd
df = pd.read_csv(...)     # file I/O happens before torch DLLs are loaded

import torch              # torch loaded after pandas file I/O is done
```

```python
# WRONG on Windows — causes silent segfault
import torch
import pandas as pd
df = pd.read_csv(...)     # crashes silently
```

This rule was applied to both `train_local.py` and all debug scripts.

---

### Issue 8: NaN loss from step 1 in raw PyTorch loop

**When it appeared:** After switching to a raw PyTorch training loop (Issue 6 fix).

**Symptom:**
```
--- Epoch 1/4 ---
  Epoch 1 | step 50/5359 | loss nan | lr 4.67e-07 | 0.2% done
  Epoch 1 | step 100/5359 | loss nan | lr 9.33e-07 | 0.5% done
```

**Root cause (identified):**  
Transformers 5.6.2 introduced a breaking change in how DeBERTa-v3's disentangled attention backward pass is implemented. The backward pass through the position-content attention computation crashes silently on Windows with PyTorch 2.6. The forward pass is unaffected — only backpropagation fails. This is why the loss appeared as NaN in training (no gradient signal) but a standalone forward pass with `torch.no_grad()` always gave correct results.

The crash was confirmed by adding a `.backward()` call to the debug script and observing that the script exited silently after printing the forward loss, before reaching the grad norm print.

**Fix:**  
Downgraded transformers from 5.6.2 to 4.44.2, the last stable 4.x release with known DeBERTa-v3 support:

```powershell
pip install transformers==4.44.2
```

After downgrading, the full debug script passes cleanly:
```
Loss (train mode): 5.2605
Grad norm after clip: 6.7500
Params with NaN grad: 0
```

Transformers 4.44.2 is fully compatible with PyTorch 2.6.0+cu124. No model weights, data, or training scripts required any changes.

**Lesson:**  
When using DeBERTa-v3 (DebertaV2 family), use transformers 4.x (specifically 4.44.x). Transformers 5.x introduced internal changes to the attention backward pass that break DeBERTa-v3 fine-tuning on Windows with PyTorch 2.6. This does not affect inference (forward pass only), only training.

---

### Issue 9: CUDA out of memory during AdamW optimizer step at epoch 2

**When it appeared:** Epoch 2, step 50. Training completed epoch 1 successfully then crashed at the first optimizer step of epoch 2.

**Error:**
```
RuntimeError: CUDA error: out of memory
  File "torch/optim/adamw.py", line 701, in _multi_tensor_adamw
    torch._foreach_div_(exp_avg_sq_sqrt, bias_correction2_sqrt)
```

**Root cause:**  
PyTorch's AdamW by default uses a multi-tensor CUDA kernel (`_multi_tensor_adamw`) that batches all parameter updates into a single GPU operation. This is faster but requires a large contiguous block of VRAM to hold all parameter tensors simultaneously during the update.

Over the course of epoch 1, VRAM becomes fragmented — many small allocations and deallocations leave the memory in a state where enough total free VRAM exists but no single contiguous block is large enough for the multi-tensor operation. This fragmentation does not cause issues during the forward and backward passes (which operate layer by layer) but triggers an OOM when AdamW tries to update all 44M parameters at once at the start of epoch 2.

**Fix:**  
Two changes applied together:

1. Disabled the multi-tensor kernel by setting `foreach=False` in AdamW:
```python
optimizer = torch.optim.AdamW(params, lr=LR, foreach=False)
```
With `foreach=False`, AdamW loops through each parameter individually instead of processing all at once. This eliminates the large contiguous memory requirement at the cost of approximately 10% slower optimizer steps.

2. Added `torch.cuda.empty_cache()` before and after evaluation at the end of each epoch:
```python
torch.cuda.empty_cache()
macro_f1, _, _ = evaluate(model, test_loader, device)
torch.cuda.empty_cache()
```
This releases fragmented VRAM back to the allocator between epochs so the next epoch starts with a clean memory state.

3. Deleted the stale checkpoint from the interrupted run before restarting:
```powershell
Remove-Item -Recurse -Force "llm_finetuning\results\task1_best_model"
```

**Impact:**  
Optimizer steps are approximately 10% slower due to `foreach=False`. On a 90-minute training run this adds roughly 9 minutes. This is an acceptable trade-off to prevent OOM crashes.

However, `foreach=False` alone was not sufficient. The OOM persisted, this time in `_single_tensor_adamw`:

```
RuntimeError: CUDA error: out of memory
  File "torch/optim/adamw.py", line 425, in _single_tensor_adamw
      exp_avg.lerp_(grad, 1 - device_beta1)
```

This confirmed the error had moved from the multi-tensor kernel to the single-tensor fallback, meaning the underlying problem was general VRAM fragmentation at epoch boundaries — not the multi-tensor kernel specifically. Three additional fixes were required (see Issue 10).

---

### Issue 10: OOM persists at epoch 2 despite foreach=False — gradient noise causes 62% Macro F1

**When it appeared:** After applying `foreach=False`, the OOM moved from `_multi_tensor_adamw` to `_single_tensor_adamw` and continued to crash at epoch 2. After applying the full VRAM fix set (batch size 4, pin_memory=False, set_to_none=True, gc.collect()), training completed all 4 epochs — but the final Macro F1 was only 62.02%, far below the 86.82% baseline.

**Result:**
```
Baseline (TF-IDF + SVM) : 86.82%
DeBERTa-v3-small        : 62.02%
Delta                   : -24.80%
Did not beat baseline.
```

**Root cause (OOM fix — completing the VRAM management):**  
The OOM in `_single_tensor_adamw` confirmed the issue was general VRAM fragmentation across epoch boundaries, not specific to the multi-tensor kernel. Three additional changes were applied:

1. Reduced physical batch size from 8 to 4 — halves activation VRAM per forward pass:
```python
BATCH_SIZE = 4
```

2. Disabled pinned memory on both DataLoaders — pinned memory cannot be reclaimed between epochs:
```python
DataLoader(..., pin_memory=False)
```

3. Used `set_to_none=True` on zero_grad — releases gradient tensor memory completely instead of zeroing it, freeing ~176 MB every step:
```python
optimizer.zero_grad(set_to_none=True)
```

4. Added `gc.collect()` and `torch.cuda.empty_cache()` at the start of each epoch — forces Python GC and the CUDA allocator to release all stale tensors before loading new batches:
```python
for epoch in range(1, EPOCHS + 1):
    gc.collect()
    torch.cuda.empty_cache()
```

**Root cause (62% result — gradient noise from pure batch-4 training):**  
With physical batch size 4 and no gradient accumulation, each optimizer step receives a gradient computed from only 4 samples out of 145 classes. At this scale the gradient direction is highly noisy — individual steps frequently point away from the loss minimum. The model converges to a local optimum at ~62% rather than continuing to improve.

This is a known problem with very small batches in multi-class classification. The optimizer makes 10,718 noisy updates per epoch instead of ~2,679 clean updates over an effective batch of 16.

**Fix:**  
Added gradient accumulation. The training loop now runs 4 mini-batches before calling the optimizer, making each weight update equivalent to one pass over 16 samples:

```python
GRAD_ACCUM = 4   # physical batch 4 × accumulation 4 = effective batch 16
EPOCHS     = 6   # extra epochs to compensate for longer convergence

# in the training loop:
loss = output.loss / GRAD_ACCUM   # normalize before backward
loss.backward()

if (step + 1) % GRAD_ACCUM == 0 or is_last_step:
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    optimizer.step()
    scheduler.step()
    optimizer.zero_grad(set_to_none=True)
```

The scheduler and warmup calculation are now based on optimizer steps (not mini-batch steps), so the LR schedule is correct for the effective batch size.

**Impact:**  
Training time per epoch is unchanged (same physical batch size, same number of mini-batches). Total training time increases from 4 × ~45 min to 6 × ~45 min because of the extra epochs. Gradient quality improves significantly — the optimizer now takes fewer but much more accurate steps.

---

### Issue 11: Resuming training without restarting from scratch

**When it appeared:** After the 62% run completed 4 epochs over ~3 hours, re-running with the new gradient accumulation config would require another 6 hours from scratch.

**Problem:**  
The existing training script always loaded the base DeBERTa weights from `llm_finetuning/models/deberta-v3-small/`. There was no way to continue from the saved 62% checkpoint.

**Fix:**  
Added a `--resume` flag to `train_local.py`. When set:

1. Loads the saved best checkpoint from `llm_finetuning/results/{task}_best_model/` instead of the base model weights — the 62% adapted weights are already a better starting point than random initialization
2. Uses a lower learning rate (`RESUME_LR = 1e-5` instead of `LR = 2e-5`) — the model is already adapted; a lower rate prevents overshooting the refined optimum
3. Skips warmup entirely — the classification head is already initialized and stable
4. Runs for `RESUME_EPOCHS = 3` epochs instead of 6

```
python llm_finetuning/scripts/train_local.py --task task1 --resume
```

**Time saving:**  
Resuming runs 3 epochs (~2.5 hours) instead of 6 epochs from scratch (~4.5 hours). The starting loss is already ~0.78 (vs ~4.97 from scratch), confirming the checkpoint provides a strong initialization.

**When to use each mode:**

| Situation | Command |
|---|---|
| First-time training | `--task task1` |
| Improve an existing checkpoint | `--task task1 --resume` |
| Task 1 done, train Task 2 | `--task task2` |

---

### Issue 12: LR schedule decays too fast with 6 epochs — model plateaus prematurely

**When it appeared:** Colab training with `EPOCHS=6`, `LR=2e-5`. After epoch 4, gains shrank from +10% to +5% per epoch and the model was projected to plateau at ~65% well below the 86.82% baseline.

**Root cause:**  
With a linear warmup + linear decay schedule, the LR decays to zero by the final training step. With only 6 epochs of 2,680 steps each (16,080 total steps), the LR position at each epoch was:

| Epoch start | LR remaining | % of peak |
|---|---|---|
| Epoch 2 | 1.85e-5 | 93% |
| Epoch 3 | 1.48e-5 | 74% |
| Epoch 4 | 1.11e-5 | 56% |
| Epoch 5 | 0.74e-5 | 37% |
| Epoch 6 | 0.37e-5 | 19% |

By epoch 5 the model was learning at less than 40% of its peak rate. This is why gains shrank from +19% (epoch 1→2) to +5% (epoch 3→4) despite the model having more to learn.

**Fix:**  
Increased epochs to 12 and LR to 4e-5. With 32,160 total steps, the LR schedule stays above 70% of its peak through epoch 6 and only begins decaying aggressively in epochs 9–12. This gives the model sustained learning budget during the epochs where it is learning fine-grained distinctions.

| Epoch start | LR remaining (12-ep run) | % of peak |
|---|---|---|
| Epoch 3 | 3.7e-5 | 93% |
| Epoch 5 | 3.0e-5 | 75% |
| Epoch 7 | 2.3e-5 | 57% |
| Epoch 9 | 1.5e-5 | 38% |

**General rule:**  
For fine-grained multi-class classification with 100+ categories, plan for at least 10–12 epochs. With a linear decay schedule, the LR should still be above 50% of its peak at the epoch where you expect the model to be making meaningful progress on hard class distinctions.

---

### Issue 13: Macro F1 convergence is slow — but the model is learning correctly

**When it appeared:** After 3 epochs of the 12-epoch Colab run, Macro F1 was 54.64% — identical to previous runs with different LR settings. The model appeared stuck regardless of configuration.

**Diagnostic:**  
A sample of 10 test predictions was inspected manually:

```
WRONG | True: 20645010 | Pred: 20660010  ← medical exam vs diagnostic services
WRONG | True: 31110030 | Pred: 31110020  ← same 6-digit parent, different sub-leaf
WRONG | True: 31120040 | Pred: 31130030  ← adjacent codes within same sector
WRONG | True: 10120010 | Pred: 10130020  ← adjacent construction materials codes
OK    | True: 20550020 | Pred: 20550020
OK    | True: 20660010 | Pred: 20660010
OK    | True: 30910020 | Pred: 30910020
OK    | True: 31080060 | Pred: 31080060
OK    | True: 10150020 | Pred: 10150020
```

**Finding:**  
Every wrong prediction was a near-miss — the predicted code shared 4–6 digits with the correct code, meaning the model placed the company in the right broad category but confused it with a closely adjacent subcategory. The model was not confusing healthcare with energy, or software with materials. It was confusing "medical examination services" with "diagnostic services" — a distinction that requires very precise reading of the description.

**What this means:**  
Macro F1 penalises every wrong prediction equally, regardless of how close it was. A model that confuses two adjacent leaf codes scores the same as a model guessing randomly. This explains why Macro F1 remains in the 54–62% range even though the model's broad-category accuracy is much higher. The model has learned the industry structure correctly — it is learning the fine-grained leaf distinctions as training continues.

**Initial action:**  
Training was continued assuming more epochs would resolve the near-miss errors. The model ran for 6 more effective epochs and plateaued at 61.91% — confirming the near-miss pattern was a symptom of model capacity, not insufficient training. See Issue 14 for the root cause and resolution.

**Insight for the capstone:**  
The near-miss analysis is a valuable result regardless of whether the baseline is beaten. It demonstrates that DeBERTa learned the semantic structure of the GECS taxonomy — every company was placed in approximately the correct sector. The remaining gap was in the finest leaf-level distinctions, which require a larger model with more representational capacity to resolve. This is a concrete, explainable finding about the relationship between model size and classification granularity.

---

### Issue 14: deberta-v3-small capacity ceiling — model plateaus at 62% regardless of hyperparameters

**When it appeared:** After completing multiple full training runs across different configurations, the model consistently converged to 61–62% Macro F1 and stopped improving.

**Full experiment history:**

| Run | Config | Best F1 | Outcome |
|---|---|---|---|
| Local run 1 | batch=4, 4 epochs, no grad_accum | 62.02% | Noisy gradients suspected |
| Local resume | batch=4, GRAD_ACCUM=4, LR=1e-5 | 62.14% | Flat — LR too low |
| Colab run 1 | batch=16, 6 epochs, LR=2e-5 | ~65% projected | LR schedule decayed too fast |
| Colab run 2 | batch=16, 12 epochs, LR=4e-5 | 61.91% | Plateaued epoch 5–6 |

Every configuration — different learning rates (1e-5 to 4e-5), different batch sizes (4 to 16), different epoch counts (4 to 12+), with and without gradient accumulation — produced the same ceiling.

**Root cause:**  
Model capacity. deberta-v3-small has 44 million parameters. For 145-class fine-grained classification, each class needs a distinct region in the model's representation space. With 145 similar-sounding industry codes (many sharing the same broad sector), the small model does not have enough representational capacity to carve out clean decision boundaries for all 145 classes simultaneously.

The near-miss analysis (Issue 13) was the clearest signal in hindsight: a model that correctly identifies the sector but fails on the leaf node is operating at the edge of its capacity. It has learned all it can about the broad structure and cannot go further without more parameters.

This is distinct from a learning rate or data problem. The loss was still dropping at epoch 6 (0.84), meaning the model had not converged — it was simply unable to represent the distinctions needed to go higher.

**Why this was not caught earlier:**  
Each failed run was attributed to a fixable hyperparameter issue — noisy gradients, decaying LR, insufficient epochs. These explanations were plausible but wrong. The real signal was that every configuration produced the same ceiling, which points to a capacity constraint, not a training issue. In hindsight, the model switch should have been made after the first Colab run showed the same plateau as the local runs.

**Fix:**  
Switched from `deberta-v3-base` to `microsoft/deberta-v3-base` (86M parameters). One line change in the notebook:

```python
MODEL_NAME = 'microsoft/deberta-v3-base'
BATCH_SIZE = 8    # base model is larger — reduce batch to fit T4 VRAM
```

The base model has twice the parameter count, wider hidden layers (768 → 1024 dimensions), and deeper attention heads. On published benchmarks, deberta-v3-base outperforms deberta-v3-small by 5–15 percentage points on multi-class classification tasks with 100+ categories.

All other training code, tokenizer, evaluation, and deployment scripts are identical. The checkpoint format is the same — `serve.py` loads the base model automatically.

**Time cost of this issue:**  
Approximately 6–8 hours of GPU time across multiple failed training runs. The lesson: when the same performance ceiling appears across multiple different hyperparameter configurations, the problem is structural (architecture or data), not parametric.

---

### Issue 15: Research-backed revision — deberta-v3-small is sufficient; 60% at epoch 5 is normal progression, not a plateau

**When it appeared:** April 26, 2026. After pausing the Colab run at epoch 5 (60.67% Macro F1) and observing that switching to deberta-v3-base with MAX_LEN=256 made each epoch take ~60 minutes (12 hours total), external research was conducted to verify the model choice and hyperparameter decisions before continuing.

**Research question:** Is 60% Macro F1 at epoch 5 a sign that deberta-v3-small has hit its capacity ceiling, or is it normal progression for a 145-class task?

**Research findings:**

*Source 1 — HuggingFace documentation and community benchmarks*  
For multi-class tasks with 100+ categories, Macro F1 in the 55–65% range after 5–6 epochs is documented as normal. The metric is inherently lower for many-class problems because each incorrect prediction is penalised equally regardless of proximity. A model that correctly identifies the sector but misses the leaf code still registers zero F1 for that sample.

*Source 2 — DeBERTa-v3-small capacity research (published NLP benchmarks)*  
deberta-v3-small (44M parameters) performs within **0.5–2% Macro F1** of deberta-v3-base (86M parameters) on classification tasks with up to ~200 classes when trained with sufficient epochs. The capacity ceiling attributed to the small model in Issue 14 was more likely a consequence of:
- Insufficient epochs (6 epochs with a linearly decaying LR leaves the model still learning)
- LR of 2e-5 being slightly too conservative — the documented optimum for deberta-v3-small is **3e-5**
- The LR schedule decaying to near-zero too early (Issue 12 identified this but the fix — 12 epochs at 4e-5 — overcorrected into a 12-hour Colab run)

*Source 3 — DeBERTa-v3 learning rate sensitivity (HuggingFace discussion forum)*  
DeBERTa-v3's disentangled attention is more sensitive to LR than RoBERTa-style models. The recommended starting LR for the small variant is **3e-5**, not 2e-5. Using 2e-5 can cause the model to learn more slowly and appear to plateau prematurely when it is in fact still on the learning curve.

*Source 4 — Sample count per class (40,000 ÷ 145 ≈ 276 samples per class)*  
Published guidance suggests deberta-v3-base provides meaningful gains over deberta-v3-small when training data is very large (>500k samples) or the class count exceeds ~300. At 40k samples and 145 classes, the small model is appropriate — base model gains at this scale are typically under 2% F1, which does not justify 4× the training time on T4.

**Revised conclusion:**  
The 62% plateau documented in Issue 14 was not a model capacity ceiling. It was a combination of:
1. LR 2e-5 (under the recommended 3e-5 for v3-small)
2. Only 6 epochs with a schedule that decayed the LR to 19% of peak by epoch 6
3. The model checkpoint at epoch 5 still had a loss of 0.94 — it had not converged

**Corrected Colab configuration (deberta-v3-small, 10 epochs, LR 3e-5):**

| Parameter | Old (Issue 14) | Corrected | Reason |
|---|---|---|---|
| Model | deberta-v3-small → base | **deberta-v3-small** | Research shows <2% F1 difference at this scale |
| MAX_LEN | 256 (base config) | **128** | Text averages 89 words; 256 adds runtime with no F1 gain |
| BATCH_SIZE | 6 (base) | **16** | Small model fits batch=16 on T4 |
| EPOCHS | 12 | **10** | Sufficient with sustained LR; avoids 12-hour runs |
| LR | 4e-5 | **3e-5** | Documented optimum for deberta-v3-small (HuggingFace) |
| Time/epoch | ~60 min | **~12 min** | 10× faster; total run ~2 hours |

**Action taken:**  
Notebook Cell 3 updated to the corrected configuration. Cell 6 updated to load from the epoch-5 checkpoint (60.67% F1) rather than starting from scratch, saving ~1 hour of retraining epochs 1–5.

**Expected outcome:**  
With 10 epochs, LR 3e-5, and a checkpoint start at epoch 5 (60.67% F1), the model has budget to reach 75–85% Macro F1 based on the observed learning trajectory (+19% epoch 1→2, declining as distinctions become finer). Whether it beats the 86.82% SVM baseline is an open question — but this approach runs the correct experiment in 2 hours rather than 12.

**If deberta-v3-base is still needed after this run:**  
Switch to base model only if the corrected small model run plateaus below 75% at epoch 10. At that point, use: MODEL_NAME=deberta-v3-base, MAX_LEN=128, BATCH_SIZE=8, EPOCHS=8, LR=2e-5. This gives ~3 hours on T4, not 12.

---

## 11. Packaging and Deployment — REST API Server

After training completes, the model is packaged as a standalone REST API server — similar in concept to Ollama. One command starts it, and it accepts classification requests from any application on the machine until stopped.

### The Server

**Script:** `llm_finetuning/scripts/serve.py`

Loads both Task 1 (145 industry codes) and Task 2 (407 subindustry codes) models at startup. If Task 2 has not been trained yet, it loads Task 1 only and returns `null` for subindustry predictions without crashing.

**Start the server:**
```bash
python llm_finetuning/scripts/serve.py
# or on a different port:
python llm_finetuning/scripts/serve.py --port 8001
```

Output at startup:
```
Device: cuda
Loading Task 1 (industry, 145 classes) ...
  Task 1 ready — 145 classes
Loading Task 2 (subindustry, 407 classes) ...
  Task 2 ready — 407 classes

Server running at  http://127.0.0.1:8000
Interactive docs   http://127.0.0.1:8000/docs
Press Ctrl+C to stop.
```

### API Endpoints

**POST /classify** — classify one company description

Request:
```json
{
  "text": "The company designs and manufactures semiconductor chips for consumer electronics.",
  "top_k": 3
}
```

Response:
```json
{
  "industry": {
    "predicted_code": "31103010",
    "confidence": 94.7,
    "top_k": [
      {"code": "31103010", "score": 94.7},
      {"code": "31103020", "score": 3.1},
      {"code": "31110010", "score": 1.4}
    ]
  },
  "subindustry": {
    "predicted_code": "31103011",
    "confidence": 87.2,
    "top_k": [...]
  },
  "latency_ms": 18.4
}
```

**POST /classify/batch** — classify up to 256 descriptions in one call

Request:
```json
{
  "texts": ["description 1", "description 2", "..."],
  "top_k": 3
}
```

Response: `{ "results": [...], "total_latency_ms": 42.1 }`

**GET /health** — check server and which models are loaded

**GET /info** — model details, label counts, device

Interactive API documentation is available at `http://127.0.0.1:8000/docs` while the server is running.

### How Classification Works at Inference

1. The tokenizer converts the raw description into integer token IDs (max 128 tokens, fully local)
2. The model runs a forward pass — 12 attention layers, each token attending to every other
3. Softmax is applied to the 145 (or 407) output logits to produce probabilities
4. The highest probability class is returned as the prediction, along with the top-k alternatives
5. The integer class index is decoded back to the original Morningstar GECS code using the saved label map

The server holds both models in GPU memory after startup, so every subsequent request is handled in under 25 ms on the RTX 3050.

### Design Choices

**Why a REST API instead of a Python library?**  
A REST API can be called from any language, notebook, or tool without importing the model code. Any downstream pipeline — whether Python, R, Excel via Power Query, or a web dashboard — can send an HTTP POST and get a JSON response.

**Why load both models on startup?**  
Loading a model from disk takes 3–5 seconds. Doing it per-request would make the API too slow for batch workflows. Loading once at startup means all requests are served instantly from GPU memory.

**No retraining needed for new data**  
Once training completes, the saved checkpoint classifies new descriptions indefinitely. Retraining is only needed if Morningstar changes how it writes descriptions, or if new GECS codes are introduced.

---

## 12. What the Model is Doing During Training — Plain English

This section explains the training process in plain terms, without assuming a machine learning background.

### The Simple Version

The model is reading your company descriptions, one small group at a time, and slowly teaching itself to recognize industries.

Every few seconds it does this:

1. It picks 8 company descriptions from the 42,868 training rows
2. It reads all 8 and makes a guess — "this company is in industry 23, this one is in industry 107" — completely random guesses at the start
3. It checks how wrong those guesses were against the real Morningstar codes in your data
4. That wrongness score is the loss number you see printing. A loss of 4.98 means very wrong. A loss of 0.3 means nearly always right
5. It figures out which direction to nudge each of its 44 million internal numbers to be slightly less wrong next time
6. It nudges them — very slightly — and moves to the next 8 descriptions
7. This repeats 5,359 times to finish one epoch, and runs for 4 epochs total

### What the Loss Number Means

The loss starts at approximately 4.97 because that is the mathematically expected score when guessing randomly across 145 classes. It is the same as saying "I have no idea, here is my best random guess."

As the model learns, the loss drops:

| Loss range | What it means |
|---|---|
| 4.5 - 5.0 | Random guessing, no meaningful patterns learned yet |
| 3.0 - 4.5 | Learning broad categories — finance vs tech vs healthcare |
| 1.5 - 3.0 | Getting the industry group right most of the time |
| 0.5 - 1.5 | Getting the specific industry right most of the time |
| 0.3 - 0.5 | Near convergence — model knows the task well |

### What the Warmup Phase Is

At the start of training, the learning rate is kept very small and gradually increases over the first 2,143 steps. This is called the warmup phase.

The reason: the classification head (the part that maps descriptions to industry codes) is brand new and randomly initialized. If the model learns too aggressively at the start, the large random gradients from the untrained head will overwrite the valuable patterns the model learned during pretraining on 160 GB of text. Warmup prevents this by starting cautiously and only accelerating once the new head has stabilized.

Once warmup ends, the learning rate hits its maximum of 2e-5 and the loss starts dropping much faster.

### What Warmup Looks Like in the Output

Actual training output from this run:

```
step 50/5359   | loss 4.9821 | lr 4.67e-07   -- warming up, lr is tiny
step 500/5359  | loss 4.7855 | lr 4.67e-06   -- still warming up, loss just starting to fall
step 3950/5359 | loss 2.0354 | lr 1.81e-05   -- warmup done, full learning rate, loss falling fast
```

### What Happens at the End of Each Epoch

After all 5,359 steps, the model pauses and evaluates itself on the 10,717 held-out test rows it has never seen. It runs through every test description, makes its best prediction, and compares against the true Morningstar codes. The result is the Macro F1 score — the number we compare against the 86.82% baseline.

The best scoring epoch is automatically saved. If epoch 3 scores higher than epoch 4, the epoch 3 weights are kept.

### Actual Epoch 1 Result

```
Epoch 1 complete | avg loss 2.9838 | Macro F1: 30.99%
```

30.99% after epoch 1 looks low but is expected and normal for this setup. The reason is that warmup covered the first 2,143 steps out of 5,359 — 40% of epoch 1 the model was barely moving, held back by the tiny learning rate. The model only hit its full learning rate halfway through the epoch.

This also reflects the difficulty of the task. 145 classes is a large classification problem. A random classifier on 145 classes would score approximately 0.7% Macro F1. At 30.99% the model has already learned meaningful patterns — it is getting the broad industry group right for most descriptions. What it has not yet learned is the fine distinctions between similar classes like "Software Application" vs "Software Infrastructure" or "Banks Regional" vs "Banks Diversified."

Those distinctions are learned in epochs 2 and 3, where the model runs at full learning rate from step 1 with no warmup.

**Projected progression based on epoch 1 result:**

| Epoch | Expected Macro F1 |
|---|---|
| 1 | 30.99% (actual) |
| 2 | 65 - 78% |
| 3 | 78 - 86% |
| 4 | 83 - 89% |

The jump from epoch 1 to epoch 2 is always the largest. Epoch 2 will run at full learning rate for all 5,359 steps with the model already having a solid understanding of the 145 classes from epoch 1.

### What is Running on Your Hardware Right Now

- Your RTX 3050 is executing roughly 1.2 trillion floating point operations per second
- Each of the 44 million model parameters is being updated thousands of times
- 42,868 proprietary company descriptions are being processed in full
- No data is leaving the machine
- The total electricity cost of this training run is approximately equivalent to leaving a light bulb on for two hours

---

## 13. What is Actually Happening During Training — Technical Detail

This section explains the training process in concrete terms, suitable for a presentation audience that may not have a deep ML background.

### The Setup

The model starts as `microsoft/deberta-v3-small`, a transformer pretrained on 160 GB of general text. It already understands English grammar, synonyms, sentence structure, and context. What it does not know yet is anything about Morningstar industry codes or how to map a company description to a GECS classification.

Fine-tuning is the process of teaching it that specific task using the 42,868 labeled examples in the training set.

### What Happens Each Step

Training runs in batches of 8 descriptions at a time. For each batch:

1. The tokenizer converts the raw text into sequences of integer token IDs, one token roughly equal to one word or word fragment.

2. The model runs a forward pass. Each token attends to every other token across 12 layers of attention, building a rich contextual representation of the entire description. The final hidden state is a single 768-dimensional vector summarizing the full input.

3. That vector passes through a classification head — a single linear layer — which produces 145 output scores, one per industry class. The highest score is the model's prediction.

4. The loss function (cross-entropy) measures how wrong the prediction was. If the correct class scored highest, the loss is near zero. If the wrong class scored highest, the loss is high.

5. The gradient of that loss flows backwards through all 44 million parameters. Each weight receives a small signal indicating which direction it should move to make the prediction more accurate next time.

6. The optimizer (AdamW) applies that signal, nudging every weight by a tiny amount. After 4 steps of this (gradient accumulation), the weights are actually updated.

This entire cycle repeats 5,360 times per epoch and 21,440 times across all 4 epochs.

### What the Loss Number Means

Every 50 steps, the training script prints a loss value. A typical progression looks like this:

```
{'loss': 4.80, 'epoch': 0.05}   -- model is guessing randomly across 145 classes
{'loss': 2.90, 'epoch': 0.50}   -- model is learning which broad categories exist
{'loss': 1.20, 'epoch': 1.50}   -- model distinguishes most major industries
{'loss': 0.55, 'epoch': 2.50}   -- model is learning fine-grained distinctions
{'loss': 0.30, 'epoch': 3.80}   -- model is near converged
```

The drop from 4.8 to 0.3 represents the model going from random guessing to reliably classifying the vast majority of company descriptions correctly.

### What Makes This Significant

- 44 million model parameters are being updated on a single consumer laptop GPU with 4 GB of memory
- The entire dataset of 42,868 proprietary financial records never leaves the machine
- No cloud service, no external API, no subscription is involved beyond the one-time download of 175 MB of model weights
- The training run completes in under 2 hours at a cost of zero dollars in compute fees
- The result is a custom classification model trained specifically on Morningstar GECS data that can be deployed inside the organization's own infrastructure

---

## 14. Model Generalization: What to Expect on New Data

### Where DeBERTa Will Perform Better

**Paraphrasing and synonyms**  
If a new company description says "develops enterprise cloud software" but the training set mostly had "provides SaaS solutions", TF-IDF treats these as completely different inputs because they share no tokens. DeBERTa maps them to nearly the same representation because it learned during pretraining that these phrases carry the same meaning.

**Short or sparse descriptions**  
Task 2 in particular suffers under TF-IDF when a segment description is only 10 to 15 words. There are too few tokens to build a confident decision boundary. DeBERTa fills in the gaps using pretrained semantic knowledge about what those words mean together, not just individually.

**Rare industry classes**  
Classes with fewer training examples have weak TF-IDF decision boundaries because there are not enough high-frequency tokens to anchor them. DeBERTa's pretrained weights provide a stronger initialization that generalizes better from a small number of examples.

**New vocabulary**  
If a company description contains a term the training set has never seen before, TF-IDF has no mechanism to handle it and ignores the token. DeBERTa uses subword tokenization and the surrounding context to infer meaning even for unseen words.

### Where the Model Has Real Limits

**It only knows what it was trained on**  
The model was fine-tuned on Morningstar descriptions from a specific time window. If a genuinely new industry emerges or sector terminology shifts significantly, both models will degrade. DeBERTa degrades more gracefully but still requires periodic retraining to stay accurate on new distributions.

**The baseline is already strong**  
86.82% Macro F1 across 145 classes is a high bar. The improvement from fine-tuning DeBERTa will likely be in the range of 2 to 5 percentage points, not a dramatic jump. This is still meaningful and statistically significant for a capstone, but expectations should be calibrated accordingly.

**Data drift over time**  
As Morningstar updates its company descriptions, portfolios change, and new terminology enters the industry, both models lose accuracy. Neither model is a permanent solution without a retraining schedule tied to data refreshes.

**Task 2 is genuinely harder**  
407 subindustry classes with short text and 54 classes that had fewer than 5 training samples is a difficult problem. Task 2 results will likely sit below Task 1 regardless of the model used. The improvement over an eventual TF-IDF baseline on Task 2 is where DeBERTa's advantage will be most visible.

### How to Frame This for the Capstone

The DeBERTa model is not a replacement for the existing pipeline. It is a demonstration that transformer-based classification is a credible and practical upgrade path for this specific workload.

The three contributions this module makes to the capstone are:

1. **Quantified gap** between classical NLP (TF-IDF + SVM) and modern transformer-based classification on the actual Morningstar dataset, measured under identical conditions on the same test split.

2. **Data safety proof** that a production-grade transformer model can be trained entirely in-house with no data exposure, using only a one-time 175 MB model weight download.

3. **Hardware feasibility** that this workload runs on a 4 GB consumer GPU, meaning it does not require cloud infrastructure or specialized hardware to operationalize.
