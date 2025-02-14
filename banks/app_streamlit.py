import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from data_analysis.bank_stats import BankSavingsAnalyzer
from data_analysis.model_visualization import SavingsModelVisualizer

def format_number(num):
    """Format numbers with appropriate units (K, M, B) and minimal decimal places."""
    if abs(num) >= 1e9:
        return f"${num/1e9:.1f}B"
    elif abs(num) >= 1e6:
        return f"${num/1e6:.1f}M"
    elif abs(num) >= 1e3:
        return f"${num/1e3:.1f}K"
    else:
        return f"${num:.0f}"

# Set page config
st.set_page_config(
    page_title="Potential Bank Savings with Proven",
    layout="wide"
)

# Initialize paths and analyzer
app_dir = Path(__file__).parent
data_dir = app_dir / 'data'
analyzer = BankSavingsAnalyzer(data_dir)

# Title
st.title("Potential Bank Savings with Proven")

# Sidebar for inputs
with st.sidebar:
    st.header("Prediction Parameters")
    
    # Startup Clients Selection
    st.subheader("Startup Clients")
    startup_range = st.radio(
        "Startup Client Range",
        options=["Small (1-100)", "Medium (100-10K)", "Large (10K-2M)"],
        index=0,
        key="startup_range"
    )
    
    # Adjust startup slider based on selected range
    if startup_range == "Small (1-100)":
        num_startup_clients = st.slider(
            "Number of Startup Clients",
            min_value=0,
            max_value=100,
            value=10,
            step=1,
            format="%d"
        )
    elif startup_range == "Medium (100-10K)":
        num_startup_clients = st.slider(
            "Number of Startup Clients",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100,
            format="%d"
        )
    else:  # Large range
        num_startup_clients = st.slider(
            "Number of Startup Clients",
            min_value=10000,
            max_value=2000000,
            value=100000,
            step=10000,
            format="%d"
        )
    
    # SME Clients Selection
    st.subheader("SME Clients")
    sme_range = st.radio(
        "SME Client Range",
        options=["Small (1-100)", "Medium (100-10K)", "Large (10K-2M)"],
        index=0,
        key="sme_range"
    )
    
    # Adjust SME slider based on selected range
    if sme_range == "Small (1-100)":
        num_sme_clients = st.slider(
            "Number of SME Clients",
            min_value=0,
            max_value=100,
            value=10,
            step=1,
            format="%d"
        )
    elif sme_range == "Medium (100-10K)":
        num_sme_clients = st.slider(
            "Number of SME Clients",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100,
            format="%d"
        )
    else:  # Large range
        num_sme_clients = st.slider(
            "Number of SME Clients",
            min_value=10000,
            max_value=2000000,
            value=100000,
            step=10000,
            format="%d"
        )
    
    # Engagement Level
    engagement_level_map = {
        "Low": "rarely",
        "Medium": "often",
        "High": "frequently"
    }
    
    engagement_ui = st.selectbox(
        "Engagement Level",
        options=["Low", "Medium", "High"],
        index=0
    )
    engagement_level = engagement_level_map[engagement_ui]
    
    # Create predict button
    predict_button = st.button("Predict Savings")

# Main content
if predict_button:
    # Get predictions for startups if any
    startup_pred = None
    if num_startup_clients > 0:
        startup_pred = analyzer.predict_annual_savings(
            num_clients=num_startup_clients,
            company_types=["startup"],
            engagement_level=engagement_level
        )
    
    # Get predictions for SMEs if any
    sme_pred = None
    if num_sme_clients > 0:
        sme_pred = analyzer.predict_annual_savings(
            num_clients=num_sme_clients,
            company_types=["sme"],
            engagement_level=engagement_level
        )
    
    # Get combined predictions if both types have clients
    combined_pred = None
    if num_startup_clients > 0 and num_sme_clients > 0:
        combined_pred = analyzer.predict_annual_savings(
            num_clients=num_startup_clients + num_sme_clients,
            company_types=["startup", "sme"],
            engagement_level=engagement_level
        )
    
    # Display savings metrics
    st.header("Potential Savings")
    
    # Create three columns for displaying metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if startup_pred:
            st.metric(
                "Startup Annual Savings",
                format_number(startup_pred['total_annual_savings'])
            )
    
    with col2:
        if sme_pred:
            st.metric(
                "SME Annual Savings",
                format_number(sme_pred['total_annual_savings'])
            )
    
    with col3:
        if combined_pred:
            st.metric(
                "Combined Annual Savings",
                format_number(combined_pred['total_annual_savings'])
            )
    
    # Insights Section
    st.header("Key Insights")
    
    # Convert engagement level to descriptive text
    engagement_desc = {
        'rarely': 'a low',
        'often': 'a medium',
        'frequently': 'a high'
    }[engagement_level]  # Keep internal mapping as is
    
    # Display startup insights if any
    if startup_pred:
        annual = startup_pred['total_annual_savings']
        monthly = startup_pred['monthly_savings']
        weekly = monthly / 4.33  # Average number of weeks in a month
        
        st.info(
            f"**Startups:** With {num_startup_clients:,} clients at {engagement_desc} engagement level:\n"
            f"- Annual Savings: {format_number(annual)}\n"
            f"- Monthly Savings: {format_number(monthly)}"
        )
    
    # Display SME insights if any
    if sme_pred:
        annual = sme_pred['total_annual_savings']
        monthly = sme_pred['monthly_savings']
        weekly = monthly / 4.33  # Average number of weeks in a month
        
        st.warning(
            f"**SMEs:** With {num_sme_clients:,} clients at {engagement_desc} engagement level:\n"
            f"- Annual Savings: {format_number(annual)}\n"
            f"- Monthly Savings: {format_number(monthly)}"
        )
    
    # Display combined insights if both types have clients
    if combined_pred:
        total_clients = num_startup_clients + num_sme_clients
        annual = combined_pred['total_annual_savings']
        monthly = combined_pred['monthly_savings']
        weekly = monthly / 4.33  # Average number of weeks in a month
        
        st.success(
            f"**Combined Portfolio:** With {total_clients:,} total clients at {engagement_desc} engagement level:\n"
            f"- Annual Savings: {format_number(annual)}\n"
            f"- Monthly Savings: {format_number(monthly)}"
        )



        
