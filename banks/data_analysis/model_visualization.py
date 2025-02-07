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
        
    def prepare_training_data(self):
        """Prepare training data for the model"""
        # Aggregate data by company and month with projections for JPM
        svb_monthly = self.aggregate_monthly_data(self.svb_data, 'SVB')
        jpm_monthly = self.aggregate_monthly_data(self.jpm_data, 'JPM')
        
        # Create features
        svb_features = self.create_features(svb_monthly, 'often')
        jpm_features = self.create_features(jpm_monthly, 'frequently')
        
        # Add confidence weights - full weight for SVB, lower weights for projected JPM months
        svb_features['confidence'] = 1.0
        jpm_features['confidence'] = np.linspace(1.0, 0.7, len(jpm_features))
        
        return pd.concat([svb_features, jpm_features])
    
    def aggregate_monthly_data(self, df, bank_name):
        """Aggregate savings data by month and project annual estimates for JPM"""
        # Create month periods
        df['month'] = df['date'].dt.to_period('M')
        monthly_data = df.groupby(['month', 'company'])['savings_amount'].agg(['sum', 'count']).reset_index()
        
        if bank_name == 'JPM':
            # Calculate average daily rate from the first month
            first_month_data = df[df['date'].dt.month == self.jpm_start_date.month]
            avg_daily_savings = first_month_data['savings_amount'].sum() / len(first_month_data['date'].dt.day.unique())
            
            # Project remaining months of 2025
            remaining_months = 12 - (self.current_date.month - self.jpm_start_date.month + 1)
            
            if remaining_months > 0:
                # Create growth factors for remaining months (higher growth initially, then stabilizing)
                growth_factors = np.linspace(1.2, 1.0, remaining_months + 1)[1:]
                
                # Project each remaining month
                for i in range(remaining_months):
                    projected_month = self.current_date + pd.DateOffset(months=i+1)
                    days_in_month = pd.Period(projected_month, freq='M').days_in_month
                    
                    # Project savings with growth factor
                    projected_savings = avg_daily_savings * days_in_month * growth_factors[i]
                    
                    # Add to monthly data
                    for company in monthly_data['company'].unique():
                        new_row = {
                            'month': pd.Period(projected_month, freq='M'),
                            'company': company,
                            'sum': projected_savings / len(monthly_data['company'].unique()),
                            'count': monthly_data.groupby('company')['count'].mean().mean()
                        }
                        monthly_data = pd.concat([monthly_data, pd.DataFrame([new_row])], ignore_index=True)
        
        if bank_name == 'JPM':
            # Calculate monthly averages per company
            avg_monthly = monthly_data.groupby('company')['sum'].mean()
            
            # Project for 12 months with growth factors
            # Assuming higher growth in early months, stabilizing later
            growth_factors = np.array([1.2, 1.15, 1.1, 1.08, 1.06, 1.05, 1.04, 1.03, 1.02, 1.01, 1.0, 1.0])
            
            projected_months = []
            for month in range(12):
                month_data = monthly_data.copy()
                month_data['sum'] = month_data['sum'] * growth_factors[month]
                month_data['month'] = f'2025-{month+1:02d}'
                projected_months.append(month_data)
            
            monthly_data = pd.concat(projected_months)
        
        return monthly_data
    
    def create_features(self, df, engagement_level):
        """Create feature matrix for modeling"""
        engagement_map = {'rarely': 0, 'often': 1, 'frequently': 2}
        df['engagement_level'] = engagement_map[engagement_level]
        df['num_companies'] = df.groupby('month')['company'].transform('nunique')
        return df
    
    def train_model(self):
        """Train a polynomial regression model with confidence weights and smoothing"""
        data = self.prepare_training_data()
        
        # Create feature matrix
        X = data[['num_companies', 'engagement_level']]
        y = data['sum']
        sample_weights = data['confidence']  # Use confidence as sample weights
        
        # Add a minimum threshold for predictions
        min_savings = data['sum'].min() * 0.5  # Set minimum to half of smallest observed value
        
        # Create polynomial features with higher degree for better fit
        poly = PolynomialFeatures(degree=3)
        X_poly = poly.fit_transform(X)
        
        # Fit model with sample weights
        model = LinearRegression()
        model.fit(X_poly, y, sample_weight=sample_weights)
        
        return model, poly, min_savings
    
    def generate_prediction_surface(self):
        """Generate prediction surface for visualization with monotonic savings"""
        model, poly, min_savings = self.train_model()
        
        # Create evenly spaced grid for number of companies
        num_points = 50  # Number of points to generate
        companies = np.linspace(0, 2000000, num_points)
        
        engagement_levels = np.array([0, 1, 2])  # rarely, often, frequently
        engagement_names = ['rarely', 'often', 'frequently']
        
        predictions = {}
        prev_level_pred = None  # Store previous level predictions for monotonicity
        
        for level in engagement_levels:
            # Generate predictions
            X = np.column_stack([companies, np.full_like(companies, level)])
            X_poly = poly.transform(X)
            pred = model.predict(X_poly)
            
            # Ensure predictions are monotonically increasing
            for i in range(1, len(pred)):
                pred[i] = max(pred[i], pred[i-1])
            
            # Ensure higher engagement levels have higher savings
            if prev_level_pred is not None:
                pred = np.maximum(pred, prev_level_pred * 1.1)  # 10% higher than previous level
            
            prev_level_pred = pred.copy()
            
            # Store results
            predictions[engagement_names[int(level)]] = {
                'companies': companies.tolist(),
                'savings': pred.tolist()
            }
        
        # Save predictions for JavaScript visualization
        with open(self.static_dir / 'prediction_data.json', 'w') as f:
            json.dump(predictions, f)
    
    def plot_historical_trends(self):
        """Plot historical and projected savings trends with monthly medians"""
        plt.figure(figsize=(15, 7))
        
        # Plot SVB data
        svb_monthly = self.aggregate_monthly_data(self.svb_data, 'SVB')
        svb_totals = svb_monthly.groupby('month')['sum'].sum()
        svb_medians = svb_monthly.groupby(['month'])['sum'].median()
        svb_months = range(len(svb_totals))
        
        # Plot SVB total and median trends
        plt.plot(svb_months, svb_totals,
                label='SVB Total Savings', marker='o', color='blue')
        plt.plot(svb_months, svb_medians,
                label='SVB Median Company Savings', marker='s', color='lightblue')
        
        # Plot JPM data
        jpm_monthly = self.aggregate_monthly_data(self.jpm_data, 'JPM')
        jpm_totals = jpm_monthly.groupby('month')['sum'].sum()
        jpm_medians = jpm_monthly.groupby(['month'])['sum'].median()
        
        # Separate actual and projected data
        actual_months = (self.current_date.month - self.jpm_start_date.month + 1)
        jpm_actual_totals = jpm_totals[:actual_months]
        jpm_projected_totals = jpm_totals[actual_months-1:]
        jpm_actual_medians = jpm_medians[:actual_months]
        jpm_projected_medians = jpm_medians[actual_months-1:]
        
        # Plot actual JPM data
        plt.plot(range(len(jpm_actual_totals)), jpm_actual_totals,
                label='JPM Total Savings', marker='o', color='red')
        plt.plot(range(len(jpm_actual_medians)), jpm_actual_medians,
                label='JPM Median Company Savings', marker='s', color='lightcoral')
        
        # Plot projected JPM data
        projected_months = range(len(jpm_actual_totals)-1, len(jpm_totals))
        plt.plot(projected_months, jpm_projected_totals,
                label='JPM Total Savings (Projected)', linestyle='--', color='red')
        plt.plot(projected_months, jpm_projected_medians,
                label='JPM Median Company Savings (Projected)', linestyle='--', color='lightcoral')
        
        # Add confidence intervals for projections
        # For total savings
        lower_bound_total = jpm_projected_totals * 0.8
        upper_bound_total = jpm_projected_totals * 1.2
        plt.fill_between(projected_months, lower_bound_total, upper_bound_total,
                        color='red', alpha=0.1, label='Total Savings Confidence Interval')
        
        # For median savings
        lower_bound_median = jpm_projected_medians * 0.8
        upper_bound_median = jpm_projected_medians * 1.2
        plt.fill_between(projected_months, lower_bound_median, upper_bound_median,
                        color='lightcoral', alpha=0.1, label='Median Savings Confidence Interval')
        
        plt.title('Bank Savings Trends (2024-2025)')
        plt.xlabel('Months Since Start')
        plt.ylabel('Total Monthly Savings ($)')
        
        # Add month labels
        all_months = pd.date_range(self.svb_start_date, self.jpm_start_date + pd.DateOffset(months=11), freq='ME')
        plt.xticks(range(len(all_months)), [d.strftime('%Y-%m') for d in all_months], rotation=45)
        
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
