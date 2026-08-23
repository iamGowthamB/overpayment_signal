# Architectural & Design Decisions

This document records the key architectural and design decisions made for **Problem 6: The Overpayment Signal**.

## 1. Core Model & Scoring Decisions

*   **Decision 1: No Target Label → Unsupervised Isolation Forest**: Because the raw benefit-payment datasets contain no explicit improper-payment target labels, we implemented an unsupervised Isolation Forest model to detect multi-dimensional anomalies instead of a supervised classifier.
*   **Decision 2: Demographic Exclusion from Predictive Inputs**: All demographic fields (`district`, `age_band`, `language_preference`, `tenure`) are strictly excluded from the predictive model feature matrix to prevent encoding algorithmic bias.
*   **Decision 3: Case-Level Feature Engineering**: We aggregated transaction histories to case-level features representing payment aggregates, post-closure payment counts, same-month duplicates, and standard deviations to align with the core entity level of benefit cases.
*   **Decision 4: Deterministic Post-Hoc Explainability**: We implemented a post-hoc rule-based explainability engine that maps anomaly drivers to deterministic plain-language sentences containing precise numerical metrics, ensuring complete auditability and demographic exclusivity.
*   **Decision 5: Post-Hoc Fairness Auditing**: We established a post-hoc audit framework to calculate representation ratios and priority score parity across demographic strata, ensuring transparency without using protected fields in predictive scoring.

## 2. Governance Adaptation Decisions (Surprise Challenge)

*   **Decision 6: Administrative-vs-Financial Signal Distinction**: Based on investigator feedback from case `C-33248`, we separated administrative signals (e.g. contact attempts, adjustments) from direct outcome financial signals (e.g. post-closure payments, same-month duplicates, large overpayments).
*   **Decision 7: No Retraining after Investigator Feedback**: To keep model boundaries stable for all other cases and comply with surprise challenge rules, we did not retrain the Isolation Forest model.
*   **Decision 8: Post-Hoc Governance Adaptation**: We implemented a post-hoc score adjustment function (`src/governance.py`) that dampens scores only for administrative-only cases while keeping genuine financial anomalies intact.
*   **Decision 9: 60% Bounded Administrative Dampening Cap**: Through in-memory sensitivity analysis, a maximum dampening cap of 60% was selected as the smallest cap that successfully reduces administrative-only cases in the Top 20 to zero while demoting `C-33248` to rank 1,097.
*   **Decision 10: Original Score Preservation**: The original `priority_score` is preserved for historical auditability, while the new rank is derived from `adjusted_priority_score`.
*   **Decision 11: $200 Empirical Threshold**: A threshold of $200 in excess payments was set empirically to exempt minor overpayments from priority ranking while protecting cases with material leakages.



