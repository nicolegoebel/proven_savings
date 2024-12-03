import streamlit as st
import pandas as pd
import numpy as np

# Add custom CSS for clean layout
st.markdown("""
<style>
    /* Apply clean font family to all elements */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    div[data-testid="column"] {
        padding: 0.5rem;
        margin: 0;
    }
    
    div[data-testid="stHorizontalBlock"] {
        gap: 0;
        margin: 0;
        border: none;
    }
    
    .column-header {
        text-align: center;
        font-size: 1.4em;
        font-weight: bold;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
        border: none;
    }
    
    .column-header.value-column {
        border-bottom: 2px solid #e0e0e0;
    }

    .column-header.total-column {
        border-bottom: 2px solid #2E5EAA;
        color: #2E5EAA;
    }
    
    .row-label {
        font-weight: bold;
        padding: 0.5rem 0;
        text-align: right;
        padding-right: 1rem;
        border: none;
        font-size: 1.4em;
    }
    
    .value-cell {
        text-align: right;
        padding: 0.5rem;
        border: none;
        font-size: 1.8em;
        font-weight: 500;
    }

    .total-cell {
        text-align: right;
        padding: 0.5rem;
        border: none;
        font-size: 1.8em;
        font-weight: 800;
        color: #2E5EAA;
    }

    .section-header {
        font-size: 1.1em;
        font-weight: bold;
        color: #666666;
        margin-bottom: 0.5rem;
    }

    .divider {
        height: 2px;
        background-color: #e0e0e0;
        margin: 1rem 0;
    }

    .title-divider {
        margin-top: 0;
        margin-bottom: 3rem;
    }

    h1 {
        font-size: 2.5em !important;
        font-weight: bold !important;
        margin-bottom: 0.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Constants for investment level distributions
DISTRIBUTION = {
    'all_three': {'Pre seed': 0.08, 'Seed': 0.90, 'Series A+': 0.02},
    'pre_seed_seed': {'Pre seed': 0.09, 'Seed': 0.91},
    'seed_series': {'Seed': 0.94, 'Series A+': 0.06},
    'pre_seed_series': {'Pre seed': 0.80, 'Series A+': 0.20}
}

# Parameters for linear regression calculations (y = mx + b)
PARAMETERS = {
    'Pre seed': {
        'slope': 142000.9,
        'intercept': -61478.75
    },
    'Seed': {
        'slope': 212778.2,
        'intercept': -118202.85
    },
    'Series A+': {
        'slope': 111347.28,
        'intercept': -72002.51
    }
}

# Constants
SUCCESS_RATES = {
    'No reminders': 0.10,
    'Quarterly reminders': 0.15,
    'Monthly reminders': 0.30
}

# Admin time savings parameters
HOURLY_RATE = 150000 / 2080  # $150,000 per year / (40 hours * 52 weeks)

def round_to_ten(value):
    """Round a number to the nearest 10."""
    return round(value / 10) * 10

def calculate_company_distribution(num_companies, selected_levels):
    """Calculate the number of companies for each investment level."""
    if len(selected_levels) == 1:
        return {selected_levels[0]: num_companies}
    
    if len(selected_levels) == 2:
        if 'Pre seed' in selected_levels and 'Seed' in selected_levels:
            dist = DISTRIBUTION['pre_seed_seed']
        elif 'Seed' in selected_levels and 'Series A+' in selected_levels:
            dist = DISTRIBUTION['seed_series']
        else:  # Pre seed and Series A+
            dist = DISTRIBUTION['pre_seed_series']
    else:  # All three levels
        dist = DISTRIBUTION['all_three']
    
    # Filter distribution for selected levels and normalize
    filtered_dist = {k: v for k, v in dist.items() if k in selected_levels}
    total = sum(filtered_dist.values())
    normalized_dist = {k: v/total for k, v in filtered_dist.items()}
    
    # Calculate number of companies for each level
    return {level: round(normalized_dist[level] * num_companies) 
            for level in selected_levels}

def calculate_admin_savings(num_companies, reminder_frequency):
    """Calculate admin time savings based on the comprehensive formula.

    Let’s break this down systematically to estimate the number of hours a 
    Head of Platform (HoP) spends managing vendor relationships manually for 
    100 portfolio companies. We’ll factor in typical activities and reasonable 
    time assumptions.

    Key Activities

        1.	Vendor Relationship Management
        •	Communicating with vendors about deals, updates, and managing 
        the preferred vendor list.
        •	Estimation: 5 hours/month for vendor coordination.
        2.	Portfolio Company Requests
        •	Responding to portfolio companies asking for vendor recommendations 
        or deals.
        •	Assume each portfolio company asks for help once every 2 months.
        •	For 100 portfolio companies, that’s 50 requests/month, with ~20 
        minutes per request.
        •	Estimation:  50 \times 20/60 = 16.7  hours/month.
        3.	Vendor Introductions
        •	Making tailored introductions between vendors and portfolio companies.
        •	Assume half the portfolio companies (50) need a specific introduction 
        once a month.
        •	Each introduction takes ~15 minutes.
        •	Estimation:  50 \times 15/60 = 12.5  hours/month.
        4.	Administrative Tasks
        •	Updating and maintaining vendor directories in Google Sheets or Notion.
        •	Assume 2 updates/week, taking ~1 hour each.
        •	Estimation:  2 \times 4 = 8  hours/month.
        5.	Vendor Outreach
        •	Replying to inbound vendor inquiries about becoming part of the 
        network or offering new deals.
        •	Assume 10 inquiries/week, taking ~10 minutes each.
        •	Estimation:  10 \times 10/60 \times 4 = 6.7  hours/month.

    Total Time Spent (Manual Process)

        1.	Vendor Relationship Management: 5 hours/month
        2.	Portfolio Company Requests: 16.7 hours/month
        3.	Vendor Introductions: 12.5 hours/month
        4.	Administrative Tasks: 8 hours/month
        5.	Vendor Outreach: 6.7 hours/month

    Grand Total: ~49 hours/month

    Using Proven Platform

    The Proven platform automates or significantly reduces most of these tasks:
        •	Vendor updates and outreach: Automated.
        •	Portfolio requests: Self-service vendor discovery.
        •	Vendor introductions: Streamlined with built-in communication tools.

    Estimated Time Savings:
    Proven could reduce the monthly time spent by 80-90%, leaving only minimal time for oversight and customization.
        •	Time saved/month:  49 \times 0.85 = 41.65  hours.

    Formula for Time Savings

    For N portfolio companies:

    \text{Time Spent (hours)} = (N \times 0.5) + (N \times 0.25) + 5 + 8 + (10 \times 0.1667 \times 4)

    Where:
        •	 N \times 0.5 : Portfolio requests (20 min/request every 2 months).
        •	 N \times 0.25 : Vendor introductions (15 min/introduction monthly).
        •	 5 : Vendor relationship management.
        •	 8 : Admin updates.
        •	 10 \times 0.1667 \times 4 : Vendor inquiries (10 min/inquiry, weekly).

    Time Saved Using Proven:

    \text{Time Saved (hours)} = \text{Time Spent} \times 0.85


    Example for 100 Portfolio Companies

        •	Time Spent Without Proven:  49  hours/month.
        •	Time Saved With Proven:  41.65  hours/month.

    This calculation provides a clear, data-driven framework for demonstrating Proven’s value in time savings for a Head of Platform.
        
        Formula components:
        - Portfolio requests: N * 0.5 (20 min/request every 2 months)
        - Vendor introductions: N * 0.25 (15 min/introduction monthly)
        - Vendor relationship management: 5 hours
        - Admin updates: 8 hours
        - Vendor inquiries: 10 * 0.1667 * 4 (10 min/inquiry, weekly)
        
        The total is reduced by 85% to represent time saved by using Proven.
    """
    N = num_companies
    T_savings = 0.85
    ADMIN_FACTOR = .5 # amount of time an admin spends on admin tasks
    
    # Calculate total hours spent
    vendor_relationship = 5 * 12 # Fixed hours per month
    portfolio_requests = N * 0.5 * 12 # 20 min/request every 2 months
    vendor_introductions = N * 0.25 * 12 # 15 min/introduction monthly
    admin_updates = 8 * 12# Fixed hours monthly
    vendor_inquiries = 10 * 0.1667 * 52  # 10 min/inquiry, weekly for 52 weeks per year
    
    total_hours = (portfolio_requests + vendor_introductions + vendor_relationship + admin_updates + vendor_inquiries)*ADMIN_FACTOR
    
    # Calculate savings (85% reduction in time)
    hours_saved = total_hours * T_savings
    
    # Convert hours to dollar savings using hourly rate
    return hours_saved * HOURLY_RATE

def calculate_savings(num_companies, selected_levels, reminder_frequency):
    """Calculate savings based on the distribution and parameters using linear regression."""
    distribution = calculate_company_distribution(num_companies, selected_levels)
    savings = {}
    details = {}
    
    success_rate = SUCCESS_RATES[reminder_frequency]
    
    for level, count in distribution.items():
        if count > 0:
            slope = PARAMETERS[level]['slope']
            intercept = PARAMETERS[level]['intercept']
            # Calculate savings using linear regression: y = mx + b
            total_savings = ((slope * count) + intercept) * success_rate
            admin_savings = calculate_admin_savings(count, reminder_frequency)
            
            successful_companies = round(count * success_rate)
            details[level] = {
                'companies': count,
                'successful_companies': successful_companies,
                'savings': total_savings,
                'admin_savings': admin_savings,
                'total_combined_savings': total_savings + admin_savings,
                'savings_per_company': total_savings / count if count > 0 else 0,
                'admin_savings_per_company': admin_savings / count if count > 0 else 0
            }
            savings[level] = total_savings
    
    return savings, distribution, details

def format_value(value, is_currency=True):
    """Format numeric values for display."""
    if value == 0:
        return "$0" if is_currency else "0"
    
    abs_value = abs(value)
    if abs_value >= 1_000_000:
        # Round to nearest million and format with M
        value_in_m = round(value / 1_000_000)
        return f"${value_in_m:,}M" if is_currency else f"{value_in_m:,}M"
    elif abs_value >= 1000:
        # Round to nearest thousand and format with K
        value_in_k = round(value / 1000)
        return f"${value_in_k:,}K" if is_currency else f"{value_in_k:,}K"
    else:
        # For values less than 1000, keep original formatting
        return f"${value:,.0f}" if is_currency else f"{value:,.0f}"

def display_metrics_table(selected_levels, details):
    """Display metrics in a table format."""
    # Calculate totals
    total_savings = sum(d['savings'] for d in details.values())
    total_admin_savings = sum(d['admin_savings'] for d in details.values())
    total_combined = total_savings + total_admin_savings
    total_companies = sum(d['companies'] for d in details.values())
    
    # Create columns for labels and each investment level
    cols = st.columns([1, 1, 1, 1, 1])
    
    # Column headers
    cols[0].markdown('<div class="column-header"></div>', unsafe_allow_html=True)
    for i, level in enumerate(selected_levels):
        cols[i+1].markdown(f'<div class="column-header value-column">{level}</div>', unsafe_allow_html=True)
    cols[-1].markdown('<div class="column-header total-column">Total</div>', unsafe_allow_html=True)
    
    # Row labels and values
    metrics = [
        ("Potential Savings", "savings", True, "Using our database, we model potential savings on the relationship between total offers redeemed and the number of portfolio companies within a specific investment level, over the period of one year."),
        ("Admin Cost Savings", "admin_savings", True, "Admin time is estimated by counting the hours spent managing current vendors (~5 hours/month), responding to portfolio company requests (bimonthly inquiries for half of portfolio companies, ~20 minutes each), tailoring specific vendor-portfolio company introductions (half of portfolio companies require specific introduction each month, ~15 minutes each), performing administrative tasks such as updating and maintaining vendor directory database (2 updates weekly, ~1 hour each), and reaching out to vendors to ensure availability of fresh, new deals offered (10 inquires per week, ~10 minutes each). We assume an annual average salary of $150K and 50% of the employees time applied to the above tasks."),
        ("Total Potential Savings", "total_combined_savings", True, None),
        ("Average Potential Savings/Portfolio Company", "savings_per_company", True, None)
    ]
    
    for i, (label, key, is_currency, tooltip) in enumerate(metrics):
        row_cols = st.columns([1, 1, 1, 1, 1])
        
        # Label column with tooltip if provided
        if tooltip:
            row_cols[0].markdown(f'<div class="row-label">{label}</div>', help=tooltip, unsafe_allow_html=True)
        else:
            row_cols[0].markdown(f'<div class="row-label">{label}</div>', unsafe_allow_html=True)
        
        # Value columns for each investment level
        for i, level in enumerate(selected_levels):
            value = details[level][key] if level in details else 0
            row_cols[i+1].markdown(f'<div class="value-cell">{format_value(value, is_currency)}</div>', unsafe_allow_html=True)
        
        # Total column
        if label == "Potential Savings":
            total = total_savings
        elif label == "Admin Cost Savings":
            total = total_admin_savings
            # Add divider after Admin Cost Savings
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        elif label == "Total Potential Savings":
            total = total_combined
            # Add divider after Total Potential Savings
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        else:  # Average Potential Savings/Startup
            total = total_savings/total_companies if total_companies > 0 else 0
        
        row_cols[-1].markdown(f'<div class="total-cell">{format_value(total, is_currency)}</div>', unsafe_allow_html=True)

# Streamlit UI
st.title('Three Steps to Estimating Potential Portfolio Savings Using Proven')
st.markdown('<div class="divider title-divider"></div>', unsafe_allow_html=True)

# Input controls
st.subheader("1. Select Total Number of Portfolio Companies")
num_companies = st.slider('', min_value=10, max_value=1000, value=100)

st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)

st.subheader("2. Select Investment Levels", help="The total number of portfolio companies selected above are distributed among the three levels of investment based on the average distributions in our database: Pre-seed: 8-9%, Seed: 90-94%, Series A+: 2-6%")

cols = st.columns(3)
investment_levels = []
if cols[0].checkbox('Pre-Seed', value=True):
    investment_levels.append('Pre seed')
if cols[1].checkbox('Seed', value=True):
    investment_levels.append('Seed')
if cols[2].checkbox('Series A+', value=True):
    investment_levels.append('Series A+')

st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)

# Reminder frequency selection
st.subheader("3. Select Reminder Frequency", help="This is the frequency which which admins contact portfolio companies in order to remind them to tap into available deals on their Proven platform.")
reminder_frequencies = ['No reminders', 'Quarterly reminders', 'Monthly reminders']
reminder_frequency = st.selectbox('', reminder_frequencies, index=0)

st.markdown("<div style='margin: 4rem 0;'></div>", unsafe_allow_html=True)

if len(investment_levels) == 0:
    st.warning('Please select at least one investment level.')
else:
    # Calculate and display results
    savings, distribution, details = calculate_savings(num_companies, investment_levels, reminder_frequency)
    
    # Display the metrics table
    display_metrics_table(investment_levels, details)
