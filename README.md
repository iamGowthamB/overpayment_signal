# Overpayment Signal

This project identifies and prioritizes benefit-payment cases that show potential overpayment or unusual transaction patterns using an unsupervised anomaly-detection approach.

* **No Ground-Truth improper-payment label**: There is no target label in the raw dataset identifying improper payments.
* **Investigation-Priority Ranking**: The model produces an investigation-priority score for each case to optimize casework resources.
* **Not Proof of Fraud**: A high score indicates a statistical anomaly or payment discrepancy and is **not** proof of improper payment or fraud.

---

## Problem Overview

The goal is to prioritize benefit-payment cases for administrative review and investigation. The system aggregates transaction-level payment behaviors and client-level information, scores them using unsupervised learning, and outputs a prioritized Top-20 worklist. Plain-language post-hoc explanations and post-hoc demographic fairness audits are provided for governance.

---

## Approach

```text
Raw Cases + Payments
→ Data Understanding
→ EDA
→ Feature Engineering
→ Isolation Forest
→ Priority Score
→ Top-20 Ranking
→ Explainability
→ Fairness Analysis
```

An unsupervised **Isolation Forest** algorithm is used to rank cases because the dataset has no explicit ground-truth labels. The model is trained on non-demographic aggregated metrics. The raw decision scores are inverted and normalized to a `[0, 1]` priority score.

---

## Repository Structure

```text
overpayment_signal/
├── data/
│   ├── raw/                 # Input cases.csv and payments.csv
│   └── processed/           # Processed features, rankings, and reports
├── notebooks/               # Executable pipeline notebooks (01 to 07)
├── src/                     # Reusable Python helper modules
├── requirements.txt         # Core dependencies list
├── DECISIONS.md             # Key design and architecture decisions
├── AI-USAGE.md              # AI tools usage declaration
└── FINAL_VALIDATION.md      # Final validation metrics matrix
```

---

## Setup and Installation

### 1. Prerequisites
* Python 3.10+
* Virtual environment tool (`venv`)

### 2. Environment Configuration
From the repository root directory:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (macOS/Linux)
source venv/bin/activate
```

### 3. Dependency Installation
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Execution Pipeline

Notebooks must be run sequentially in the following order:

1. **`01_data_understanding.ipynb`**: Performs dataset profiling and data structure checks.
2. **`02_eda.ipynb`**: Visualizes amount distributions, temporal anomalies, and payment adjustments.
3. **`03_feature_engineering.ipynb`**: Generates the case-level feature table.
4. **`04_model_training.ipynb`**: Fits the Isolation Forest and computes priority scores.
5. **`05_risk_scoring.ipynb`**: Ranks the worklist and generates the Top 20 cases.
6. **`06_explainability.ipynb`**: Compiles plain-language explanations for the prioritized cases.
7. **`07_fairness_analysis.ipynb`**: Audits representation ratios and score parity across demographics.

### Execution Commands
To execute the notebook pipeline from the repository root:
```bash
python -m nbconvert --to notebook --execute --inplace notebooks/01_data_understanding.ipynb
python -m nbconvert --to notebook --execute --inplace notebooks/02_eda.ipynb
python -m nbconvert --to notebook --execute --inplace notebooks/03_feature_engineering.ipynb
python -m nbconvert --to notebook --execute --inplace notebooks/04_model_training.ipynb
python -m nbconvert --to notebook --execute --inplace notebooks/05_risk_scoring.ipynb
python -m nbconvert --to notebook --execute --inplace notebooks/06_explainability.ipynb
python -m nbconvert --to notebook --execute --inplace notebooks/07_fairness_analysis.ipynb
```

---

## Expected Deliverables & Verification

After executing the pipeline, the following processed outputs are generated and verified:

* **`data/processed/case_features.csv`**: Feature table containing 4,200 rows and 34 columns.
* **`data/processed/scored_cases.csv`**: Raw scores and priority scores (4,200 rows).
* **`data/processed/ranked_cases.csv`**: Full ranked list of cases (4,200 rows).
* **`data/processed/top20_cases.csv`**: Top 20 prioritized cases worklist.
* **`data/processed/top20_explanations.csv`**: Human-readable explanations for the Top 20 cases.
* **`data/processed/fairness_report.csv`**: Representation ratios and average scores across demographics (17 rows).
