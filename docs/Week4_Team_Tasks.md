# Week 4 — Team Task Sheet
## MGT 599 Capstone · Group 4 · DePaul University Chicago

Each person runs **one independent model** this week. No coordination needed — just run your script, record your numbers, and share results with Akash.

Do NOT touch `server_legendary.py`, `train_cascade.py`, or anything in `legendary/` — that is Akash's work.

---

## Setup (everyone does this first)

```powershell
cd "C:\Users\akash\Desktop\capstone MGT 599"
pip install breezeml==0.2.5
python -c "import breezeml; print(breezeml.__version__)"  # should print 0.2.5
```

---

## Srilaxmi — Linear SVM on Task 1

```python
# save as: scripts/srilaxmi_week4.py
# run:     python scripts/srilaxmi_week4.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from breezeml import classifiers

df = pd.read_csv("data/cleaned/task1_clean.csv")
df = df.dropna(subset=["text", "mstar_code"])

vec = TfidfVectorizer(max_features=50_000, ngram_range=(1, 2), sublinear_tf=True)
X   = vec.fit_transform(df["text"].tolist())
y   = df["mstar_code"].astype(str).tolist()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

_, report = classifiers.linear_svm(X=X_train, y=y_train, X_test=X_test, y_test=y_test)
print(report)
```

**Record your score:**
- Macro F1: ______
- Weighted F1: ______
- Last week's number to beat: Macro F1 = **59.70%**

---

## Vishal — Logistic Regression on Task 1

```python
# save as: scripts/vishal_week4.py
# run:     python scripts/vishal_week4.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from breezeml import classifiers

df = pd.read_csv("data/cleaned/task1_clean.csv")
df = df.dropna(subset=["text", "mstar_code"])

vec = TfidfVectorizer(max_features=50_000, ngram_range=(1, 2), sublinear_tf=True)
X   = vec.fit_transform(df["text"].tolist())
y   = df["mstar_code"].astype(str).tolist()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

_, report = classifiers.logistic_regression(X=X_train, y=y_train, X_test=X_test, y_test=y_test)
print(report)
```

**Record your score:**
- Macro F1: ______
- Weighted F1: ______
- Last week's number to beat: Macro F1 = **59.70%**

---

## Subasree — Linear SVM on Task 2

```python
# save as: scripts/subasree_week4.py
# run:     python scripts/subasree_week4.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from breezeml import classifiers

df = pd.read_csv("data/cleaned/task2_clean.csv")
df = df.dropna(subset=["text"])

label_col = "GECSSubIndustryCode"   # update if your column name is different
y = df[label_col].astype(str).tolist()

vec = TfidfVectorizer(max_features=10_000, ngram_range=(1, 2), sublinear_tf=True)
X   = vec.fit_transform(df["text"].tolist())

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

_, report = classifiers.linear_svm(
    X=X_train, y=y_train, X_test=X_test, y_test=y_test,
    class_weight="balanced"
)
print(report)
```

**Record your score:**
- Macro F1: ______
- Weighted F1: ______
- Last week's number to beat: Weighted F1 = **47.72%**

---

## Tserennad — Naive Bayes on Task 1

```python
# save as: scripts/tserennad_week4.py
# run:     python scripts/tserennad_week4.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from breezeml import classifiers

df = pd.read_csv("data/cleaned/task1_clean.csv")
df = df.dropna(subset=["text", "mstar_code"])

vec = TfidfVectorizer(max_features=50_000, ngram_range=(1, 2), sublinear_tf=True)
X   = vec.fit_transform(df["text"].tolist())
y   = df["mstar_code"].astype(str).tolist()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

_, report = classifiers.naive_bayes(X=X_train, y=y_train, X_test=X_test, y_test=y_test)
print(report)
```

**Record your score:**
- Macro F1: ______
- Weighted F1: ______
- Last week's number to beat: Macro F1 = **59.70%**

---

## Results Table — fill in and send to Akash

| Person | Model | Task | Macro F1 | Weighted F1 |
|--------|-------|------|----------|-------------|
| Srilaxmi  | Linear SVM         | Task 1 | | |
| Vishal    | Logistic Regression| Task 1 | | |
| Subasree  | Linear SVM         | Task 2 | | |
| Tserennad | Naive Bayes        | Task 1 | | |
| **Baseline (Week 3)** | Flat SVM | Task 1 | 59.70% | 86.82% |

---

*MGT 599 Capstone · Group 4 · DePaul University Chicago · Week 4 · May 2026*
