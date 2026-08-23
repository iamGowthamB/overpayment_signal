"""
Fairness and Governance Analysis Module for The Overpayment Signal.
Provides functions to evaluate representation ratios, priority score averages,
and group representation metrics across demographic subgroups.
"""

import pandas as pd
import numpy as np

def analyze_fairness(scored_path: str, top20_path: str = None) -> pd.DataFrame:
    """
    Analyzes demographic representation between the overall population and the Top 20 prioritized cases.
    
    Parameters:
    -----------
    scored_path : str
        Path to data/processed/scored_cases.csv
    top20_path : str, optional
        Path to data/processed/top20_cases.csv. If None, the Top 20 will be extracted
        directly from the head of scored_cases.csv.
        
    Returns:
    --------
    pd.DataFrame
        Consolidated fairness report containing:
        demographic_field, group, population_count, population_percentage,
        top20_count, top20_percentage, representation_ratio, average_priority_score
    """
    # 1. Load scored cases
    df_scored = pd.read_csv(scored_path)
    
    # 2. Extract Top 20 cases
    if top20_path is not None and os.path.exists(top20_path):
        df_top20 = pd.read_csv(top20_path)
    else:
        df_top20 = df_scored.head(20).copy()
        
    demographic_fields = ['district', 'age_band', 'language_preference', 'tenure']
    reports = []
    
    # 3. Calculate statistics for each demographic category
    for col in demographic_fields:
        if col not in df_scored.columns:
            raise ValueError(f"Demographic column '{col}' not found in scored dataset")
            
        # Group population stats
        pop_counts = df_scored.groupby(col).size()
        pop_pcts = (pop_counts / len(df_scored)) * 100
        
        # Group Top 20 stats
        # Reindexing ensures all groups from the population are accounted for in the Top 20 stats
        t20_counts = df_top20.groupby(col).size().reindex(pop_counts.index, fill_value=0)
        t20_pcts = (t20_counts / len(df_top20)) * 100
        
        # Average priority score in overall population
        avg_scores = df_scored.groupby(col)['priority_score'].mean()
        
        # Calculate representation ratios: top20_percentage / population_percentage
        rep_ratios = t20_pcts / pop_pcts
        
        # Build category report
        cat_df = pd.DataFrame({
            'demographic_field': col,
            'group': pop_counts.index,
            'population_count': pop_counts.values,
            'population_percentage': pop_pcts.values,
            'top20_count': t20_counts.values,
            'top20_percentage': t20_pcts.values,
            'representation_ratio': rep_ratios.values,
            'average_priority_score': avg_scores.reindex(pop_counts.index).values
        })
        
        reports.append(cat_df)
        
    # Combine reports
    report_df = pd.concat(reports, ignore_index=True)
    
    # Handle possible division anomalies (just in case)
    report_df['representation_ratio'] = report_df['representation_ratio'].fillna(0.0)
    
    return report_df
