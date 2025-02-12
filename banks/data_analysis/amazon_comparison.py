import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def compare_with_without_amazon():
    """Generate comparison plots showing historical trends with and without Amazon deals"""
    data_dir = Path(__file__).parent.parent / 'data'
    output_dir = Path(__file__).parent.parent / 'analysis_output'
    output_dir.mkdir(exist_ok=True)
    
    # Load raw data
    jpm_data = pd.read_csv(data_dir / "money_saved_JPM2025.csv")
    svb_data = pd.read_csv(data_dir / "money_saved_svb2024.csv")
    
    # Convert dates
    jpm_data['date'] = pd.to_datetime(jpm_data['Offer redeemed on'], dayfirst=True)
    svb_data['date'] = pd.to_datetime(svb_data['Offer redeemed on'], dayfirst=False)
    
    # Convert savings amounts
    jpm_data['savings_amount'] = pd.to_numeric(jpm_data['Estimated Value'].str.replace('$', '').str.replace(',', ''), errors='coerce')
    svb_data['savings_amount'] = pd.to_numeric(svb_data['Estimated Value'].str.replace('$', '').str.replace(',', ''), errors='coerce')
    
    # Filter dates
    jpm_start_date = pd.Timestamp('2025-01-01')
    svb_start_date = pd.Timestamp('2024-01-01')
    current_date = pd.Timestamp('2025-02-06')
    
    jpm_data = jpm_data[
        (jpm_data['date'] >= jpm_start_date) & 
        (jpm_data['date'] <= current_date)
    ]
    svb_data = svb_data[
        (svb_data['date'] >= svb_start_date) & 
        (svb_data['date'] <= current_date)
    ]
    
    # Filter internal bank domains
    jpm_data = jpm_data[~jpm_data['Redeemer Domain'].str.contains('jpmorgan|chase', case=False, na=False)]
    svb_data = svb_data[~svb_data['Redeemer Domain'].str.contains('svb', case=False, na=False)]
    
    # Create monthly stats with and without Amazon
    def get_monthly_stats(df, include_amazon=True):
        if not include_amazon:
            df = df[~df['Name of offer'].str.contains('AWS', case=False, na=False)]
        df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
        monthly_totals = df.groupby('month')['savings_amount'].sum()
        monthly_medians = df.groupby('month')['savings_amount'].median()
        return monthly_totals, monthly_medians
    
    # Get stats for both scenarios
    jpm_totals_with, jpm_medians_with = get_monthly_stats(jpm_data, include_amazon=True)
    jpm_totals_without, jpm_medians_without = get_monthly_stats(jpm_data, include_amazon=False)
    svb_totals_with, svb_medians_with = get_monthly_stats(svb_data, include_amazon=True)
    svb_totals_without, svb_medians_without = get_monthly_stats(svb_data, include_amazon=False)
    
    # Create comparison plots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
    
    def format_month(m):
        return m.strftime('%b %Y')
    
    # Plot total monthly savings comparison
    svb_months = [format_month(m.to_timestamp()) for m in svb_totals_with.index]
    jpm_months = [format_month(m.to_timestamp()) for m in jpm_totals_with.index]
    
    # SVB lines
    ax1.plot(svb_months, svb_totals_with.values, 
            label='SVB with Amazon', color='blue', marker='o', linestyle='-', markersize=8, linewidth=2)
    ax1.plot(svb_months, svb_totals_without.values,
            label='SVB without Amazon', color='blue', marker='s', linestyle='--', markersize=8, linewidth=2)
    
    # JPM lines
    ax1.plot(jpm_months, jpm_totals_with.values,
            label='JPM with Amazon', color='red', marker='o', linestyle='-', markersize=8, linewidth=2)
    ax1.plot(jpm_months, jpm_totals_without.values,
            label='JPM without Amazon', color='red', marker='s', linestyle='--', markersize=8, linewidth=2)
    
    ax1.set_title('Total Monthly Savings Comparison', fontsize=14, pad=20)
    ax1.set_xlabel('Month', fontsize=12)
    ax1.set_ylabel('Total Monthly Savings ($)', fontsize=12)
    ax1.tick_params(axis='x', rotation=45)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Plot median savings comparison
    ax2.plot(svb_months, svb_medians_with.values,
            label='SVB with Amazon', color='blue', marker='o', linestyle='-', markersize=8, linewidth=2)
    ax2.plot(svb_months, svb_medians_without.values,
            label='SVB without Amazon', color='blue', marker='s', linestyle='--', markersize=8, linewidth=2)
    
    ax2.plot(jpm_months, jpm_medians_with.values,
            label='JPM with Amazon', color='red', marker='o', linestyle='-', markersize=8, linewidth=2)
    ax2.plot(jpm_months, jpm_medians_without.values,
            label='JPM without Amazon', color='red', marker='s', linestyle='--', markersize=8, linewidth=2)
    
    ax2.set_title('Median Monthly Savings Comparison', fontsize=14, pad=20)
    ax2.set_xlabel('Month', fontsize=12)
    ax2.set_ylabel('Median Monthly Savings ($)', fontsize=12)
    ax2.tick_params(axis='x', rotation=45)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    # Format y-axis labels with dollar signs and commas
    for ax in [ax1, ax2]:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${int(x):,}'))
    
    plt.tight_layout()
    plt.savefig(output_dir / 'amazon_comparison.png', bbox_inches='tight', dpi=300, format='png', facecolor='white')
    plt.close()
    
    # Print statistics
    print("\nMonthly Savings Statistics:")
    print("\nSVB:")
    print(f"Average monthly total with Amazon: ${svb_totals_with.mean():,.2f}")
    print(f"Average monthly total without Amazon: ${svb_totals_without.mean():,.2f}")
    print(f"Average monthly median with Amazon: ${svb_medians_with.mean():,.2f}")
    print(f"Average monthly median without Amazon: ${svb_medians_without.mean():,.2f}")
    
    print("\nJPM:")
    print(f"Average monthly total with Amazon: ${jpm_totals_with.mean():,.2f}")
    print(f"Average monthly total without Amazon: ${jpm_totals_without.mean():,.2f}")
    print(f"Average monthly median with Amazon: ${jpm_medians_with.mean():,.2f}")
    print(f"Average monthly median without Amazon: ${jpm_medians_without.mean():,.2f}")

if __name__ == "__main__":
    compare_with_without_amazon()
