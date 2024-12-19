// Round a number to the nearest 10
function roundToTen(value) {
    return Math.round(value / 10) * 10;
}

// Format numeric values for display
function formatValue(value, isCurrency = true) {
    if (value === 0) return '$0';
    
    // Round values less than 1000 to nearest 100
    if (Math.abs(value) < 1000) {
        value = Math.round(value / 100) * 100;
        return isCurrency ? `$${value}` : value.toString();
    }
    
    // Convert to thousands (K) or millions (M)
    if (Math.abs(value) >= 1000000) {
        value = (value / 1000000).toFixed(1);
        return isCurrency ? `$${value}M` : `${value}M`;
    }
    
    if (Math.abs(value) >= 1000) {
        value = Math.round(value / 1000);
        return isCurrency ? `$${value}K` : `${value}K`;
    }
    
    return isCurrency ? `$${value}` : value.toString();
}

// Calculate admin time savings
function calculateAdminSavings(numCompanies, reminderFrequency) {
    if (numCompanies <= 0) {
        return 0;
    }
    
    const hoursPerCompany = 2; // Base hours saved per company
    const hourlyRate = 150; // Standard hourly rate for admin work
    
    // Adjust multiplier based on reminder frequency
    let frequencyMultiplier = 1;
    if (reminderFrequency === 'monthly') {
        frequencyMultiplier = 1.5;
    }
    
    return numCompanies * hoursPerCompany * hourlyRate * frequencyMultiplier;
}

// Calculate company distribution across investment levels
function calculateCompanyDistribution(numCompanies, selectedLevels) {
    if (numCompanies <= 0) {
        return {};
    }

    // Calculate total weight for selected levels
    let totalWeight = 0;
    selectedLevels.forEach(level => {
        totalWeight += INVESTMENT_DISTRIBUTIONS[level] || 0;
    });

    // Distribute companies proportionally
    const result = {};
    selectedLevels.forEach(level => {
        const weight = INVESTMENT_DISTRIBUTIONS[level] || 0;
        const proportion = totalWeight > 0 ? weight / totalWeight : 0;
        result[level] = Math.max(1, Math.round(numCompanies * proportion));
    });

    // Ensure total matches numCompanies
    let total = Object.values(result).reduce((a, b) => a + b, 0);
    if (total > numCompanies) {
        // Adjust proportionally
        Object.keys(result).forEach(level => {
            result[level] = Math.max(1, Math.floor(result[level] * (numCompanies / total)));
        });
    }

    return result;
}

// Calculate savings for each investment level
function calculateSavings(numCompanies, selectedLevels, reminderFrequency) {
    const distribution = calculateCompanyDistribution(numCompanies, selectedLevels);
    const adminSavings = calculateAdminSavings(numCompanies, reminderFrequency);
    
    const savings = {};
    const details = {};
    
    // Get success rate based on reminder frequency
    const successRate = SUCCESS_RATES[reminderFrequency];
    
    for (const [level, count] of Object.entries(distribution)) {
        if (count > 0) {
            const params = PARAMETERS[level];
            
            // Calculate number of active companies based on success rate
            const activeCompanies = Math.round(count * successRate);
            
            // Calculate savings using polynomial model based on active companies
            const totalSavings = (params.a * Math.pow(activeCompanies, 2)) + 
                               (params.b * activeCompanies) + 
                               params.c;
            
            details[level] = {
                companies: count,
                successfulCompanies: activeCompanies,
                savings: totalSavings,
                adminSavings: 0,  // Set to 0 for individual levels
                totalCombinedSavings: totalSavings,  // Don't include admin savings in level totals
                savingsPerCompany: totalSavings / count
            };
            
            savings[level] = totalSavings;
        }
    }
    
    return {
        totalSavings: Object.values(savings).reduce((a, b) => a + b, 0),
        distribution,
        details,
        adminSavings
    };
}
