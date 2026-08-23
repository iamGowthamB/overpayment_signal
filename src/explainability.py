"""
Explainability Module for The Overpayment Signal.
Provides functions to generate plain-language explanations for prioritized cases.
"""

import pandas as pd
import numpy as np

def explain_case_row(row: pd.Series) -> tuple:
    """
    Analyzes an individual case row and identifies active anomaly signals,
    generating both technical labels and a plain-language explanation.
    
    Parameters:
    -----------
    row : pd.Series
        A single row from the scored cases dataset.
        
    Returns:
    --------
    tuple (str, str)
        A tuple of (contributing_signals_string, plain_language_explanation_string)
    """
    signals = []
    explanations = []
    
    # 1. Post-Closure Payment Signal
    if row['post_closure_payment_count'] > 0:
        signals.append('post_closure_payment')
        explanations.append(
            f"Payments continued after the recorded case closure "
            f"(case received {int(row['post_closure_payment_count'])} post-closure payments)."
        )
        
    # 2. Same-Month Multiple Payments Signal
    if row['has_same_month_multi_payments'] == 1:
        signals.append('multi_payment_month')
        explanations.append(
            f"Multiple payments were recorded within the same calendar month "
            f"(case received {int(row['total_payments'])} payments over {int(row['distinct_payment_months'])} months)."
        )
        
    # 3. Disbursed Amount Exceeds Monthly Award Signal
    if row['max_payment_to_award_ratio'] > 1.05:
        signals.append('high_award_excess')
        explanations.append(
            f"Actual payment amounts were substantially higher than the standard monthly award "
            f"(maximum payment was {row['max_payment_to_award_ratio']:.2f}x the award, "
            f"resulting in ${row['total_excess_amount']:,.2f} of total excess payments)."
        )
        
    # 4. Unusually High Standard Benefit Award
    if row['monthly_award'] > 1500:
        signals.append('high_standard_award')
        explanations.append(
            f"The case standard monthly award is unusually high (${row['monthly_award']:,.2f})."
        )
        
    # 5. Short Active Payment History (often flags sudden closures with high standard awards)
    if row['total_payments'] <= 3 and row['status'] == 'Closed':
        signals.append('short_payment_history')
        explanations.append(
            f"The case is closed and had a very short active payment history "
            f"(only {int(row['total_payments'])} transactions recorded)."
        )
        
    # 6. Unusually High Contact Attempts
    if row['contact_attempts'] >= 5:
        signals.append('high_contact_attempts')
        explanations.append(
            f"The case shows an unusually high number of agency contact attempts "
            f"({int(row['contact_attempts'])} attempts)."
        )
        
    # 7. Unusually Long Review Gap
    if row['months_since_review'] >= 18:
        signals.append('unreviewed_review_gap')
        explanations.append(
            f"The case has been unreviewed for an unusually long period "
            f"({int(row['months_since_review'])} months)."
        )
        
    # Fallback explanation if no explicit signals are tripped
    if len(explanations) == 0:
        signals.append('general_statistical_anomaly')
        explanations.append(
            f"The case exhibits a general statistical anomaly in its benefit history "
            f"(monthly award: ${row['monthly_award']:.2f}, total payments: {int(row['total_payments'])})."
        )
        
    return ' | '.join(signals), ' | '.join(explanations)

def generate_case_explanations(df_scored: pd.DataFrame) -> pd.DataFrame:
    """
    Ranks scored cases, generates plain-language explanations for each,
    and returns a summarized dataframe suitable for investigation review.
    
    Parameters:
    -----------
    df_scored : pd.DataFrame
        DataFrame of scored cases (needs anomaly_score, priority_score).
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with ranks, case IDs, scores, contributing signals, and explanations.
    """
    # Ensure dataframe is sorted descending by priority_score
    df_sorted = df_scored.sort_values(by='priority_score', ascending=False).reset_index(drop=True)
    df_sorted['rank'] = df_sorted.index + 1
    
    signals_list = []
    explanations_list = []
    
    for _, row in df_sorted.iterrows():
        sig, expl = explain_case_row(row)
        signals_list.append(sig)
        explanations_list.append(expl)
        
    df_sorted['top_contributing_signals'] = signals_list
    df_sorted['plain_language_explanation'] = explanations_list
    
    # Select subset of key columns to return
    output_cols = [
        'rank', 'case_id', 'priority_score', 'status', 'monthly_award',
        'total_payments', 'post_closure_payment_count', 'total_excess_amount',
        'has_same_month_multi_payments', 'contact_attempts', 'months_since_review',
        'top_contributing_signals', 'plain_language_explanation'
    ]
    
    return df_sorted[output_cols]

def generate_governed_case_explanations(df_gov: pd.DataFrame) -> pd.DataFrame:
    """
    Ranks governed cases using adjusted_priority_score, generates plain-language
    explanations, and returns a dataframe suitable for review.
    
    Parameters:
    -----------
    df_gov : pd.DataFrame
        DataFrame of governed cases (needs adjusted_priority_score, priority_score).
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with ranks, case IDs, scores, contributing signals, and explanations.
    """
    # Sort deterministically
    df_sorted = df_gov.sort_values(by=['adjusted_priority_score', 'case_id'], ascending=[False, True]).reset_index(drop=True)
    df_sorted['rank'] = df_sorted.index + 1
    
    signals_list = []
    explanations_list = []
    
    for _, row in df_sorted.iterrows():
        sig, expl = explain_case_row(row)
        
        # If the case is admin-only, we check if it was dampened.
        # However, for the Top 20, none are admin-only, so this is a safety fallback.
        if row.get('is_admin_only', False):
            # Do not expose internal scoring math. Filter out high_contact_attempts or adjustments
            # if they are not legitimate payment anomalies.
            cleaned_sigs = [s for s in sig.split(' | ') if s not in ['high_contact_attempts']]
            cleaned_expls = [e for e in expl.split(' | ') if "contact attempts" not in e]
            if not cleaned_sigs:
                cleaned_sigs = ['general_statistical_anomaly']
                cleaned_expls = [f"The case exhibits a general statistical anomaly in its benefit history."]
            sig = ' | '.join(cleaned_sigs)
            expl = ' | '.join(cleaned_expls)
            
        signals_list.append(sig)
        explanations_list.append(expl)
        
    df_sorted['top_contributing_signals'] = signals_list
    df_sorted['plain_language_explanation'] = explanations_list
    
    output_cols = [
        'rank', 'case_id', 'adjusted_priority_score', 'priority_score', 'status', 'monthly_award',
        'total_payments', 'post_closure_payment_count', 'total_excess_amount',
        'has_same_month_multi_payments', 'contact_attempts', 'months_since_review',
        'top_contributing_signals', 'plain_language_explanation'
    ]
    
    return df_sorted[output_cols]

