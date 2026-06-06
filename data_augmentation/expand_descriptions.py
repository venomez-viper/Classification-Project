import pandas as pd
import json
import os
import time

# --- CONFIGURATION ---
# Replace with your actual OpenAI API key or local LLM endpoint
OPENAI_API_KEY = "sk-your-api-key-here"

# Path logic for the new folder
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "llm_finetuning", "data")
INPUT_CSV = os.path.join(DATA_DIR, "task1_train.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "task1_train_augmented.csv")
JSON_MAP = os.path.join(DATA_DIR, "task1_idx_to_code.json")

# Define the threshold for what constitutes a "short" description
WORD_COUNT_THRESHOLD = 20

import torch
from transformers import pipeline

print("Loading local LLM for text expansion (this is 100% free and runs offline)...")
# We use google/flan-t5-base because it's highly capable of instruction following
# and small enough (~900MB) to fit perfectly on a 4GB VRAM GPU without crashing.
device = 0 if torch.cuda.is_available() else -1
generator = pipeline("text2text-generation", model="google/flan-t5-base", device=device)

def get_expanded_description(original_text, industry_name):
    """
    Uses a free local HuggingFace model to expand the short company description.
    """
    prompt = (
        f"Expand the following short company description into a realistic, detailed 3-sentence profile "
        f"for a company in the '{industry_name}' industry. Add typical products and services.\n\n"
        f"Original: {original_text}\n\n"
        f"Expanded:"
    )
    
    try:
        # Generate the expanded text
        output = generator(
            prompt, 
            max_length=150, 
            min_length=40,
            do_sample=True,
            temperature=0.7,
            truncation=True
        )
        expanded_text = output[0]['generated_text'].strip()
        
        # Sometimes small models output the prompt again, ensure we just have the expansion
        if len(expanded_text) < len(original_text):
            return original_text
            
        return expanded_text
        
    except Exception as e:
        print(f"Generation Error for text '{original_text[:20]}...': {e}")
        return original_text

def main():
    print("Loading data...")
    df = pd.read_csv(INPUT_CSV, dtype={"text": str, "label_idx": int})
    
    with open(JSON_MAP, "r") as f:
        idx_to_code = json.load(f)

    expanded_rows = 0
    new_texts = []

    print(f"Total rows in dataset: {len(df)}")
    
    for i, row in df.iterrows():
        # Print progress every 500 rows so it doesn't look frozen
        if i > 0 and i % 500 == 0:
            print(f"Processed {i} / {len(df)} rows... (Expanded {expanded_rows} so far)")
            
        text = str(row["text"])
        label_idx = str(row["label_idx"])
        industry_code = idx_to_code.get(label_idx, "Unknown Industry")
        
        word_count = len(text.split())
        
        if word_count < WORD_COUNT_THRESHOLD:
            expanded_text = get_expanded_description(text, industry_code)
            new_texts.append(expanded_text)
            expanded_rows += 1
        else:
            new_texts.append(text)

    df["text"] = new_texts
    
    print(f"\nExpanded {expanded_rows} short descriptions.")
    print(f"Saving augmented dataset to {OUTPUT_CSV}...")
    df.to_csv(OUTPUT_CSV, index=False)
    print("Done!")

if __name__ == "__main__":
    main()
