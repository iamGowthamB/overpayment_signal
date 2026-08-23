"""
Feature Engineering Module for The Overpayment Signal.
Provides functions to construct a case-level feature table from cases and payments data.
"""

import pandas as pd
import numpy as np

def build_case_features(cases_path: str, payments_path: str) -> pd.DataFrame:
    """
    Loads raw cases and payments datasets, engineers case-level features,
    and returns a clean, single-row-per-case feature DataFrame.
    
    Parameters:
    -----------
    cases_path : str
        File path to cases.csv
    payments_path : str
        File path to payments.csv
        
    Returns:
    --------
    pd.DataFrame
        Aggregated case-level feature table.
    """
    # 1. Load datasets
    df_cases = pd.read_csv(cases_path)
    df_payments = pd.read_csv(payments_path)
    
    # 2. Case-level basic payment behaviors
    # We group payments by case_id to extract statistical metrics of their payments
    pay_grouped = df_payments.groupby('case_id')
    
    df_pay_behavior = pay_grouped.agg(
        total_payments=('amount', 'count'),
        total_amount_paid=('amount', 'sum'),
        avg_payment_amount=('amount', 'mean'),
        min_payment_amount=('amount', 'min'),
        max_payment_amount=('amount', 'max'),
        std_payment_amount=('amount', 'std'),
        distinct_payment_months=('pay_month', 'nunique')
    ).reset_index()
    
    # Handle std deviation being NaN for cases with only 1 payment
    df_pay_behavior['std_payment_amount'] = df_pay_behavior['std_payment_amount'].fillna(0.0)
    
    # 3. Payment frequency and monthly patterns
    # Calculate counts per case per month to identify duplicate payment issues
    month_counts = df_payments.groupby(['case_id', 'pay_month']).size().reset_index(name='count')
    
    # Max payments in any single month for each case
    max_pay_single_month = month_counts.groupby('case_id')['count'].max().reset_index(name='max_payments_in_single_month')
    
    # Count of months that received more than 1 payment
    multi_pay_months = month_counts.groupby('case_id').apply(
        lambda x: (x['count'] > 1).sum(),
        include_groups=False
    ).reset_index(name='multi_payment_months_count')
    
    # Merge monthly patterns
    df_pay_patterns = pd.merge(max_pay_single_month, multi_pay_months, on='case_id')
    df_pay_patterns['has_same_month_multi_payments'] = (df_pay_patterns['multi_payment_months_count'] > 0).astype(int)
    
    # 4. Transaction-level potential signal calculations
    # We merge payments with case metadata to perform comparative logic
    payments_merged = df_payments.merge(df_cases[['case_id', 'monthly_award', 'closure_month']], on='case_id')
    
    # Post-closure payment flag
    # Note: If closure_month is null (NaN), this comparison naturally yields False
    payments_merged['is_post_closure'] = payments_merged['pay_month'] > payments_merged['closure_month']
    
    # Excess payments relative to standard award
    payments_merged['payment_excess_amount'] = (payments_merged['amount'] - payments_merged['monthly_award']).apply(lambda x: max(0.0, x))
    payments_merged['payment_excess_ratio'] = payments_merged['amount'] / payments_merged['monthly_award']
    payments_merged['is_adjusted'] = (payments_merged['adjustment'] == 'Y').astype(int)
    
    # Group comparative metrics to case-level
    df_signals = payments_merged.groupby('case_id').agg(
        post_closure_payment_count=('is_post_closure', 'sum'),
        total_post_closure_amount=('amount', lambda x: x[payments_merged.loc[x.index, 'is_post_closure']].sum()),
        total_excess_amount=('payment_excess_amount', 'sum'),
        avg_payment_to_award_ratio=('payment_excess_ratio', 'mean'),
        max_payment_to_award_ratio=('payment_excess_ratio', 'max'),
        num_adjusted_payments=('is_adjusted', 'sum')
    ).reset_index()
    
    # Binary post-closure indicator
    df_signals['is_post_closure_paid'] = (df_signals['post_closure_payment_count'] > 0).astype(int)
    
    # Merge with basic behavior to compute adjustment rate
    df_signals = df_signals.merge(df_pay_behavior[['case_id', 'total_payments']], on='case_id')
    df_signals['adjustment_rate'] = df_signals['num_adjusted_payments'] / df_signals['total_payments']
    df_signals = df_signals.drop(columns=['total_payments'])
    
    # 5. Temporal Features from cases.csv
    # Calculate opened date characteristics and age of the case relative to December 2025 (end of window)
    opened_dt = pd.to_datetime(df_cases['opened_date'])
    df_temporal = pd.DataFrame({'case_id': df_cases['case_id']})
    df_temporal['opened_year'] = opened_dt.dt.year
    df_temporal['opened_month'] = opened_dt.dt.month
    
    # Fixed reference date at the end of tracking period (2025-12-31)
    ref_date = pd.to_datetime('2025-12-31')
    df_temporal['case_age_months'] = (ref_date.year - opened_dt.dt.year) * 12 + (ref_date.month - opened_dt.dt.month)
    
    # 6. Assembly of Case-Level Feature Table
    # Start with raw case attributes, then join engineered payment features
    feature_df = df_cases.copy()
    
    feature_df = feature_df.merge(df_pay_behavior, on='case_id', how='left')
    feature_df = feature_df.merge(df_pay_patterns, on='case_id', how='left')
    feature_df = feature_df.merge(df_signals, on='case_id', how='left')
    feature_df = feature_df.merge(df_temporal, on='case_id', how='left')
    
    # Re-order/Clean columns
    # We place ID, status, and demographics first, then case info, then payment features
    cols_order = [
        'case_id', 'status', 'district', 'age_band', 'language_preference', 'tenure',
        'household_size', 'opened_date', 'closure_month', 'monthly_award',
        'opened_year', 'opened_month', 'case_age_months',
        'contact_attempts', 'months_since_review', 'payment_adjustments',
        'total_payments', 'total_amount_paid', 'avg_payment_amount', 'min_payment_amount',
        'max_payment_amount', 'std_payment_amount', 'distinct_payment_months',
        'max_payments_in_single_month', 'multi_payment_months_count', 'has_same_month_multi_payments',
        'post_closure_payment_count', 'is_post_closure_paid', 'total_post_closure_amount',
        'total_excess_amount', 'avg_payment_to_award_ratio', 'max_payment_to_award_ratio',
        'num_adjusted_payments', 'adjustment_rate'
    ]
    
    # Assert all columns are present
    assert set(cols_order).issubset(feature_df.columns), f"Missing columns in engineered table: {set(cols_order) - set(feature_df.columns)}"
    
    return feature_df[cols_order]
