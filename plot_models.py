import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Actual data
data = {
    'AllPortcos_Count': [1,3,3,3,1,15,10,2,6,2,1,1,1,10,1,2,44,1,27,15,3,3,7,1,6,1,4,1,5,6,2,48,45,27,38,4,1,92,14,16,81,19,48,103,19,11,15,14,12,1,1,2,3,1,5,1,2,1,5,5,1,7,6,5,4,1,5,1,2,1,6,5,1,14,28,192,1,151,564,8,2,1,11,2,4,7,3,2,5,1,1,8,22,7,6,28,2,51,1,57,1,44,3,1,3,5,3,7,11,10,12,3,5,1,1,3,1,9,7,1,5,1,13,3,5,3,8,8,3,1,2,3,4,2,1,11,16,18,2,3,2,11,1,5,1,1,1,1,4,5,3,1,1,1,7,8,1,9,3,1,6,1,3,15,29,1,5,1,18,10,1,11,2,4,1,1,3,3,1,13,54,1,40,39,38,2,24,1,36,2,44,5,3,2,6,1,15,1,4,6,1,24,1,19,15,3,6,6,6,12,14,1,44,1,27,15,2,2,8,2,6,2,5],
    'AllPortcos_Sum': [3000.0,679500.0,21000.0,459000.0,22500.0,1535395.0,1003800.0,13000.0,232550.0,25100.0,60000.0,360000.0,10000.0,118650.0,100000.0,250000.0,5392500.0,300000.0,3757000.0,4367830.0,378000.0,4500.0,2130000.0,1000.0,574500.0,5000.0,709500.0,3000.0,191000.0,1839400.0,86000.0,776901.0,4209700.0,4182000.0,4959000.0,327000.0,1000.0,13368415.0,1021400.0,2360650.0,16155868.0,2065400.0,12927025.0,22638747.0,2324900.0,166000.0,2301000.0,355500.0,614900.0,180.0,6000.0,21752.0,146000.0,100000.0,209400.0,10000.0,140000.0,25000.0,1181500.0,116100.0,1000.0,3025100.0,822000.0,1055750.0,716000.0,53500.0,2056500.0,100.0,19100.0,2000.0,210000.0,31600.0,1000.0,2103285.0,2325124.0,55980614.0,1000.0,19803368.0,200849124.0,725152.0,353800.0,10000.0,390500.0,28500.0,22000.0,94000.0,102100.0,101000.0,44500.0,50000.0,25000.0,836750.0,513750.0,289500.0,1515500.0,1311250.0,10500.0,5998000.0,217500.0,3991800.0,25000.0,3545754.0,91000.0,77000.0,33000.0,192085.0,128500.0,533500.0,2015305.0,191500.0,555500.0,137000.0,285500.0,1000.0,110000.0,118100.0,9000.0,795543.0,1227470.0,350000.0,273350.0,25000.0,3861600.0,408500.0,917200.0,172500.0,54685.0,109290.0,132725.0,5000.0,53750.0,38500.0,434500.0,119000.0,4000.0,2093200.0,1592000.0,2537150.0,10800.0,42000.0,12000.0,1683500.0,100000.0,647000.0,1000.0,26000.0,25000.0,25000.0,55500.0,246400.0,205000.0,4752.0,5000.0,6000.0,266350.0,581000.0,9000.0,908558.0,570000.0,100000.0,128000.0,3000.0,113000.0,736000.0,1938600.0,5000.0,180200.0,105100.0,2887030.0,934950.0,2500.0,947650.0,102500.0,222500.0,25000.0,13500.0,250000.0,253000.0,3000.0,1091500.0,6506000.0,26000.0,5118550.0,6005222.0,5666104.0,27500.0,853000.0,4183.0,2230917.0,150000.0,1369958.0,333000.0,156100.0,351000.0,572350.0,100000.0,816250.0,2500.0,342500.0,124000.0,10000.0,1511265.0,20.0,1578960.0,2636693.0,121000.0,1339100.0,511174.0,3600400.0,836150.0,3465600.0,526000.0,5392500.0,300000.0,3757000.0,4008830.0,13000.0,9500.0,486500.0,26000.0,724500.0,23500.0,217000.0]
}

df = pd.DataFrame(data)

# Model parameters from constants.js
PARAMETERS = {
    'Pre-seed': {
        'a': 100,
        'b': 35000,
        'c': 20000
    },
    'Seed': {
        'a': 250,
        'b': 80000,
        'c': 50000
    },
    'Series A+': {
        'a': 50,
        'b': 25000,
        'c': 15000
    }
}

# Success rates
SUCCESS_RATES = {
    'none': 0.10,
    'quarterly': 0.15,
    'monthly': 0.30
}

# Create data points
companies = np.linspace(0, 1600, 100)

plt.figure(figsize=(15, 10))

# Plot actual data points
plt.scatter(df['AllPortcos_Count'], df['AllPortcos_Sum'] / 1e6, 
           alpha=0.3, color='gray', label='Actual Data', s=30)

# Plot each investment level
for level, params in PARAMETERS.items():
    savings = params['a'] * companies**2 + params['b'] * companies + params['c']
    plt.plot(companies, savings / 1e6, label=f'{level} (Base)')

# Plot total savings with different reminder frequencies
total_savings = np.zeros_like(companies)
for level, params in PARAMETERS.items():
    total_savings += params['a'] * companies**2 + params['b'] * companies + params['c']

for freq, rate in SUCCESS_RATES.items():
    active_companies = companies * rate
    freq_savings = np.zeros_like(companies)
    for params in PARAMETERS.values():
        freq_savings += params['a'] * active_companies**2 + params['b'] * active_companies + params['c']
    plt.plot(companies, freq_savings / 1e6, '--', label=f'Total with {freq} reminders ({rate*100}% active)')

plt.xlabel('Number of Portfolio Companies')
plt.ylabel('Savings (Millions USD)')
plt.title('Savings Models by Investment Level and Reminder Frequency')
plt.grid(True, alpha=0.3)
plt.legend()

# Add reference points
reference_points = [(100, 17), (500, 166), (1000, 529)]
for companies, savings in reference_points:
    plt.plot(companies, savings, 'ro')
    plt.annotate(f'({companies}, ${savings}M)', 
                (companies, savings),
                xytext=(10, 10), 
                textcoords='offset points')

plt.savefig('savings_models.png')
plt.close()
