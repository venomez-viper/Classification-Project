# Architecture vs Intelligence: Why BreezeML Beat DeBERTa
## MGT 599 Capstone · Group 4 · DePaul University Chicago

---

## The Core Finding

> **A classical SVM with the right structure outperformed a fine-tuned neural transformer by +24.9 percentage points — not because it was smarter, but because it was better organized.**

This document explains what each model does, why one won, and what that result means.

---

## How Each Model Understands Text

### BreezeML (LinearSVC + TF-IDF) — Pattern Matching

The SVM does not understand language. It converts every company description into a vector of 50,000 numbers — each number representing how often a specific word or phrase appeared. It then draws a mathematical boundary that separates the classes.

**What it learned:**  
Words like *"mortgage"*, *"brokerage"*, *"deposits"* → Financial Services  
Words like *"semiconductor"*, *"wafer"*, *"chip fabrication"* → Technology Hardware

**What it struggles with:**  
*"The business takes money from regular people and lends it out to buy homes."*  
No jargon. No technical terms. The SVM may miss this entirely because none of the exact learned keywords appeared.

---

### DeBERTa-v3-small — Meaning Understanding

DeBERTa is a transformer model pre-trained on billions of sentences. It learned grammar, context, and semantic relationships between words before ever seeing financial data.

**What it learned:**  
That *"takes money from people and lends it out"* and *"retail deposit banking"* describe the same activity. The words are different but the meaning is the same.

**Proof from the live demo:**

| Input (plain English, zero jargon) | DeBERTa Output |
|------------------------------------|----------------|
| "Workers drill deep holes into the earth and the ocean floor to find pockets of crude oil" | Oil & Gas Exploration ✓ |
| "Scientists spend years in labs trying to find new drugs that can stop cancer cells from growing" | Biotechnology ✓ |
| "The firm builds fighter jets and missiles under government contracts" | Aerospace & Defence ✓ |
| "The company designs tiny chips that go inside smartphones to make them run fast" | Semiconductors ✓ |

The SVM would likely misclassify most of these — none of them use standard financial taxonomy language.

---

## Why the SVM Still Won

If DeBERTa understands language better, why did it score 64% Macro F1 while BreezeML Level 2 scored 88.90%?

### The problem: 145 classes, all at once

In the flat configuration, both models face the same problem: a company description must be assigned to 1 of 145 Morningstar codes in a single decision. For DeBERTa, this means its softmax output layer competes across all 145 classes simultaneously.

When two classes are semantically similar — *"Regional Banks"* vs *"Diversified Banks"*, or *"Oil & Gas Exploration"* vs *"Oil & Gas Midstream"* — DeBERTa's language understanding alone is not enough to reliably separate them, especially for rare classes with fewer than 10 training examples.

### The solution: structural advantage

BreezeML Level 2 does not ask one model to do everything. It mirrors the actual Morningstar taxonomy tree:

```
Input text
    │
    ▼  L1 — Broad Sector        (11 classes)
    │       "This is Energy."
    │
    ▼  L2 — Industry Group      (5–8 classes within Energy)
    │       "This is Oil & Gas, not Utilities."
    │
    ▼  L3 — Morningstar Code    (3–5 classes within Oil & Gas)
            "This is Exploration, not Midstream."
```

At each level, the classifier only competes against a small group of closely related classes. *"Oil & Gas Midstream"* never has to compete against *"Regional Banks"* — they are separated at Level 1. By Level 3, the model only needs to distinguish between 3–5 codes, not 145.

### The numbers

| Model | Macro F1 | What it competed against per prediction |
|-------|----------|-----------------------------------------|
| DeBERTa (flat) | 64.00% | All 145 classes at once |
| Flat SVM (flat) | 59.70% | All 145 classes at once |
| **BreezeML Level 2** | **88.90%** | **3–8 classes per level** |

The cascade SVM on rare classes (≤10 training samples):

| Model | Rare-class Macro F1 |
|-------|---------------------|
| Flat SVM | 20.44% |
| **BreezeML Level 2** | **73.68%** |

Rare classes improved by +53 percentage points — not because of better language understanding, but because rare classes no longer have to compete against the entire taxonomy.

---

## What Each Model Is Good For

| Capability | BreezeML Level 2 | DeBERTa |
|------------|-----------------|---------|
| Understands plain English | No — needs domain keywords | **Yes** |
| Handles taxonomy structure | **Yes — 3-level hierarchy** | No — flat softmax |
| Accuracy on 145 classes | **88.90%** | 64.00% |
| Speed | **1,673 samples/sec on CPU** | ~40 samples/sec on GPU |
| Requires GPU | No | Yes |
| Rare class performance | **73.68%** | ~20% (estimated) |
| Needs exact financial terms | Yes | No |

---

## The Key Insight

DeBERTa is the more intelligent model. It can read a sentence written in plain English and understand what industry it describes without any financial jargon.

BreezeML is the better-organized model. It uses the known structure of the Morningstar taxonomy to reduce every decision to a small, manageable choice.

On this dataset and task, **organization beat intelligence by 24.9 percentage points**.

This is not a fluke. It reflects a general principle in machine learning:

> *A well-structured simpler model will outperform a powerful model given the wrong structure — especially on imbalanced, hierarchical classification problems.*

The correct long-term architecture is a hybrid: use BreezeML's cascade to narrow the search space, then use DeBERTa's language understanding within each narrow branch. That is the next step described in the Week 4 guide.

---

## Practical Summary for the Presentation

- **BreezeML Level 2** is your production model. Use it when you need fast, accurate, CPU-only classification.
- **DeBERTa** is your research finding. Use it to demonstrate that even a neural network with language understanding loses to a well-engineered classical model when the problem has known hierarchical structure.
- The result is publishable as a finding: *hierarchical decomposition of a multi-class problem produces larger gains than switching to a more powerful model class.*

---

*MGT 599 Capstone · Group 4 · DePaul University Chicago · Spring 2026*
