import pandas as pd
import numpy as np
from pathlib import Path

class BankSavingsAnalyzer:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.jpm_data = None
        self.svb_data = None
        self.jpm_start_date = pd.Timestamp('2025-01-01')
        self.svb_start_date = pd.Timestamp('2024-01-01')
        self.current_date = pd.Timestamp('2025-02-06')  # Current date from metadata
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
    
    def calculate_bank_stats(self, df, bank_name):
        """Calculate statistics for a given bank's dataset"""
        stats = {
            'bank_name': bank_name,
            'total_savings': df['savings_amount'].sum(),
            'avg_savings_per_redemption': df['savings_amount'].mean(),
            'median_savings_per_redemption': df['savings_amount'].median(),
            'min_savings': df['savings_amount'].min(),
            'max_savings': df['savings_amount'].max(),
            'unique_companies': df['company'].nunique(),
            'unique_offers': df['offer_id'].nunique(),
            'total_redemptions': len(df),  # Total number of deal redemptions
        }
        
        # Calculate average and median per company
        company_savings = df.groupby('company')['savings_amount'].sum()
        stats['avg_savings_per_company'] = company_savings.mean()
        stats['median_savings_per_company'] = company_savings.median()
        
        # Calculate redemptions per company
        company_redemptions = df.groupby('company').size()
        stats['avg_redemptions_per_company'] = company_redemptions.mean()
        
        # Get top 10 companies
        top_companies = df.groupby('company')['savings_amount'].sum().sort_values(ascending=False).head(10)
        stats['top_10_companies'] = top_companies.to_dict()
        
        return stats
    
    def get_all_stats(self):
        """Get statistics for both banks"""
        jpm_stats = self.calculate_bank_stats(self.jpm_data, 'JPM')
        svb_stats = self.calculate_bank_stats(self.svb_data, 'SVB')
        return {'JPM': jpm_stats, 'SVB': svb_stats}
    
    def predict_annual_savings(self, num_clients, company_types, engagement_level):
        """
        Predict annual savings based on input parameters
        
        Parameters:
        -----------
        num_clients : int
            Number of clients (up to 3 million)
        company_types : list
            List containing 'startup' and/or 'sme'
        engagement_level : str
            One of 'rarely', 'often', 'frequently'
        """
        # Calculate actual savings per client per year from historical data, adjusting for engagement levels
        
        # SVB data (41,000 clients, 7.7M annual, medium/often engagement)
        svb_annual_per_client = 7.7e6 / 41000  # ~$188 per client per year
        # Adjust SVB data up to 'frequent' baseline for fair comparison
        svb_frequent_baseline = svb_annual_per_client / 1.0 * 1.5  # Convert from 'often' to 'frequent' baseline
        
        # JPM data (5,000 clients, 1.7M monthly = 20.4M annual, high/frequent engagement)
        jpm_annual_per_client = 20.4e6 / 5000  # ~$4,080 per client per year
        # JPM is already at 'frequent' engagement level, no adjustment needed
        
        # Use weighted average as baseline (now both at 'frequent' engagement level)
        total_clients = 41000 + 5000
        base_annual_per_client_frequent = (svb_frequent_baseline * 41000 + jpm_annual_per_client * 5000) / total_clients
        
        # Engagement level multipliers relative to 'frequent' baseline
        engagement_multipliers = {
            'rarely': 0.33,   # 1/3 of frequent engagement
            'often': 0.67,    # 2/3 of frequent engagement
            'frequently': 1.0  # Baseline is now at 'frequent' level
        }
        
        # Calculate base prediction (already at 'frequent' baseline)
        base_prediction = base_annual_per_client_frequent * num_clients * engagement_multipliers[engagement_level]
        
        # Adjust for company types
        if len(company_types) == 2:  # Both startups and SMEs
            startup_prediction = base_prediction * 0.5  # 50% startups
            sme_prediction = base_prediction * 0.5 * 0.7  # 50% SMEs with 30% less savings
            total_prediction = startup_prediction + sme_prediction
        elif 'sme' in company_types:
            total_prediction = base_prediction * 0.7  # SMEs make 30% less
        else:  # startups only
            total_prediction = base_prediction
        
        # Add a scaling factor that reduces the per-client savings as the number of clients increases
        # This reflects that it's harder to maintain the same level of engagement with more clients
        scaling_factor = 1.0 / (1 + np.log10(num_clients / 1000))
        total_prediction *= scaling_factor
        
        return {
            'total_annual_savings': round(total_prediction, 2),
            'avg_savings_per_company': round(total_prediction / num_clients, 2),
            'monthly_savings': round(total_prediction / 12, 2)
        }
    
    def get_top_offers(self, num_clients, company_types, engagement_level):
        """Get top 10 potential offers based on historical data and selected parameters"""
        # Combine data from both banks
        combined_data = pd.concat([
            self.jpm_data[['offer_id', 'savings_amount', 'company', 'Name of offer']],
            self.svb_data[['offer_id', 'savings_amount', 'company', 'Name of offer']]
        ])
        
        # Calculate offer statistics
        offer_stats = combined_data.groupby(['offer_id', 'Name of offer']).agg({
            'savings_amount': ['mean', 'count', 'sum'],
            'company': 'nunique'
        }).reset_index()
        
        # Flatten column names
        offer_stats.columns = ['offer_id', 'offer_name', 'avg_savings', 'usage_count', 'total_savings', 'unique_companies']
        
        # Calculate score based on savings and popularity
        offer_stats['score'] = (
            offer_stats['avg_savings'] * 
            np.log1p(offer_stats['usage_count']) * 
            np.log1p(offer_stats['unique_companies'])
        )
        
        # Engagement level multipliers
        engagement_multipliers = {
            'rarely': 0.5,
            'often': 1.0,  # SVB level
            'frequently': 1.5  # JPM level
        }
        
        # Calculate base multiplier from number of clients (assuming current data is based on average of 10,000 clients)
        client_multiplier = num_clients / 10000
        
        # Apply client and engagement multipliers
        offer_stats['avg_savings'] *= client_multiplier * engagement_multipliers[engagement_level]
        
        # Adjust for company types
        if len(company_types) == 2:  # Both startups and SMEs
            startup_offers = offer_stats.copy()
            sme_offers = offer_stats.copy()
            sme_offers['avg_savings'] *= 0.7  # SMEs make 30% less
            
            # Combine with 50-50 split
            offer_stats['avg_savings'] = (
                startup_offers['avg_savings'] * 0.5 + 
                sme_offers['avg_savings'] * 0.5
            )
        elif 'sme' in company_types:
            offer_stats['avg_savings'] *= 0.7  # SMEs make 30% less
        
        # Update score based on adjusted savings
        offer_stats['score'] = (
            offer_stats['avg_savings'] * 
            np.log1p(offer_stats['usage_count']) * 
            np.log1p(offer_stats['unique_companies'])
        )
        
        # Get top 10 offers
        top_offers = offer_stats.nlargest(10, 'score')[[
            'offer_name', 'avg_savings'
        ]].round(2)
        
        # Calculate percentage of total savings, handling NaN values
        total_savings = offer_stats['avg_savings'].fillna(0).sum()
        if total_savings > 0:  # Avoid division by zero
            top_offers['percentage'] = (top_offers['avg_savings'].fillna(0) / total_savings * 100).round(2)
        else:
            # If no savings data, distribute percentages evenly
            top_offers['percentage'] = (100.0 / len(top_offers)).round(2)
        
        return top_offers
