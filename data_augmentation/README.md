# Data Augmentation (Secondary Track)

This folder contains experimental scripts for augmenting training data using LLMs. 

## Purpose
To handle extreme class imbalance in the GECS dataset, we can use an LLM to generate or expand company descriptions for rare minority classes. This gives the DeBERTa model more substantial text to learn from.

## Usage
1. Edit `expand_descriptions.py` to insert your LLM API Key (e.g., OpenAI).
2. Adjust the `WORD_COUNT_THRESHOLD` as needed.
3. Run the script: `python expand_descriptions.py`
4. Use the newly generated `task1_train_augmented.csv` for fine-tuning.
