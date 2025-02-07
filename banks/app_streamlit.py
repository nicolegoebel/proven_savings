import streamlit as st
import pandas as pd
import numpy as np
import math
import plotly.graph_objects as go
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
            startup_base = num_clients * 1000 * (1.5 if engagement_level == "frequently" else 1.0 if engagement_level == "often" else 0.5)
            startup_doubled = startup_base * 2
            growth_rate = ((startup_doubled / startup_base) - 1) * 100 if startup_base > 0 else 100
            
            st.info(
                f"**Startups:** For every doubling of clients, savings increase by {growth_rate:.1f}%. "
                f"At {num_clients:,} clients, expect {format_number(startup_base)} in annual savings."
            )
        
        if "sme" in company_types:
            sme_base = num_clients * 1000 * 0.7 * (1.5 if engagement_level == "frequently" else 1.0 if engagement_level == "often" else 0.5)
            sme_doubled = sme_base * 2
            growth_rate = ((sme_doubled / sme_base) - 1) * 100 if sme_base > 0 else 100
            
            st.warning(
                f"**SMEs:** For every doubling of clients, savings increase by {growth_rate:.1f}%. "
                f"At {num_clients:,} clients, expect {format_number(sme_base)} in annual savings."
            )
        
        if len(company_types) == 2:
            both_base = (startup_base + sme_base) / 2
            both_doubled = both_base * 2
            growth_rate = ((both_doubled / both_base) - 1) * 100 if both_base > 0 else 100
            
            st.success(
                f"**Mixed Portfolio:** For every doubling of clients, savings increase by {growth_rate:.1f}%. "
                f"At {num_clients:,} clients, expect {format_number(both_base)} in annual savings."
            )
        
        # Engagement Comparison Chart
        st.header("Startup Savings by Engagement Level")
        
        # Generate points from current to double clients
        num_points = 10
        start_clients = max(200, num_clients)  # Start at current or 200, whichever is larger
        end_clients = start_clients * 2  # Show up to double the clients
        client_points = np.linspace(start_clients, end_clients, num_points)
        
        # Create traces for each engagement level
        fig = go.Figure()
        
        engagement_colors = {
            'frequently': '#4BC0C0',
            'often': '#FF9F40',
            'rarely': '#FF6384'
        }
        
        # Calculate multipliers for each engagement level
        multipliers = {
            'frequently': 1.5,
            'often': 1.0,
            'rarely': 0.5
        }
        
        max_savings = 0
        
        for level in ['frequently', 'often', 'rarely']:
            # Calculate linear growth based on number of clients
            base_savings_per_client = 1000  # $1000 base savings per client
            savings = client_points * base_savings_per_client * multipliers[level]
            max_savings = max(max_savings, max(savings))
            
            fig.add_trace(go.Scatter(
                x=client_points,
                y=savings,
                name=level.capitalize(),
                line=dict(color=engagement_colors[level])
            ))
        
        # Calculate nice round numbers for y-axis ticks
        magnitude = 10 ** (len(str(int(max_savings))) - 1)
        max_y = math.ceil(max_savings / magnitude) * magnitude
        y_ticks = np.linspace(0, max_y, 6)  # 6 evenly spaced ticks
        
        fig.update_layout(
            title=f"Potential Savings Growth: {format_number(start_clients)} to {format_number(end_clients)} Clients",
            xaxis_title="Number of Clients",
            yaxis_title="Annual Savings ($)",
            showlegend=True,
            height=500,
            yaxis=dict(
                tickmode='array',
                tickvals=y_ticks,
                ticktext=[format_number(y) for y in y_ticks]
            ),
            xaxis=dict(
                tickmode='array',
                tickvals=np.linspace(start_clients, end_clients, 6),
                ticktext=[format_number(x) for x in np.linspace(start_clients, end_clients, 6)]
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)

# Historical Data Section
st.header("Historical Bank Data")

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

# Display visualizations
st.header("Historical Visualizations")

# Historical Savings Trends
st.subheader("Historical Savings Trends")
st.image(str(static_dir / 'historical_trends.png'), use_container_width=True)

# Company Distribution
st.subheader("Company Savings Distribution")
st.image(str(static_dir / 'company_distribution.png'), use_container_width=True)

# Savings vs Clients
st.subheader("Projected Annual Savings by Number of Clients")
st.image(str(static_dir / 'savings_vs_clients.png'), use_container_width=True)
