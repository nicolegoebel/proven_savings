import numpy as np
import matplotlib.pyplot as plt

# Current JavaScript model parameters
current_models = {
    'Pre-seed': {
        'model': 'linear',
        'slope': 142000.9,
        'intercept': -61478.75
    },
    'Seed': {
        'model': 'polynomial',
        'a': 1245.44,
        'b': 53613.65,
        'c': 220522.93
    },
    'Series A+': {
        'model': 'linear',
        'slope': 111347.28,
        'intercept': -72002.51
    }
}

# Old HTML model parameters
old_models = {
    'Pre-seed': {
        'model': 'quadratic',
        'a': 100,
        'b': 2000,
        'c': 0
    },
    'Seed': {
        'model': 'quadratic',
        'a': 150,
        'b': 3000,
        'c': 0
    },
    'Series A+': {
        'model': 'quadratic',
        'a': 200,
        'b': 4000,
        'c': 0
    }
}

# New proposed model parameters
proposed_models = {
    'Pre-seed': {
        'model': 'linear',
        'slope': 45000,
        'intercept': -10000
    },
    'Seed': {
        'model': 'polynomial',
        'a': 200,  # reduced quadratic coefficient
        'b': 50000,  # increased linear coefficient
        'c': 100000  # increased base savings
    },
    'Series A+': {
        'model': 'linear',
        'slope': 40000,
        'intercept': -10000
    }
}

# Create sample data with new range
companies = np.linspace(10, 1600, 200)  # From 10 to 1600 companies

# Create subplots for better comparison
fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(15, 25))
colors = {'Pre-seed': 'blue', 'Seed': 'green', 'Series A+': 'red'}

# Plot current models
for level in colors.keys():
    params = current_models[level]
    if params['model'] == 'linear':
        savings = params['slope'] * companies + params['intercept']
    else:  # polynomial
        savings = params['a'] * companies**2 + params['b'] * companies + params['c']
    ax1.plot(companies, savings/1e6, color=colors[level], label=f'{level}', linewidth=2)

ax1.grid(True)
ax1.set_xlabel('Number of Companies')
ax1.set_ylabel('Savings (Millions $)')
ax1.set_title('Current Model (JavaScript)')
ax1.legend()

# Plot old models
for level in colors.keys():
    params = old_models[level]
    savings = params['a'] * companies**2 + params['b'] * companies + params['c']
    ax2.plot(companies, savings/1e6, color=colors[level], label=f'{level}', linewidth=2)

ax2.grid(True)
ax2.set_xlabel('Number of Companies')
ax2.set_ylabel('Savings (Millions $)')
ax2.set_title('Old Model (HTML)')
ax2.legend()

# Plot proposed models
for level in colors.keys():
    params = proposed_models[level]
    if params['model'] == 'linear':
        savings = params['slope'] * companies + params['intercept']
    else:  # polynomial
        savings = params['a'] * companies**2 + params['b'] * companies + params['c']
    ax3.plot(companies, savings/1e6, color=colors[level], label=f'{level}', linewidth=2)

ax3.grid(True)
ax3.set_xlabel('Number of Companies')
ax3.set_ylabel('Savings (Millions $)')
ax3.set_title('Proposed New Model')
ax3.legend()

# Plot all models together
for level in colors.keys():
    current_params = current_models[level]
    if current_params['model'] == 'linear':
        current_savings = current_params['slope'] * companies + current_params['intercept']
    else:  # polynomial
        current_savings = current_params['a'] * companies**2 + current_params['b'] * companies + current_params['c']

    old_params = old_models[level]
    old_savings = old_params['a'] * companies**2 + old_params['b'] * companies + old_params['c']

    proposed_params = proposed_models[level]
    if proposed_params['model'] == 'linear':
        proposed_savings = proposed_params['slope'] * companies + proposed_params['intercept']
    else:  # polynomial
        proposed_savings = proposed_params['a'] * companies**2 + proposed_params['b'] * companies + proposed_params['c']

    ax4.plot(companies, current_savings/1e6, color=colors[level], label=f'{level} (Current)', linewidth=2)
    ax4.plot(companies, old_savings/1e6, color=colors[level], linestyle='--', label=f'{level} (Old)', linewidth=2)
    ax4.plot(companies, proposed_savings/1e6, color=colors[level], linestyle=':', label=f'{level} (Proposed)', linewidth=2)

ax4.grid(True)
ax4.set_xlabel('Number of Companies')
ax4.set_ylabel('Savings (Millions $)')
ax4.set_title('All Models Comparison')
ax4.legend()

# Format axes for better readability
for ax in [ax1, ax2, ax3, ax4]:
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))

plt.tight_layout()
plt.savefig('model_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# Create sample data with new range
companies = np.linspace(10, 1600, 200)  # From 10 to 1600 companies

# Set up the plot
plt.figure(figsize=(15, 10))
colors = {'Pre-seed': 'blue', 'Seed': 'green', 'Series A+': 'red'}

# Plot proposed models
for level in colors.keys():
    params = proposed_models[level]
    if params['model'] == 'linear':
        savings = params['slope'] * companies + params['intercept']
    else:  # polynomial
        savings = params['a'] * companies**2 + params['b'] * companies + params['c']
    
    plt.plot(companies, savings/1e6, color=colors[level], label=f'{level}', linewidth=2)

plt.grid(True)
plt.xlabel('Number of Companies')
plt.ylabel('Savings (Millions $)')
plt.title('Proposed Savings Models (10-1600 Companies)')
plt.legend()

# Add text box with model characteristics
plt.text(0.02, 0.98, 
         'Model Characteristics:\n' +
         '1. Seed: Quadratic growth (highest savings)\n' +
         '2. Pre-seed: Linear growth (medium savings)\n' +
         '3. Series A+: Linear growth (lowest savings)',
         transform=plt.gca().transAxes,
         bbox=dict(facecolor='white', alpha=0.8),
         verticalalignment='top',
         fontsize=10)

# Format axis for better readability
plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))

plt.savefig('proposed_models.png', dpi=300, bbox_inches='tight')
plt.close()
