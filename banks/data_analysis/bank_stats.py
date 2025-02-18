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
        # Base amount per client per year (calculated from SVB's actual data: $7.4M / 41,438 clients)
        base_amount = 178.58  # Base amount per client per year at SVB's engagement level
        
        # Engagement level multipliers
        engagement_multipliers = {
            'rarely': 1.0,     # SVB baseline engagement level
            'often': 1.03,    # JPM engagement level (+3%)
            'frequently': 1.05  # Projected high engagement level (+5%)
        }
        
        # Base calculation per client at given engagement level
        base_per_client = base_amount * engagement_multipliers[engagement_level]
        
        # Calculate total based on company types
        if len(company_types) == 2:  # Both startups and SMEs
            # All clients are startups, then add 30% more for SMEs
            startup_total = base_per_client * num_clients
            sme_additional = startup_total * 0.3  # Additional 30% from SMEs
            total = startup_total + sme_additional
        elif 'sme' in company_types:  # SMEs only
            # All clients are SMEs (70% of startup savings)
            total = base_per_client * num_clients * 0.7
        else:  # Startups only
            # All clients are startups (100%)
            total = base_per_client * num_clients
        
        return {
            'total_annual_savings': total,
            'monthly_savings': total / 12
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
            'rarely': 1.0,     # SVB baseline
            'often': 1.03,    # JPM level (+3%)
            'frequently': 1.05  # Projected high engagement (+5%)
        }
        
        # Calculate base multiplier from number of clients (SVB baseline: 41,438 clients)
        client_multiplier = num_clients / 41438  # Scale relative to SVB's client base
        
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

    def get_top_companies(self, bank='all', n=10):
        """Get top N companies by total savings for specified bank(s)"""
        def get_company_stats(df):
            # Group by company and calculate total and median savings
            stats = df.groupby('company').agg({
                'savings_amount': ['sum', 'median']
            }).reset_index()
            
            # Flatten column names
            stats.columns = ['company', 'total_savings', 'median_savings']
            
            # Sort by total savings and get top N
            return stats.nlargest(n, 'total_savings')
        
        if bank.upper() == 'JPM' or bank.upper() == 'ALL':
            jpm_top = get_company_stats(self.jpm_data)
            jpm_top['bank'] = 'JPM'
        
        if bank.upper() == 'SVB' or bank.upper() == 'ALL':
            svb_top = get_company_stats(self.svb_data)
            svb_top['bank'] = 'SVB'
        
        if bank.upper() == 'ALL':
            return pd.concat([jpm_top, svb_top])
        elif bank.upper() == 'JPM':
            return jpm_top
        elif bank.upper() == 'SVB':
            return svb_top
        else:
            raise ValueError("bank must be 'JPM', 'SVB', or 'all'")
