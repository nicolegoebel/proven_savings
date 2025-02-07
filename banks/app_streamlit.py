import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path
from data_analysis.bank_stats import BankSavingsAnalyzer
from data_analysis.model_visualization import SavingsModelVisualizer

# Set page config
st.set_page_config(
    page_title="Potential Bank Savings with Proven",
    layout="wide"
)

# Initialize the analyzers
data_dir = Path(__file__).parent / 'data'
analyzer = BankSavingsAnalyzer(data_dir)
visualizer = SavingsModelVisualizer(data_dir)

# Title
st.title("Potential Bank Savings with Proven")

# Sidebar for inputs
with st.sidebar:
    st.header("Prediction Parameters")
    
    # Number of Clients slider
    num_clients = st.slider(
        "Number of Clients",
        min_value=10000,
        max_value=3000000,
        value=10000,
        step=10000,
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
                    f"${annual_savings['total_annual_savings']:,.2f}"
                )
                st.metric(
                    "Average Monthly Savings",
                    f"${annual_savings['monthly_savings']:,.2f}"
                )
            
            with metrics_col2:
                st.metric(
                    "Annual Savings per Company",
                    f"${annual_savings['avg_savings_per_company']:,.2f}"
                )
                st.metric(
                    "Monthly Savings per Company",
                    f"${annual_savings['avg_savings_per_company']/12:,.2f}"
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
                f"At {num_clients:,} clients, expect ${startup_base:,.2f} in annual savings."
            )
        
        if "sme" in company_types:
            sme_base = num_clients * 1000 * 0.7 * (1.5 if engagement_level == "frequently" else 1.0 if engagement_level == "often" else 0.5)
            sme_doubled = sme_base * 2
            growth_rate = ((sme_doubled / sme_base) - 1) * 100 if sme_base > 0 else 100
            
            st.warning(
                f"**SMEs:** For every doubling of clients, savings increase by {growth_rate:.1f}%. "
                f"At {num_clients:,} clients, expect ${sme_base:,.2f} in annual savings."
            )
        
        if len(company_types) == 2:
            both_base = (startup_base + sme_base) / 2
            both_doubled = both_base * 2
            growth_rate = ((both_doubled / both_base) - 1) * 100 if both_base > 0 else 100
            
            st.success(
                f"**Mixed Portfolio:** For every doubling of clients, savings increase by {growth_rate:.1f}%. "
                f"At {num_clients:,} clients, expect ${both_base:,.2f} in annual savings."
            )
        
        # Engagement Comparison Chart
        st.header("Startup Savings by Engagement Level")
        
        # Generate points from 0 to num_clients
        num_points = 10
        client_points = np.linspace(0, num_clients, num_points)
        
        # Create traces for each engagement level
        fig = go.Figure()
        
        engagement_colors = {
            'frequently': '#4BC0C0',
            'often': '#FF9F40',
            'rarely': '#FF6384'
        }
        
        for level in ['frequently', 'often', 'rarely']:
            savings = [
                analyzer.predict_annual_savings(
                    num_clients=int(clients),
                    company_types=['startup'],
                    engagement_level=level
                )['total_annual_savings']
                for clients in client_points
            ]
            
            fig.add_trace(go.Scatter(
                x=client_points,
                y=savings,
                name=level.capitalize(),
                line=dict(color=engagement_colors[level])
            ))
        
        fig.update_layout(
            xaxis_title="Number of Clients",
            yaxis_title="Annual Savings ($)",
            showlegend=True,
            height=500
        )
        
        # Update axis labels to use formatted numbers
        fig.update_xaxes(tickformat=",d")
        fig.update_yaxes(tickprefix="$", tickformat=",")
        
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
    * Total Savings: ${stats['JPM']['total_savings']:,.2f}
    * Avg per Redemption: ${stats['JPM']['avg_savings_per_redemption']:,.2f}
    * Unique Companies: {stats['JPM']['unique_companies']}
    * Total Deal Redemptions: {stats['JPM']['total_redemptions']}
    * Avg Redemptions per Company: {stats['JPM']['avg_redemptions_per_company']:.1f}
    """)

# SVB Statistics
with col2:
    st.subheader("SVB Statistics")
    st.markdown(f"""
    * Total Savings: ${stats['SVB']['total_savings']:,.2f}
    * Avg per Redemption: ${stats['SVB']['avg_savings_per_redemption']:,.2f}
    * Unique Companies: {stats['SVB']['unique_companies']}
    * Total Deal Redemptions: {stats['SVB']['total_redemptions']}
    * Avg Redemptions per Company: {stats['SVB']['avg_redemptions_per_company']:.1f}
    """)

# Display visualizations
st.header("Historical Visualizations")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Historical Savings Trends")
    # Get the directory containing the current script
    script_dir = Path(__file__).parent
    # Construct the absolute path to the image
    image_path = script_dir / "static" / "historical_trends.png"
    st.image(str(image_path))

with col2:
    st.subheader("Company Savings Distribution")
    st.image("static/company_distribution.png")
