# Week 5 — Team Task Sheet
## MGT 599 Capstone · Group 4 · DePaul University Chicago

Each person runs **one independent model** this week. No coordination needed — just run your script, record your numbers, and share results with Akash.

Do NOT touch `server_legendary.py`, `train_cascade.py`, or anything in `legendary/` — that is Akash's work.

---

## Setup (everyone does this first)

```powershell
cd "C:\Users\akash\Desktop\capstone MGT 599"
pip install breezeml==0.2.5 lightgbm scikit-learn
python -c "import breezeml; print(breezeml.__version__)"  # should print 0.2.5
```

---

## Srilaxmi — Linear SVM with character n-grams on Task 1

```python
# save as: scripts/srilaxmi_week5.py
# run:     python scripts/srilaxmi_week5.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from scipy.sparse import hstack
from breezeml import classifiers

df = pd.read_csv("data/cleaned/task1_clean.csv")
df = df.dropna(subset=["text", "mstar_code"])

# Word n-grams
vec_word = TfidfVectorizer(max_features=50_000, ngram_range=(1, 2), sublinear_tf=True)
X_word   = vec_word.fit_transform(df["text"].tolist())

# Character n-grams (new this week)
vec_char = TfidfVectorizer(max_features=30_000, ngram_range=(3, 5),
                            analyzer="char_wb", sublinear_tf=True)
X_char   = vec_char.fit_transform(df["text"].tolist())

X = hstack([X_word, X_char]).tocsr()
y = df["mstar_code"].astype(str).tolist()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

_, report = classifiers.linear_svm(X=X_train, y=y_train, X_test=X_test, y_test=y_test)
print(report)
```

**Record your score:**
- Macro F1: ______
- Weighted F1: ______
- Last week's number to beat: Macro F1 = **(your Week 4 number)**

---

## Vishal — Logistic Regression with larger vocabulary on Task 1

```python
# save as: scripts/vishal_week5.py
# run:     python scripts/vishal_week5.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from breezeml import classifiers

df = pd.read_csv("data/cleaned/task1_clean.csv")
df = df.dropna(subset=["text", "mstar_code"])

# Bigger vocabulary + trigrams this week
vec = TfidfVectorizer(max_features=100_000, ngram_range=(1, 3),
                       sublinear_tf=True, min_df=2)
X   = vec.fit_transform(df["text"].tolist())
y   = df["mstar_code"].astype(str).tolist()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

_, report = classifiers.logistic_regression(
    X=X_train, y=y_train, X_test=X_test, y_test=y_test
)
print(report)
```

**Record your score:**
- Macro F1: ______
- Weighted F1: ______
- Last week's number to beat: Macro F1 = **(your Week 4 number)**

---

## Subasree — Linear SVM with balanced class weights on Task 2

```python
# save as: scripts/subasree_week5.py
# run:     python scripts/subasree_week5.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from breezeml import classifiers

df = pd.read_csv("data/cleaned/task2_clean.csv")
df = df.dropna(subset=["text"])

label_col = "GECSSubIndustryCode"   # update if your column name is different
y = df[label_col].astype(str).tolist()

# Larger vocab this week
vec = TfidfVectorizer(max_features=30_000, ngram_range=(1, 2),
                       sublinear_tf=True, min_df=2)
X   = vec.fit_transform(df["text"].tolist())

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

_, report = classifiers.linear_svm(
    X=X_train, y=y_train, X_test=X_test, y_test=y_test,
    class_weight="balanced"   # rebalance for rare codes
)
print(report)
```

**Record your score:**
- Macro F1: ______
- Weighted F1: ______
- Last week's number to beat: Weighted F1 = **(your Week 4 number)**

---

## Tserennad — Random Forest on Task 1

```python
# save as: scripts/tserennad_week5.py
# run:     python scripts/tserennad_week5.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

df = pd.read_csv("data/cleaned/task1_clean.csv")
df = df.dropna(subset=["text", "mstar_code"])

vec = TfidfVectorizer(max_features=20_000, ngram_range=(1, 2), sublinear_tf=True)
X   = vec.fit_transform(df["text"].tolist())
y   = df["mstar_code"].astype(str).tolist()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

clf = RandomForestClassifier(
    n_estimators=300,
    max_depth=40,
    min_samples_leaf=2,
    class_weight="balanced",
    n_jobs=-1,
    random_state=42,
)
clf.fit(X_train, y_train)
preds = clf.predict(X_test)
print(classification_report(y_test, preds, zero_division=0, digits=4))
```

**Record your score:**
- Macro F1: ______
- Weighted F1: ______
- Last week's number to beat: Macro F1 = **(your Week 4 number)**

---

## Results Table — fill in and send to Akash

| Person | Model | Task | Macro F1 | Weighted F1 |
|--------|-------|------|----------|-------------|
| Srilaxmi  | Linear SVM (word + char n-grams) | Task 1 | | |
| Vishal    | Logistic Regression (100k vocab, trigrams) | Task 1 | | |
| Subasree  | Linear SVM (balanced weights) | Task 2 | | |
| Tserennad | Random Forest | Task 1 | | |
| **Best from Week 4** | (whatever you scored) | | | |

---

*MGT 599 Capstone · Group 4 · DePaul University Chicago · Week 5 · May 2026*
