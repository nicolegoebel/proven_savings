import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import json
from datetime import datetime, timedelta

class SavingsModelVisualizer:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.static_dir = Path(__file__).parent.parent / 'static'
        self.static_dir.mkdir(exist_ok=True)
        self.jpm_start_date = pd.Timestamp('2025-01-01')
        self.svb_start_date = pd.Timestamp('2024-01-01')
        self.current_date = pd.Timestamp('2025-02-05')  # Current date from metadata
        self.load_and_prepare_data()
        
    def load_and_prepare_data(self):
        """Load and prepare data with proper date handling and filtering"""
        # Load raw data
        self.jpm_data = pd.read_csv(self.data_dir / "money_saved_JPM2025.csv")
        self.svb_data = pd.read_csv(self.data_dir / "money_saved_svb2024.csv")
        
        # Filter out JPM and Chase emails
        jpm_filter = ~self.jpm_data['Redeemer Domain'].str.contains('jpmorgan|chase', case=False, na=False)
        svb_filter = ~self.svb_data['Redeemer Domain'].str.contains('jpmorgan|chase', case=False, na=False)
        
        self.jpm_data = self.jpm_data[jpm_filter].copy()
        self.svb_data = self.svb_data[svb_filter].copy()
        
        # Convert dates - JPM uses day first (UK format), SVB uses month first (US format)
        self.jpm_data['date'] = pd.to_datetime(self.jpm_data['Offer redeemed on'], dayfirst=True)
        self.svb_data['date'] = pd.to_datetime(self.svb_data['Offer redeemed on'], dayfirst=False)
        
        # Filter by valid date ranges
        self.jpm_data = self.jpm_data[
            (self.jpm_data['date'] >= self.jpm_start_date) & 
            (self.jpm_data['date'] <= self.current_date)
        ]
        self.svb_data = self.svb_data[
            (self.svb_data['date'] >= self.svb_start_date) & 
            (self.svb_data['date'] <= self.current_date)
        ]
        
        # Prepare columns for analysis
        for df in [self.jpm_data, self.svb_data]:
            df['savings_amount'] = pd.to_numeric(df['Estimated Value'].str.replace('$', '').str.replace(',', ''), errors='coerce')
            df['company'] = df['Offer redeemed by']
            df['offer_id'] = df['Name of offer']
        

    
    def generate_prediction_surface(self):
        """Generate prediction surface with linear growth"""
        # Create grid of values with focus on lower range
        num_companies = np.concatenate([
            np.linspace(200, 1000, 20),  # More points in lower range
            np.linspace(1000, 2000000, 30)  # Fewer points in higher range
        ])
        
        # Define base savings per client and engagement multipliers
        base_savings_per_client = 1000  # $1000 base savings per client
        engagement_multipliers = {
            'frequently': 1.5,
            'often': 1.0,
            'rarely': 0.5
        }
        
        predictions = {}
        
        # Create static plot
        plt.figure(figsize=(12, 6))
        colors = {'frequently': '#4BC0C0', 'often': '#FF9F40', 'rarely': '#FF6384'}
        
        for level, multiplier in engagement_multipliers.items():
            # Calculate linear savings
            savings = num_companies * base_savings_per_client * multiplier
            
            predictions[level] = {
                'companies': num_companies.tolist(),
                'savings': savings.tolist()
            }
            
            # Add to static plot
            plt.plot(num_companies, savings, label=level.capitalize(),
                     color=colors[level])
        
        plt.title('Projected Annual Savings by Number of Clients')
        plt.xlabel('Number of Clients')
        plt.ylabel('Annual Savings ($)')
        plt.grid(True, alpha=0.3)
        plt.legend(loc='upper left')
        
        # Format axes
        plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
        plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${int(x):,}'))
        
        # Save static plot
        plt.savefig(self.static_dir / 'savings_vs_clients.png', bbox_inches='tight', dpi=300)
        plt.close()
        
        # Save predictions for JavaScript visualization
        with open(self.static_dir / 'prediction_data.json', 'w') as f:
            json.dump(predictions, f)
    
    def plot_historical_trends(self):
        """Plot historical savings trends in two separate plots for total and median savings"""
        # Calculate SVB monthly stats
        self.svb_data['month'] = self.svb_data['date'].dt.to_period('M')
        svb_monthly_totals = self.svb_data.groupby('month')['savings_amount'].sum()
        svb_monthly_medians = self.svb_data.groupby('month')['savings_amount'].median()
        
        # Calculate JPM monthly stats
        self.jpm_data['month'] = self.jpm_data['date'].dt.to_period('M')
        jpm_monthly_totals = self.jpm_data.groupby('month')['savings_amount'].sum()
        jpm_monthly_medians = self.jpm_data.groupby('month')['savings_amount'].median()
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot total savings
        ax1.plot(range(len(svb_monthly_totals)), svb_monthly_totals.values, 
                label='SVB', color='blue', marker='o')
        ax1.plot(range(len(jpm_monthly_totals)), jpm_monthly_totals.values, 
                label='JPM', color='red', marker='o')
        ax1.set_title('Total Monthly Savings')
        ax1.set_ylabel('Total Savings ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot median savings
        ax2.plot(range(len(svb_monthly_medians)), svb_monthly_medians.values, 
                label='SVB', color='blue', marker='o')
        ax2.plot(range(len(jpm_monthly_medians)), jpm_monthly_medians.values, 
                label='JPM', color='red', marker='o')
        ax2.set_title('Median Savings per Deal')
        ax2.set_ylabel('Median Savings ($)')
        ax2.set_xlabel('Month')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Format y-axis labels
        for ax in [ax1, ax2]:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${int(x):,}'))
        
        plt.tight_layout()
        plt.savefig(self.static_dir / 'historical_trends.png', bbox_inches='tight', dpi=300)
        plt.close()
        

        ax1.plot(svb_monthly_totals.index.astype(str), svb_monthly_totals,
                label='SVB Total Savings', marker='o', color='blue')
        ax1.plot(jpm_monthly_totals.index.astype(str), jpm_monthly_totals,
                label='JPM Total Savings', marker='o', color='red')
        
        # Project JPM totals using SVB's growth rate
        if len(jpm_monthly_totals) > 0 and len(svb_monthly_totals) > 1:
            # Calculate SVB's average monthly growth rate
            svb_growth_rates = svb_monthly_totals.pct_change().dropna()
            avg_monthly_growth = 1 + svb_growth_rates.mean()
            
            # Project remaining months
            remaining_months = 12 - len(jpm_monthly_totals)
            if remaining_months > 0:
                last_total = jpm_monthly_totals.iloc[-1]
                projected_totals = [last_total * (avg_monthly_growth ** (i+1)) 
                                  for i in range(remaining_months)]
                
                # Create month labels for projections
                last_month = jpm_monthly_totals.index[-1]
                projected_months = [pd.Period(last_month) + i + 1 
                                  for i in range(remaining_months)]
                
                # Plot projections
                ax1.plot([last_month.strftime('%Y-%m')] + 
                        [m.strftime('%Y-%m') for m in projected_months],
                        [last_total] + projected_totals,
                        label='JPM Projected', linestyle='--', color='red')
                
                # Add confidence interval
                lower_bound = np.array([last_total] + projected_totals) * 0.8
                upper_bound = np.array([last_total] + projected_totals) * 1.2
                ax1.fill_between(
                    [last_month.strftime('%Y-%m')] + 
                    [m.strftime('%Y-%m') for m in projected_months],
                    lower_bound, upper_bound,
                    color='red', alpha=0.1)
        
        ax1.set_title('Total Monthly Savings')
        ax1.set_xlabel('Month')
        ax1.set_ylabel('Total Monthly Savings ($)')
        ax1.tick_params(axis='x', rotation=45)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Median Savings per Deal
        ax2.plot(svb_monthly_medians.index.astype(str), svb_monthly_medians,
                label='SVB Median per Deal', marker='s', color='blue')
        ax2.plot(jpm_monthly_medians.index.astype(str), jpm_monthly_medians,
                label='JPM Median per Deal', marker='s', color='red')
        
        # Project JPM medians
        if len(jpm_monthly_medians) > 0:
            # Use same growth rate as totals but with smaller factor
            remaining_months = 12 - len(jpm_monthly_medians)
            if remaining_months > 0:
                last_median = jpm_monthly_medians.iloc[-1]
                projected_medians = [last_median * (avg_monthly_growth ** (i+1)) 
                                   for i in range(remaining_months)]
                
                ax2.plot([last_month.strftime('%Y-%m')] + 
                        [m.strftime('%Y-%m') for m in projected_months],
                        [last_median] + projected_medians,
                        label='JPM Projected', linestyle='--', color='red')
                
                # Add confidence interval
                lower_bound = np.array([last_median] + projected_medians) * 0.8
                upper_bound = np.array([last_median] + projected_medians) * 1.2
                ax2.fill_between(
                    [last_month.strftime('%Y-%m')] + 
                    [m.strftime('%Y-%m') for m in projected_months],
                    lower_bound, upper_bound,
                    color='red', alpha=0.1)
        
        ax2.set_title('Median Savings per Deal')
        ax2.set_xlabel('Month')
        ax2.set_ylabel('Median Savings per Deal ($)')
        ax2.tick_params(axis='x', rotation=45)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.static_dir / 'historical_trends.png', bbox_inches='tight', dpi=300)
        plt.close()
        
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        plt.savefig(self.static_dir / 'historical_trends.png', bbox_inches='tight', dpi=300)
        plt.close()
    
    def plot_company_distribution(self):
        """Plot distribution of savings across companies"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # SVB distribution
        svb_company_savings = self.svb_data.groupby('company')['savings_amount'].sum()
        sns.histplot(data=svb_company_savings, ax=ax1, bins=20, color='blue', alpha=0.6)
        ax1.set_title('SVB Savings Distribution\n(Jan 2024 - Present)')
        ax1.set_xlabel('Total Savings per Company ($)')
        ax1.set_ylabel('Number of Companies')
        
        # Add mean and median lines for SVB
        svb_mean = svb_company_savings.mean()
        svb_median = svb_company_savings.median()
        ax1.axvline(svb_mean, color='red', linestyle='--', label=f'Mean: ${svb_mean:,.0f}')
        ax1.axvline(svb_median, color='green', linestyle='--', label=f'Median: ${svb_median:,.0f}')
        ax1.legend()
        
        # JPM distribution
        jpm_company_savings = self.jpm_data.groupby('company')['savings_amount'].sum()
        sns.histplot(data=jpm_company_savings, ax=ax2, bins=20, color='red', alpha=0.6)
        ax2.set_title('JPM Savings Distribution\n(Jan 2025 - Present)')
        ax2.set_xlabel('Total Savings per Company ($)')
        ax2.set_ylabel('Number of Companies')
        
        # Add mean and median lines for JPM
        jpm_mean = jpm_company_savings.mean()
        jpm_median = jpm_company_savings.median()
        ax2.axvline(jpm_mean, color='red', linestyle='--', label=f'Mean: ${jpm_mean:,.0f}')
        ax2.axvline(jpm_median, color='green', linestyle='--', label=f'Median: ${jpm_median:,.0f}')
        ax2.legend()
        
        plt.suptitle('Distribution of Savings Across Companies', y=1.05, fontsize=14)
        plt.tight_layout()
        plt.savefig(self.static_dir / 'company_distribution.png', bbox_inches='tight', dpi=300)
        plt.close()
    
    def generate_all_visualizations(self):
        """Generate all visualizations"""
        self.generate_prediction_surface()
        self.plot_historical_trends()
        self.plot_company_distribution()
