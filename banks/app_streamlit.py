import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from data_analysis.bank_stats import BankSavingsAnalyzer
from data_analysis.model_visualization import SavingsModelVisualizer

def format_number(num):
    """Format numbers to be rounded to nearest 10 for values under 1000,
    nearest 100 for larger values, and use M/B for millions/billions."""
    if abs(num) < 1000:
        num = round(num / 10) * 10  # Round to nearest 10
        return f"${num:,.0f}"
    
    num = round(num / 100) * 100  # Round to nearest 100
    
    if abs(num) >= 1e9:
        return f"${num/1e9:.1f}B"
    elif abs(num) >= 1e6:
        return f"${num/1e6:.1f}M"
    else:
        return f"${num:,.0f}"

# Set page config
st.set_page_config(
    page_title="Potential Bank Savings with Proven",
    layout="wide"
)

# Initialize paths and analyzers
app_dir = Path(__file__).parent
data_dir = app_dir / 'data'
static_dir = app_dir / 'static'
analyzer = BankSavingsAnalyzer(data_dir)
visualizer = SavingsModelVisualizer(data_dir)

# Generate visualizations
visualizer.generate_all_visualizations()

# Title
st.title("Potential Bank Savings with Proven")

# Sidebar for inputs
with st.sidebar:
    st.header("Prediction Parameters")
    
    # Number of Clients slider
    num_clients = st.slider(
        "Number of Clients",
        min_value=200,
        max_value=2000000,
        value=200,
        step=200,
        format="%d"
    )
    
    # Company Types
    st.subheader("Company Types")
    startup_checkbox = st.checkbox("Startups", value=True)
    sme_checkbox = st.checkbox("SMEs", value=False)
    
    # Engagement Level
    engagement_level = st.selectbox(
        "Engagement Level",
        options=["rarely", "often", "frequently"],
        index=0
    )
    
    # Create predict button
    predict_button = st.button("Predict Savings")

# Main content
if predict_button:
    # Prepare company types list
    company_types = []
    if startup_checkbox:
        company_types.append("startup")
    if sme_checkbox:
        company_types.append("sme")
    
    if not company_types:
        st.error("Please select at least one company type.")
    else:
        # Get predictions
        annual_savings = analyzer.predict_annual_savings(
            num_clients=num_clients,
            company_types=company_types,
            engagement_level=engagement_level
        )
        
        # Get top offers
        top_offers = analyzer.get_top_offers(
            num_clients=num_clients,
            company_types=company_types,
            engagement_level=engagement_level
        )
        
        # Display results in columns
        col1, col2 = st.columns(2)
        
        # Column 1: Savings Metrics
        with col1:
            st.header("Potential Savings")
            metrics_col1, metrics_col2 = st.columns(2)
            
            with metrics_col1:
                st.metric(
                    "Total Annual Savings",
                    format_number(annual_savings['total_annual_savings'])
                )
                st.metric(
                    "Average Monthly Savings",
                    format_number(annual_savings['monthly_savings'])
                )
            
            with metrics_col2:
                st.metric(
                    "Annual Savings per Company",
                    format_number(annual_savings['avg_savings_per_company'])
                )
                st.metric(
                    "Monthly Savings per Company",
                    format_number(annual_savings['avg_savings_per_company']/12)
                )
        
        # Column 2: Top Offers
        with col2:
            st.header("Top 10 Potential Deals")
            st.dataframe(
                top_offers[['offer_name', 'avg_savings']].rename(columns={
                    'offer_name': 'Deal Name',
                    'avg_savings': 'Potential Savings'
                }).style.format({
                    'Potential Savings': '${:,.2f}'
                }),
                hide_index=True
            )
        
        # Insights Section
        st.header("Key Insights")
        
        # Calculate insights for each company type
        if "startup" in company_types:
            # Calculate savings based on SVB benchmark ($188 per client)
            startup_savings = num_clients * 188 * (1.5 if engagement_level == "frequently" else 1.0 if engagement_level == "often" else 0.5)
            st.info(
                f"**Startups:** With {num_clients:,} clients at {engagement_level} engagement level, "
                f"expect {format_number(startup_savings)} in annual savings."
            )
        
        if "sme" in company_types:
            # SMEs have 30% lower savings on average
            sme_savings = num_clients * 188 * 0.7 * (1.5 if engagement_level == "frequently" else 1.0 if engagement_level == "often" else 0.5)
            st.warning(
                f"**SMEs:** With {num_clients:,} clients at {engagement_level} engagement level, "
                f"expect {format_number(sme_savings)} in annual savings."
            )
        
        if len(company_types) == 2:
            mixed_savings = (startup_savings + sme_savings) / 2
            st.success(
                f"**Mixed Portfolio:** With {num_clients:,} total clients at {engagement_level} engagement level, "
                f"expect an average of {format_number(mixed_savings)} in annual savings."
            )
        
        # Display Savings Projections Section
        st.header("Savings Projections")
        
        # Create dynamic plot for selected number of clients
        st.subheader("Projected Growth in Annual Savings")
        
        # Create plot points for current and doubled clients
        client_points = np.array([num_clients, num_clients * 2])
        
        # Create plot
        fig = plt.figure(figsize=(12, 6))
        
        # Colors for different engagement levels
        colors = {'Frequently': '#4BC0C0', 'Often': '#FF9F40', 'Rarely': '#FF6384'}
        multipliers = {'Frequently': 1.5, 'Often': 1.0, 'Rarely': 0.5}
        
        # Plot for each company type and engagement level
        if "startup" in company_types:
            for level, mult in multipliers.items():
                savings = client_points * 188 * mult
                plt.plot(client_points, savings, 
                         label=f'Startups - {level} (x{mult})',
                         color=colors[level],
                         linestyle='-' if level == engagement_level.capitalize() else '--',
                         linewidth=3 if level == engagement_level.capitalize() else 1)
                if level == engagement_level.capitalize():
                    plt.scatter(client_points, savings, color=colors[level], s=100)
        
        if "sme" in company_types:
            for level, mult in multipliers.items():
                savings = client_points * 188 * 0.7 * mult  # 30% lower for SMEs
                plt.plot(client_points, savings, 
                         label=f'SMEs - {level} (x{mult})',
                         color=colors[level],
                         linestyle=':' if level == engagement_level.capitalize() else '-.',
                         linewidth=3 if level == engagement_level.capitalize() else 1)
                if level == engagement_level.capitalize():
                    plt.scatter(client_points, savings, color=colors[level], s=100)
        
        plt.title('Projected Annual Savings Growth\n(Current vs Double Clients)', fontsize=14, pad=20)
        plt.xlim(num_clients * 0.9, num_clients * 2.1)  # Set x-axis with some padding
        plt.xlabel('Number of Clients', fontsize=12)
        plt.ylabel('Annual Savings ($)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend(loc='upper left', fontsize=10)
        
        # Format axes
        ax = plt.gca()
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${int(x):,}'))
        
        # Show plot
        st.pyplot(fig)
        plt.close()
        
        # Historical Data Section
        st.header("Historical Data")
        
        # Historical Trends
        st.subheader("Monthly Savings Trends")
        st.write("This plot shows the actual and projected monthly savings for both banks:")
        st.image(str(static_dir / 'historical_trends.png'), use_container_width=True)
        
        # Bank Statistics
        st.subheader("Current Statistics")

# Get statistics
stats = analyzer.get_all_stats()

# Display historical data in columns
col1, col2 = st.columns(2)

# JPM Statistics
with col1:
    st.subheader("JPM Statistics")
    st.markdown(f"""
    * Total Savings: {format_number(stats['JPM']['total_savings'])}
    * Avg per Redemption: {format_number(stats['JPM']['avg_savings_per_redemption'])}
    * Unique Companies: {stats['JPM']['unique_companies']:,}
    * Total Deal Redemptions: {stats['JPM']['total_redemptions']:,}
    * Avg Redemptions per Company: {stats['JPM']['avg_redemptions_per_company']:.1f}
    """)
    
    # Display top 10 companies for JPM
    st.subheader("Top 10 Companies by Savings")
    top_jpm = analyzer.get_top_companies(bank='JPM', n=10)
    for idx, row in top_jpm.iterrows():
        st.markdown(f"{idx + 1}. **{row['company']}**")
        st.markdown(f"   - Total Savings: {format_number(row['total_savings'])}")
        st.markdown(f"   - Median per Deal: {format_number(row['median_savings'])}")

# SVB Statistics
with col2:
    st.subheader("SVB Statistics")
    st.markdown(f"""
    * Total Savings: {format_number(stats['SVB']['total_savings'])}
    * Avg per Redemption: {format_number(stats['SVB']['avg_savings_per_redemption'])}
    * Unique Companies: {stats['SVB']['unique_companies']:,}
    * Total Deal Redemptions: {stats['SVB']['total_redemptions']:,}
    * Avg Redemptions per Company: {stats['SVB']['avg_redemptions_per_company']:.1f}
    """)
    
    # Display top 10 companies for SVB
    st.subheader("Top 10 Companies by Savings")
    top_svb = analyzer.get_top_companies(bank='SVB', n=10)
    for idx, row in top_svb.iterrows():
        st.markdown(f"{idx + 1}. **{row['company']}**")
        st.markdown(f"   - Total Savings: {format_number(row['total_savings'])}")
        st.markdown(f"   - Median per Deal: {format_number(row['median_savings'])}")

# Company Distribution
st.subheader("Company Savings Distribution")
st.image(str(static_dir / 'company_distribution.png'), use_container_width=True)

# Savings vs Clients
st.subheader("Projected Annual Savings by Number of Clients")
st.write("This chart shows how annual savings scale with the number of clients at different engagement levels:")
st.write("- **Frequently (x1.5)**: High engagement (JPM's level)")
st.write("- **Often (x1.0)**: Medium engagement (SVB's level)")
st.write("- **Rarely (x0.5)**: Low engagement")
st.image(str(static_dir / 'savings_vs_clients.png'), use_container_width=True)
