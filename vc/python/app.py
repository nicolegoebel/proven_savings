import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

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
"""
Two different approaches for distributing companies across investment levels:

1. Original Variable Distribution (DISTRIBUTION):
   - Uses different ratios depending on which combination of levels is selected
   - Pre-defined ratios for each possible combination:
     * All three levels: Pre-seed (8%), Seed (90%), Series A+ (2%)
     * Pre-seed + Seed: Pre-seed (9%), Seed (91%)
     * Seed + Series A+: Seed (94%), Series A+ (6%)
     * Pre-seed + Series A+: Pre-seed (80%), Series A+ (20%)
   - Advantage: Tailored ratios for each specific combination
   - Disadvantage: Less flexible, requires predefined ratios for each possible combination
"""
DISTRIBUTION = {
    'all_three': {'Pre seed': 0.08, 'Seed': 0.90, 'Series A+': 0.02},
    'pre_seed_seed': {'Pre seed': 0.09, 'Seed': 0.91},
    'seed_series': {'Seed': 0.94, 'Series A+': 0.06},
    'pre_seed_series': {'Pre seed': 0.80, 'Series A+': 0.20}
}

"""
2. Fixed Distribution (JS_DISTRIBUTION):
   - Uses a single set of weights that are normalized based on selected levels
   - Same ratios used regardless of which combination is selected
   - When fewer than all levels are selected, weights are normalized while maintaining relative proportions
   - Example for 100 companies with Seed + Series A+ selected:
     * Original weights: Seed (0.875), Series A+ (0.04)
     * Total weight = 0.875 + 0.04 = 0.915
     * Normalized: Seed (96%), Series A+ (4%)
   - Advantage: More flexible, maintains consistent relative relationships
   - Disadvantage: May not capture nuanced differences between specific combinations
"""
JS_DISTRIBUTION = {
    'Pre seed': 0.085,  # 8.5%
    'Seed': 0.875,      # 87.5%
    'Series A+': 0.04   # 4%
}

# Parameters for savings calculations
PARAMETERS = {
    'Pre seed': {
        'model': 'linear',
        'slope': 142000.9,
        'intercept': -61478.75
    },
    'Seed': {
        'model': 'polynomial',
        'a': 1245.44,  # x^2 coefficient
        'b': 53613.65,  # x coefficient
        'c': 220522.93  # constant term
    },
    'Series A+': {
        'model': 'linear',
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
    """Calculate the number of companies for each investment level.
    
    This function supports two different distribution methods:
    
    1. Fixed (JavaScript-style):
       - Uses consistent weights (JS_DISTRIBUTION) regardless of selected combination
       - Weights are normalized while maintaining relative proportions
       - Example: If Seed (0.875) and Series A+ (0.04) are selected:
         * Normalized to Seed (95.6%) and Series A+ (4.4%)
         * For 100 companies: Seed (96), Series A+ (4)
    
    2. Original (Variable):
       - Uses different predefined ratios (DISTRIBUTION) for each combination
       - Example: If Seed and Series A+ are selected:
         * Uses seed_series distribution: Seed (94%), Series A+ (6%)
         * For 100 companies: Seed (94), Series A+ (6)
    
    Args:
        num_companies (int): Total number of companies to distribute
        selected_levels (list): List of selected investment levels
    
    Returns:
        dict: Number of companies assigned to each selected level
    """
    if len(selected_levels) == 1:
        return {selected_levels[0]: num_companies}
    
    with st.sidebar:
        st.markdown("### Advanced Settings")
        distribution_method = st.selectbox(
            "Distribution Method",
            ["Original (Variable)", "Fixed (JavaScript-style)"],
            help="Choose how to distribute companies across investment levels. Original method uses different ratios based on selected combinations. Fixed method uses consistent ratios regardless of selection."
        )

    if distribution_method == "Fixed (JavaScript-style)":
        # JavaScript-style distribution: normalize the fixed weights
        total_weight = sum(JS_DISTRIBUTION[level] for level in selected_levels)
        return {
            level: round((JS_DISTRIBUTION[level] / total_weight) * num_companies)
            for level in selected_levels
        }
    else:
        # Original distribution method: use predefined ratios for each combination
        if len(selected_levels) == 2:
            if 'Pre seed' in selected_levels and 'Seed' in selected_levels:
                dist = DISTRIBUTION['pre_seed_seed']
            elif 'Seed' in selected_levels and 'Series A+' in selected_levels:
                dist = DISTRIBUTION['seed_series']
            else:  # Pre seed and Series A+
                dist = DISTRIBUTION['pre_seed_series']
        else:  # All three levels
            dist = DISTRIBUTION['all_three']
        
        # Filter and normalize the distribution for selected levels
        filtered_dist = {k: v for k, v in dist.items() if k in selected_levels}
        total = sum(filtered_dist.values())
        normalized_dist = {k: v/total for k, v in filtered_dist.items()}
        
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
    """Calculate savings based on the distribution and parameters using linear or polynomial regression."""
    distribution = calculate_company_distribution(num_companies, selected_levels)
    total_admin_savings = calculate_admin_savings(num_companies, reminder_frequency)
    
    savings = {}
    details = {}
    
    success_rate = SUCCESS_RATES[reminder_frequency]
    
    for level, count in distribution.items():
        if count > 0:
            params = PARAMETERS[level]
            
            # Calculate savings based on model type
            if params['model'] == 'linear':
                total_savings = ((params['slope'] * count) + params['intercept']) * success_rate
            else:  # polynomial
                total_savings = (params['a'] * (count ** 2) + params['b'] * count + params['c']) * success_rate
            
            successful_companies = round(count * success_rate)
            details[level] = {
                'companies': count,
                'successful_companies': successful_companies,
                'savings': total_savings,
                'admin_savings': 0,  # Set to 0 for individual levels
                'total_combined_savings': total_savings,  # Don't include admin savings in level totals
                'savings_per_company': total_savings / count if count > 0 else 0
            }
            savings[level] = total_savings
    
    return sum(savings.values()), distribution, details, total_admin_savings

def format_value(value, is_currency=True):
    """Format numeric values for display."""
    if value == 0:
        return "$0" if is_currency else "0"
    
    abs_value = abs(value)
    if abs_value >= 1_000_000:
        # Round to one decimal place for millions
        value_in_m = round(value / 1_000_000, 1)
        return f"${value_in_m:,.1f}M" if is_currency else f"{value_in_m:,.1f}M"
    elif abs_value >= 1000:
        # Round to nearest thousand for K values
        value_in_k = round(value / 1000)
        return f"${value_in_k:,}K" if is_currency else f"{value_in_k:,}K"
    else:
        # For values less than 1000, keep original formatting
        return f"${value:,.0f}" if is_currency else f"{value:,.0f}"

def display_metrics_table(selected_levels, details, total_admin_savings):
    """Display metrics in a table format."""
    # Calculate totals
    total_savings = sum(d['savings'] for d in details.values())
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
        ("Potential Portfolio Savings", "savings", True, "Using the Proven database, we model potential savings on the relationship between total offers redeemed and the number of portfolio companies within a specific investment level, over the period of one year."),
        ("VC Admin Cost Savings", "admin_savings", True, "Admin time is estimated by counting the hours spent managing current vendors (~5 hours/month), responding to portfolio company requests (bimonthly inquiries for half of portfolio companies, ~20 minutes each), tailoring specific vendor-portfolio company introductions (half of portfolio companies require specific introduction each month, ~15 minutes each), performing administrative tasks such as updating and maintaining vendor directory database (2 updates weekly, ~1 hour each), and reaching out to vendors to ensure availability of fresh, new deals offered (10 inquires per week, ~10 minutes each). We assume an annual average salary of $150K and 50% of the employees time applied to the above tasks."),
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
            if label == "VC Admin Cost Savings":
                # Show dash for admin savings in level columns
                row_cols[i+1].markdown('<div class="value-cell">-</div>', unsafe_allow_html=True)
            else:
                value = details[level][key] if level in details else 0
                row_cols[i+1].markdown(f'<div class="value-cell">{format_value(value, is_currency)}</div>', unsafe_allow_html=True)
        
        # Total column
        if label == "Potential Portfolio Savings":
            total = total_savings
        elif label == "VC Admin Cost Savings":
            total = total_admin_savings
            # Add divider after Admin Cost Savings
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        elif label == "Total Potential Savings":
            total = total_savings + total_admin_savings
            # Add divider after Total Potential Savings
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        else:  # Average Potential Savings/Portfolio Company
            total = (total_savings + total_admin_savings)/total_companies if total_companies > 0 else 0
        
        row_cols[-1].markdown(f'<div class="total-cell">{format_value(total, is_currency)}</div>', unsafe_allow_html=True)

def plot_savings_models():
    """Create a comparison plot of savings models using Altair."""
    # Create range of company numbers
    companies = np.linspace(10, 1600, 100)
    
    # Calculate savings for each model
    data = pd.DataFrame({
        'Companies': companies,
        'Seed (Current Polynomial)': PARAMETERS['Seed']['a'] * (companies ** 2) + 
                                   PARAMETERS['Seed']['b'] * companies + 
                                   PARAMETERS['Seed']['c'],
        'Seed (Alternative Polynomial)': 1245.44228685 * (companies ** 2) + 
                                       53613.64782558 * companies + 
                                       220522.93396342,
        'Seed (Linear)': 212778.2 * companies - 118202.85,  # Original linear parameters
        'Pre_seed': PARAMETERS['Pre seed']['slope'] * companies + 
                   PARAMETERS['Pre seed']['intercept'],
        'Series_A': PARAMETERS['Series A+']['slope'] * companies + 
                   PARAMETERS['Series A+']['intercept']
    })
    
    # Melt the dataframe for Altair
    data_melted = data.melt(
        id_vars=['Companies'], 
        value_vars=['Seed (Current Polynomial)', 'Seed (Alternative Polynomial)', 
                   'Seed (Linear)', 'Pre_seed', 'Series_A'],
        var_name='Model',
        value_name='Savings'
    )
    
    # Base chart for solid lines
    solid_lines = alt.Chart(data_melted).mark_line().encode(
        x=alt.X('Companies:Q', title='Number of Portfolio Companies'),
        y=alt.Y('Savings:Q', 
                title='Potential Savings ($)',
                axis=alt.Axis(format='$~s')),
        color=alt.Color('Model:N', 
                       title='Investment Stage',
                       scale=alt.Scale(
                           domain=['Seed (Current Polynomial)', 'Seed (Alternative Polynomial)', 
                                 'Seed (Linear)', 'Pre_seed', 'Series_A'],
                           range=['#1f77b4', '#1f77b4', '#1f77b4', '#2ca02c', '#d62728']
                       )),
        strokeDash=alt.StrokeDash(
            'Model:N',
            scale=alt.Scale(
                domain=['Seed (Current Polynomial)', 'Seed (Alternative Polynomial)', 
                       'Seed (Linear)', 'Pre_seed', 'Series_A'],
                range=[[0], [10,5], [5,5], [0], [0]]  # Solid, dot-dash, dashed, solid, solid
            )
        ),
        tooltip=[
            alt.Tooltip('Companies:Q', title='Portfolio Companies'),
            alt.Tooltip('Savings:Q', title='Savings', format='$,.0f'),
            alt.Tooltip('Model:N', title='Stage')
        ]
    ).properties(
        width=700,
        height=400,
        title='Comparison of Savings Models'
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14
    ).configure_title(
        fontSize=16,
        anchor='middle'
    )
    
    return solid_lines

# Streamlit UI
st.title('Three Steps to Estimating Potential Portfolio Savings Using Proven')
st.markdown('<div class="divider title-divider"></div>', unsafe_allow_html=True)

# Input controls
st.subheader("1. Select Total Number of Portfolio Companies")
num_companies = st.slider('', min_value=10, max_value=1600, value=100)

st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)

st.subheader("2. Select Investment Levels", help="The total number of portfolio companies selected above are distributed among the three levels of investment based on the average distributions in the Proven database: Pre-seed: 8-9%, Seed: 90-94%, Series A+: 2-6%")

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
st.subheader("3. Select Reminder Frequency", help="This is the frequency with which admins contact portfolio companies in order to remind them to tap into available deals on their Proven platform; the higher the frequency, the higher the potential savings, with Monthly and Quarterly reminders increasing the No Frequency savings by 30% and 15%, respectively.")
reminder_frequency = st.selectbox(
    'Reminder Frequency',
    ['No reminders', 'Quarterly reminders', 'Monthly reminders'],
    index=2,
    label_visibility='collapsed'
)

if len(investment_levels) == 0:
    st.warning('Please select at least one investment level.')
else:
    # Add section title and divider
    st.markdown("<h2 style='font-size: 2em; margin-bottom: 0.5rem;'>Potential Annual Savings</h2>", unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # Calculate and display results
    savings, distribution, details, total_admin_savings = calculate_savings(num_companies, investment_levels, reminder_frequency)
    
    # Display the metrics table
    display_metrics_table(investment_levels, details, total_admin_savings)

    # Add spacing
    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)

    # Display the comparison plot
    # st.subheader("Savings Models Comparison")
    # st.markdown("This plot shows how potential savings scale with portfolio size across different investment stages.")
    # chart = plot_savings_models()
    # st.altair_chart(chart, use_container_width=True)
