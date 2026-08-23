"""
Model Training and Scoring Module for The Overpayment Signal.
Provides functions to train an unsupervised Isolation Forest model
and rank cases by investigation priority.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

def train_and_score(features_path: str, output_path: str) -> pd.DataFrame:
    """
    Loads case features, prepares features for the Isolation Forest model,
    trains the model, scores each case, ranks them by priority,
    and saves the scored dataset.
    
    Parameters:
    -----------
    features_path : str
        Path to data/processed/case_features.csv
    output_path : str
        Path to save data/processed/scored_cases.csv
        
    Returns:
    --------
    pd.DataFrame
        DataFrame of all cases sorted from highest to lowest investigation priority.
    """
    # 1. Load the case-level feature table
    df = pd.read_csv(features_path)
    
    # 2. Select model features
    # Exclude demographic fields to prevent model bias
    demographic_cols = ['district', 'age_band', 'language_preference', 'tenure']
    
    # Exclude identifier and raw dates
    exclude_cols = ['case_id', 'opened_date', 'closure_month']
    
    # Non-demographic features to use directly (numeric)
    numeric_features = [
        'household_size', 'monthly_award', 'opened_year', 'opened_month', 'case_age_months',
        'contact_attempts', 'months_since_review', 'payment_adjustments',
        'total_payments', 'total_amount_paid', 'avg_payment_amount', 'min_payment_amount',
        'max_payment_amount', 'std_payment_amount', 'distinct_payment_months',
        'max_payments_in_single_month', 'multi_payment_months_count', 'has_same_month_multi_payments',
        'post_closure_payment_count', 'is_post_closure_paid', 'total_post_closure_amount',
        'total_excess_amount', 'avg_payment_to_award_ratio', 'max_payment_to_award_ratio',
        'num_adjusted_payments', 'adjustment_rate'
    ]
    
    # 3. Data Preparation
    # Prepare X matrix: numeric features + one-hot encoded 'status'
    X = df[numeric_features].copy()
    
    # One-hot encode status (categorical non-demographic)
    status_dummies = pd.get_dummies(df['status'], prefix='status', dtype=int)
    X = pd.concat([X, status_dummies], axis=1)
    
    # Keep column order stable
    model_features_list = list(X.columns)
    
    # 4. Train Isolation Forest
    # We use a fixed random state for reproducibility and default contamination='auto'
    clf = IsolationForest(
        n_estimators=100,
        contamination='auto',
        random_state=42
    )
    clf.fit(X)
    
    # 5. Generate scores
    # sklearn decision_function returns negative values for anomalies, positive for normal.
    # We invert it so higher score = higher anomaly / investigation priority.
    raw_anomaly_scores = -clf.decision_function(X)
    
    # Scale scores linearly to [0, 1] range to represent an Investigation Priority Score
    s_min = raw_anomaly_scores.min()
    s_max = raw_anomaly_scores.max()
    priority_scores = (raw_anomaly_scores - s_min) / (s_max - s_min)
    
    # Add scores to original DataFrame
    df_scored = df.copy()
    df_scored['anomaly_score'] = raw_anomaly_scores
    df_scored['priority_score'] = priority_scores
    
    # 6. Rank cases: sort descending by priority
    df_scored = df_scored.sort_values(by='priority_score', ascending=False).reset_index(drop=True)
    
    # 7. Basic Model Sanity Checks (Asserts)
    assert len(df_scored) == 4200, f"Expected 4200 scored cases, got {len(df_scored)}"
    assert df_scored['priority_score'].isnull().sum() == 0, "Found missing priority scores"
    assert not df_scored['case_id'].duplicated().any(), "case_id is not unique in scored table"
    assert (df_scored['priority_score'].diff().dropna() <= 0.000001).all(), "Scores are not correctly sorted in descending order"
    
    # 8. Save scored cases
    df_scored.to_csv(output_path, index=False)
    
    return df_scored
