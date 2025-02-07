import streamlit as st
import pandas as pd
import numpy as np
import json
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

# Initialize the analyzers
data_dir = Path(__file__).parent / 'data'
analyzer = BankSavingsAnalyzer(data_dir)
visualizer = SavingsModelVisualizer(data_dir)

# Title
st.title("Potential Bank Savings with Proven")

# Sidebar for inputs
with st.sidebar:
    st.header("Prediction Parameters")
    
    # Client range selector
    range_option = st.radio(
        "Select Range",
        options=["Small (200-10,000)", "Large (10,000-2,000,000)"]
    )
    
    # Number of Clients slider based on selected range
    if range_option == "Small (200-10,000)":
        num_clients = st.slider(
            "Number of Clients",
            min_value=200,
            max_value=10000,
            value=200,
            step=200,
            format="%d"
        )
    else:
        num_clients = st.slider(
            "Number of Clients",
            min_value=10000,
            max_value=2000000,
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
        
        # Create savings vs clients plot
        st.header("Savings vs Number of Clients")
        fig_savings = go.Figure()
        
        # Generate points from 200 to num_clients
        client_points = np.linspace(200, num_clients, 50)
        
        # Calculate base savings per client
        base_per_client = 1000  # $1000 per client base
        
        # Adjust for engagement level
        engagement_multiplier = 1.5 if engagement_level == "frequently" else 1.0 if engagement_level == "often" else 0.5
        
        # Adjust for company types
        savings_points = []
        for clients in client_points:
            total = 0
            if "startup" in company_types:
                startup_savings = clients * base_per_client * engagement_multiplier
                total += startup_savings
            if "sme" in company_types:
                sme_savings = clients * base_per_client * 0.7 * engagement_multiplier  # SMEs save 70% of startup amount
                total += sme_savings
            if len(company_types) == 2:
                total /= 2  # Average for mixed portfolio
            savings_points.append(total)
        
        # Add trace
        fig_savings.add_trace(go.Scatter(
            x=client_points,
            y=savings_points,
            mode='lines',
            name='Predicted Savings',
            line=dict(color='#4BC0C0', width=2)
        ))
        
        # Add current point
        fig_savings.add_trace(go.Scatter(
            x=[num_clients],
            y=[annual_savings['total_annual_savings']],
            mode='markers',
            name='Current Selection',
            marker=dict(color='red', size=10)
        ))
        
        # Calculate y-axis ticks
        max_savings = max(savings_points)
        y_step = 10**int(np.log10(max_savings/5))  # Round to nearest power of 10
        y_max = ((int(max_savings / y_step) + 1) * y_step)  # Round up to nearest step
        y_ticks = list(range(0, int(y_max) + y_step, y_step))
        
        # Update layout
        fig_savings.update_layout(
            xaxis_title="Number of Clients",
            yaxis_title="Annual Savings ($)",
            showlegend=True,
            height=500,
            yaxis=dict(
                tickmode='array',
                tickvals=y_ticks,
                ticktext=[format_number(x) for x in y_ticks],
                range=[0, y_max * 1.1]  # Add 10% padding at top
            ),
            xaxis=dict(
                type='linear',  # Ensure linear scale
                tickformat=',d'
            )
        )
        
        st.plotly_chart(fig_savings, use_container_width=True)


# Engagement Level Plot
# Generate prediction surface
visualizer.generate_prediction_surface()

# Engagement Comparison Chart
st.header("Startup Savings by Engagement Level")

# Load prediction data
with open(visualizer.static_dir / 'prediction_data.json', 'r') as f:
    prediction_data = json.load(f)

# Create the plot
fig = go.Figure()

# Define colors for engagement levels
engagement_colors = {
    'frequently': '#4BC0C0',
    'often': '#FF9F40',
    'rarely': '#FF6384'
}

# Add traces for each engagement level
max_savings = 0
for level in ['rarely', 'often', 'frequently']:
    data = prediction_data[level]
    # Filter data points to only show >= 200 clients
    companies = np.array(data['companies'])
    savings = np.array(data['savings'])
    mask = companies >= 200
    
    fig.add_trace(go.Scatter(
        x=companies[mask],
        y=savings[mask],
        name=level.capitalize(),
        line=dict(color=engagement_colors[level], width=2)
    ))
    
    max_savings = max(max_savings, max(savings[mask]))

# Calculate y-axis ticks
y_step = 10**int(np.log10(max_savings/5))  # Round to nearest power of 10
y_max = ((int(max_savings / y_step) + 1) * y_step)  # Round up to nearest step
y_ticks = list(range(0, int(y_max) + y_step, y_step))

# Update layout
fig.update_layout(
    xaxis_title="Number of Clients",
    yaxis_title="Annual Savings ($)",
    showlegend=True,
    height=500,
    yaxis=dict(
        tickmode='array',
        tickvals=y_ticks,
        ticktext=[format_number(x) for x in y_ticks],
        range=[0, y_max * 1.1]  # Add 10% padding at top
    ),
    xaxis=dict(
        type='linear',  # Ensure linear scale
        tickformat=',d'
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

# Get the directory containing the current script
script_dir = Path(__file__).parent

# Historical Savings Trends
st.subheader("Historical Savings Trends")
image_path = script_dir / "static" / "historical_trends.png"
st.image(str(image_path))

# Company Distribution
st.subheader("Company Savings Distribution")
image_path = script_dir / "static" / "company_distribution.png"
st.image(str(image_path))
