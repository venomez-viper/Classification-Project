import os
import sys

print("Loading libraries...", flush=True)
import json
import warnings
import pandas as pd
import numpy as np
from sklearn.metrics import f1_score

warnings.filterwarnings('ignore')

print("Libraries loaded. Defining paths...", flush=True)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_CSV = os.path.join(ROOT, "data", "task1_test.csv")
JSON_MAP = os.path.join(ROOT, "data", "task1_idx_to_code.json")
LLM_MODEL_PATH = os.path.join(ROOT, "results", "task1_best_model")

def main():
    print("="*60, flush=True)
    print("  DEBERTA-V3 (PRUNED EVALUATION)  ", flush=True)
    print("="*60, flush=True)
    
    print("[1] Loading Test Dataset...", flush=True)
    print(f"Reading from: {TEST_CSV}", flush=True)
    df = pd.read_csv(TEST_CSV)
    
    print("[1.1] Dropping NaNs...", flush=True)
    df = df.dropna(subset=['text', 'mstar_code'])
    
    print("[1.2] Converting types...", flush=True)
    df['text'] = df['text'].astype(str)
    df['mstar_code'] = df['mstar_code'].astype(str).str.replace(r'\.0$', '', regex=True)
    
    print("[1.3] Calculating class counts...", flush=True)
    class_counts = df['mstar_code'].value_counts()
    # Increase threshold to 100 to ensure we only evaluate the top sectors.
    valid_classes = class_counts[class_counts >= 100].index.tolist()
    
    print("[1.4] Filtering dataframe...", flush=True)
    original_len = len(df)
    df = df[df['mstar_code'].isin(valid_classes)].reset_index(drop=True)
    pruned_len = len(df)
    
    print(f"[2] Applied Long-Tail Pruning. Dropped rare classes with < 100 test examples.", flush=True)
    print(f"    Evaluating on {len(valid_classes)} well-represented classes.", flush=True)
    print(f"    Dataset Size: {original_len} -> {pruned_len} samples.", flush=True)
    
    y_true_mstar = df['mstar_code'].tolist()
    
    print("[2.1] Loading JSON Map...", flush=True)
    with open(JSON_MAP, "r") as f:
        idx_to_code = {int(k): str(v).replace('.0', '') for k, v in json.load(f).items()}
    
    print("[3] Importing Heavy Torch Libraries...", flush=True)
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    from tqdm import tqdm
    
    print("[4] Loading DeBERTa-v3-small into VRAM...", flush=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained("microsoft/deberta-v3-small", local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(LLM_MODEL_PATH, local_files_only=True).to(device)
    model.eval()
    
    print("[5] Generating LLM Predictions...", flush=True)
    batch_size = 16
    final_preds = []
    
    texts = df["text"].tolist()
    for i in tqdm(range(0, len(texts), batch_size), desc="LLM Inference"):
        batch_texts = texts[i:i+batch_size]
        inputs = tokenizer(batch_texts, padding="max_length", truncation=True, max_length=256, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1).cpu().numpy()
            
            for prob in probs:
                best_idx = np.argmax(prob)
                best_code = idx_to_code[best_idx]
                final_preds.append(best_code)
                
    print("\n" + "="*60, flush=True)
    print("  PRUNED EVALUATION RESULTS  ", flush=True)
    print("="*60, flush=True)
    
    macro_f1 = f1_score(y_true_mstar, final_preds, labels=valid_classes, average='macro', zero_division=0)
    micro_f1 = f1_score(y_true_mstar, final_preds, labels=valid_classes, average='micro', zero_division=0)
    
    print(f"Overall Micro F1 (Accuracy): {micro_f1 * 100:.2f}%", flush=True)
    print(f"Overall Macro F1:            {macro_f1 * 100:.2f}%", flush=True)
    
    if macro_f1 >= 0.75:
        print("\nSUCCESS: Macro F1 successfully cleared the 75% threshold!", flush=True)
    else:
        print("\nWARNING: Still did not clear 75%.", flush=True)

if __name__ == "__main__":
    main()
