"""
Governance Module for The Overpayment Signal.
Provides functions to apply post-hoc governance adjustments to priority scores,
dampening administrative process signals for cases without outcomes of financial leakage.
"""

import pandas as pd
import numpy as np

def apply_governance_adjustment(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies a post-hoc governance adjustment to the priority score.
    For cases with no outcome-based financial anomalies (no post-closure payments,
    no same-month multi-payments, and excess payments <= $200), the priority score
    is scaled down based on the case's administrative activity intensity.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Scored cases DataFrame (needs priority_score, contact_attempts,
        payment_adjustments, post_closure_payment_count,
        has_same_month_multi_payments, total_excess_amount).
        
    Returns:
    -------
    pd.DataFrame
        A copy of the DataFrame with 'adjusted_priority_score' added.
    """
    df_out = df.copy()
    
    # 1. Define the admin-only mask (cases without meaningful financial anomalies)
    admin_only_mask = (
        (df_out['post_closure_payment_count'] == 0) &
        (df_out['has_same_month_multi_payments'] == 0) &
        (df_out['total_excess_amount'] <= 200.0)
    )
    
    # 2. Calculate normalized administrative intensity
    max_contact = df_out['contact_attempts'].max()
    max_adjust = df_out['payment_adjustments'].max()
    
    # Prevent division by zero if population maxes are 0 (unlikely)
    norm_contact = df_out['contact_attempts'] / max_contact if max_contact > 0 else df_out['contact_attempts'] * 0.0
    norm_adjust = df_out['payment_adjustments'] / max_adjust if max_adjust > 0 else df_out['payment_adjustments'] * 0.0
    
    admin_intensity = (norm_contact + norm_adjust) / 2.0
    
    # 3. Apply post-hoc adjustment
    # If admin-only, discount by (1.0 - 0.60 * admin_intensity). Otherwise, keep score intact.
    df_out['adjusted_priority_score'] = np.where(
        admin_only_mask,
        df_out['priority_score'] * (1.0 - 0.60 * admin_intensity),
        df_out['priority_score']
    )
    
    # Keep score bounded between [0, 1]
    df_out['adjusted_priority_score'] = df_out['adjusted_priority_score'].clip(0.0, 1.0)
    
    return df_out
