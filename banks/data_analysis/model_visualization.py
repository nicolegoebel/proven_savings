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
        
        # Filter out internal bank and Amazon deals
        jpm_filter = ~(self.jpm_data['Redeemer Domain'].str.contains('jpmorgan|chase', case=False, na=False) | 
                      self.jpm_data['Name of offer'].str.contains('AWS', case=False, na=False))
        svb_filter = ~(self.svb_data['Redeemer Domain'].str.contains('svb', case=False, na=False) | 
                      self.svb_data['Name of offer'].str.contains('AWS', case=False, na=False))
        
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
        """Generate prediction surface with linear growth based on SVB and JPM data"""
        # SVB benchmark (medium engagement): 7.7M annual savings with 41k clients
        svb_benchmark_clients = 41000
        svb_benchmark_savings = 7.7e6  # 7.7 million
        base_savings_per_client = svb_benchmark_savings / svb_benchmark_clients  # About $188 per client
        
        # JPM data (high engagement): 5000 clients, need to project annual from monthly
        jpm_clients = 5000
        jpm_monthly_savings = self.jpm_data['savings_amount'].sum()  # Total for first month
        jpm_projected_annual = jpm_monthly_savings * 12  # Simple annual projection
        
        # Create evenly spaced points for linear visualization
        num_companies = np.linspace(200, 2000000, 50)  # Extend range to 2M clients
        
        # Define engagement multipliers relative to SVB's medium engagement
        engagement_multipliers = {
            'Frequently': 1.5,  # JPM's level (high engagement)
            'Often': 1.0,      # SVB's level (medium engagement)
            'Rarely': 0.5      # Low engagement
        }
        
        predictions = {}
        
        # Create static plot
        plt.figure(figsize=(12, 6))
        colors = {'Frequently': '#4BC0C0', 'Often': '#FF9F40', 'Rarely': '#FF6384'}
        linestyles = {'Frequently': '-', 'Often': '--', 'Rarely': ':'}
        
        # Add reference points
        plt.scatter([svb_benchmark_clients], [svb_benchmark_savings], 
                   color='blue', s=100, zorder=5,
                   label='SVB Actual (41k clients, medium engagement)')
        plt.scatter([jpm_clients], [jpm_projected_annual], 
                   color='red', s=100, zorder=5,
                   label='JPM Projected Annual (5k clients, high engagement)')
        
        for level, multiplier in engagement_multipliers.items():
            # Calculate linear savings
            savings = num_companies * base_savings_per_client * multiplier
            
            predictions[level.lower()] = {
                'companies': num_companies.tolist(),
                'savings': savings.tolist()
            }
            
            # Add to static plot with distinct line styles and markers
            plt.plot(num_companies, savings, 
                     label=f'{level}',
                     color=colors[level],
                     linestyle=linestyles[level],
                     linewidth=2,
                     marker='o',
                     markevery=5)
        
        plt.title('Projected Annual Savings by Number of Clients', fontsize=14, pad=20)
        plt.xlabel('Number of Clients', fontsize=12)
        plt.ylabel('Annual Savings ($)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend(loc='upper left', fontsize=10)
        
        # Format axes with linear scale
        ax = plt.gca()
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${int(x):,}'))
        
        # Ensure plot shows linear relationship clearly
        plt.xlim(0, 2000000)  # Set x-axis to 2M clients
        plt.ylim(0, max(savings) * 1.1)
        
        # Save static plot
        plt.tight_layout()
        plt.savefig(self.static_dir / 'savings_vs_clients.png', bbox_inches='tight', dpi=300, format='png', facecolor='white')
        plt.close()
        
        # Save predictions for JavaScript visualization
        with open(self.static_dir / 'prediction_data.json', 'w') as f:
            json.dump(predictions, f)
    
    def plot_historical_trends(self):
        """Plot historical savings trends in two separate plots for total and median savings"""
        # Calculate SVB monthly stats
        self.svb_data['month'] = pd.to_datetime(self.svb_data['date']).dt.to_period('M')
        svb_monthly_totals = self.svb_data.groupby('month')['savings_amount'].sum()
        svb_monthly_medians = self.svb_data.groupby('month')['savings_amount'].median()
        
        # Calculate JPM monthly stats
        self.jpm_data['month'] = pd.to_datetime(self.jpm_data['date']).dt.to_period('M')
        jpm_monthly_totals = self.jpm_data.groupby('month')['savings_amount'].sum()
        jpm_monthly_medians = self.jpm_data.groupby('month')['savings_amount'].median()
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
        
        # Format month labels
        def format_month(m):
            return m.strftime('%b %Y')
        
        # Plot 1: Total Monthly Savings
        svb_months = [format_month(m.to_timestamp()) for m in svb_monthly_totals.index]
        jpm_months = [format_month(m.to_timestamp()) for m in jpm_monthly_totals.index]
        
        # Plot actual data
        ax1.plot(svb_months, svb_monthly_totals.values, 
                label='SVB Actual', color='blue', marker='o', markersize=8, linewidth=2)
        ax1.plot(jpm_months, jpm_monthly_totals.values, 
                label='JPM Actual', color='red', marker='o', markersize=8, linewidth=2)
        
        # Project JPM totals
        if len(jpm_monthly_totals) > 0 and len(svb_monthly_totals) > 1:
            # Calculate average monthly growth rate from SVB data
            svb_growth_rates = svb_monthly_totals.pct_change().dropna()
            avg_monthly_growth = 1 + svb_growth_rates.mean()
            
            # Calculate the ratio between JPM and SVB monthly averages (excluding AWS)
            jpm_avg = jpm_monthly_totals.mean()
            svb_avg = svb_monthly_totals.mean()
            scale_factor = jpm_avg / svb_avg if svb_avg > 0 else 1.0
            
            # Adjust growth rate based on the scale factor
            adj_monthly_growth = 1 + (svb_growth_rates.mean() * scale_factor)
            
            # Project remaining months
            remaining_months = 12 - len(jpm_monthly_totals)
            if remaining_months > 0:
                last_total = jpm_monthly_totals.iloc[-1]
                projected_totals = [last_total * (adj_monthly_growth ** (i+1)) 
                                  for i in range(remaining_months)]
                
                # Create month labels for projections
                last_month = jpm_monthly_totals.index[-1]
                projected_months = [format_month((last_month + i + 1).to_timestamp()) 
                                  for i in range(remaining_months)]
                
                # Plot projections with confidence interval
                ax1.plot([format_month(last_month.to_timestamp())] + projected_months,
                        [last_total] + projected_totals,
                        label='JPM Projected', linestyle='--', color='red', 
                        linewidth=2, marker='s', markersize=6)
                
                # Add confidence interval
                # Wider confidence interval due to AWS removal uncertainty
                lower_bound = np.array([last_total] + projected_totals) * 0.7
                upper_bound = np.array([last_total] + projected_totals) * 1.3
                ax1.fill_between([format_month(last_month.to_timestamp())] + projected_months,
                                lower_bound, upper_bound,
                                color='red', alpha=0.1,
                                label='Confidence Interval (±20%)')
        
        ax1.set_title('Total Monthly Savings', fontsize=14, pad=20)
        ax1.set_xlabel('Month', fontsize=12)
        ax1.set_ylabel('Total Monthly Savings ($)', fontsize=12)
        ax1.tick_params(axis='x', rotation=45)
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # Calculate monthly averages
        svb_monthly_means = self.svb_data.groupby('month')['savings_amount'].mean()
        jpm_monthly_means = self.jpm_data.groupby('month')['savings_amount'].mean()
        
        # Plot 2: Median and Average Savings per Deal
        # Plot medians
        ax2.plot(svb_months, svb_monthly_medians.values, 
                label='SVB Median', color='blue', marker='s', markersize=8, linewidth=2)
        ax2.plot(jpm_months, jpm_monthly_medians.values, 
                label='JPM Median', color='red', marker='s', markersize=8, linewidth=2)
        
        # Plot averages (dashed lines)
        ax2.plot(svb_months, svb_monthly_means.values,
                label='SVB Average', color='blue', marker='o', markersize=6,
                linestyle='--', linewidth=2)
        ax2.plot(jpm_months, jpm_monthly_means.values,
                label='JPM Average', color='red', marker='o', markersize=6,
                linestyle='--', linewidth=2)
        
        # Project JPM medians
        if len(jpm_monthly_medians) > 0 and len(svb_monthly_totals) > 1:
            # Use same growth rate but with smaller factor for median projection
            remaining_months = 12 - len(jpm_monthly_medians)
            if remaining_months > 0:
                last_median = jpm_monthly_medians.iloc[-1]
                projected_medians = [last_median * (avg_monthly_growth ** (i+1)) 
                                   for i in range(remaining_months)]
                
                # Plot projections with confidence interval
                ax2.plot([format_month(last_month.to_timestamp())] + projected_months,
                        [last_median] + projected_medians,
                        label='JPM Projected', linestyle='--', color='red',
                        linewidth=2, marker='s', markersize=6)
                
                # Add confidence interval
                lower_bound = np.array([last_median] + projected_medians) * 0.8
                upper_bound = np.array([last_median] + projected_medians) * 1.2
                ax2.fill_between([format_month(last_month.to_timestamp())] + projected_months,
                                lower_bound, upper_bound,
                                color='red', alpha=0.1,
                                label='Confidence Interval (±20%)')
        
        ax2.set_title('Median and Average Savings per Deal', fontsize=14, pad=20)
        ax2.set_xlabel('Month', fontsize=12)
        ax2.set_ylabel('Median Savings per Deal ($)', fontsize=12)
        ax2.tick_params(axis='x', rotation=45)
        ax2.legend(fontsize=10)
        ax2.grid(True, alpha=0.3)
        
        # Format y-axis labels with dollar signs and commas
        for ax in [ax1, ax2]:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${int(x):,}'))
        
        plt.tight_layout()
        plt.savefig(self.static_dir / 'historical_trends.png', bbox_inches='tight', dpi=300, format='png', facecolor='white')
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
