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
        totalWeight += INVESTMENT_DISTRIBUTIONS[level];
    });

    // Distribute companies proportionally
    const result = {};
    selectedLevels.forEach(level => {
        const proportion = INVESTMENT_DISTRIBUTIONS[level] / totalWeight;
        result[level] = Math.round(numCompanies * proportion);
    });

    return result;
}

// Calculate savings for each investment level
function calculateSavings(numCompanies, selectedLevels, reminderFrequency) {
    if (numCompanies <= 0) {
        return {
            totalSavings: 0,
            adminSavings: 0,
            details: {}
        };
    }

    const distribution = calculateCompanyDistribution(numCompanies, selectedLevels);
    const adminSavings = calculateAdminSavings(numCompanies, reminderFrequency);
    let totalSavings = 0;
    const details = {};
    
    // Calculate savings for each investment level
    Object.entries(distribution).forEach(([level, companies]) => {
        const params = PARAMETERS[level];
        let baseSavings;
        
        // Calculate savings based on model type
        if (params.model === 'linear') {
            baseSavings = (params.slope * companies) + params.intercept;
        } else { // polynomial
            baseSavings = (params.a * (companies ** 2)) + (params.b * companies) + params.c;
        }
        
        const successRate = SUCCESS_RATES[reminderFrequency];
        const savings = Math.round(baseSavings * successRate);
        
        totalSavings += savings;
        details[level] = {
            companies: companies,
            savings: savings
        };
    });
    
    return {
        totalSavings: totalSavings,
        adminSavings: adminSavings,
        details: details
    };
}
