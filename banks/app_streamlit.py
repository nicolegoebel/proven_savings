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
    
    # Number of Clients selection
    client_range = st.radio(
        "Client Range",
        options=["Small (1-100)", "Medium (100-10K)", "Large (10K-2M)"],
        index=0
    )
    
    # Adjust slider based on selected range
    if client_range == "Small (1-100)":
        num_clients = st.slider(
            "Number of Clients",
            min_value=1,
            max_value=100,
            value=10,
            step=1,
            format="%d"
        )
    elif client_range == "Medium (100-10K)":
        num_clients = st.slider(
            "Number of Clients",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100,
            format="%d"
        )
    else:  # Large range
        num_clients = st.slider(
            "Number of Clients",
            min_value=10000,
            max_value=2000000,
            value=100000,
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
        
        # Display savings metrics
        st.header("Potential Savings")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Total Annual Savings",
                format_number(annual_savings['total_annual_savings'])
            )
        
        with col2:
            st.metric(
                "Total Monthly Savings",
                format_number(annual_savings['total_annual_savings'] / 12)
            )
        
        # Insights Section
        st.header("Key Insights")
        
        # Calculate insights for each company type
        if "startup" in company_types and "sme" not in company_types:
            # Get startup-only predictions
            startup_pred = analyzer.predict_annual_savings(
                num_clients=num_clients,
                company_types=["startup"],
                engagement_level=engagement_level
            )
            st.info(
                f"**Startups:** With {num_clients:,} clients at {engagement_level} engagement level, "
                f"expect {format_number(startup_pred['total_annual_savings'])} in annual savings."
            )
        
        if "sme" in company_types and "startup" not in company_types:
            # Get SME-only predictions
            sme_pred = analyzer.predict_annual_savings(
                num_clients=num_clients,
                company_types=["sme"],
                engagement_level=engagement_level
            )
            st.warning(
                f"**SMEs:** With {num_clients:,} clients at {engagement_level} engagement level, "
                f"expect {format_number(sme_pred['total_annual_savings'])} in annual savings."
            )
        
        if len(company_types) == 2:
            # Mixed portfolio predictions were already calculated in annual_savings
            st.success(
                f"**Mixed Portfolio:** With {num_clients:,} total clients at {engagement_level} engagement level, "
                f"expect an average of {format_number(annual_savings['total_annual_savings'])} in annual savings."
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
        
        # Plot savings based on company types and engagement levels
        for level in ['rarely', 'often', 'frequently']:
            # Get predictions for current and doubled clients
            current_pred = analyzer.predict_annual_savings(
                num_clients=num_clients,
                company_types=company_types,
                engagement_level=level
            )['total_annual_savings']
            
            doubled_pred = analyzer.predict_annual_savings(
                num_clients=num_clients * 2,
                company_types=company_types,
                engagement_level=level
            )['total_annual_savings']
            
            # Plot the predictions
            savings = [current_pred, doubled_pred]
            plt.plot(client_points, savings,
                     label=f'{level.capitalize()}',
                     color=colors[level.capitalize()],
                     linestyle='-' if level == engagement_level else '--',
                     linewidth=3 if level == engagement_level else 1)
            
            if level == engagement_level:
                plt.scatter(client_points, savings, color=colors[level.capitalize()], s=100)
        
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
        

        
