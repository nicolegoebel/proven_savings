// Investment level distributions (percentage of portfolio)
const INVESTMENT_DISTRIBUTIONS = {
    'Pre-seed': 0.085,  // 8.5%
    'Seed': 0.875,      // 87.5%
    'Series A+': 0.04   // 4%
};

// Savings per company per investment level
const SAVINGS_PER_COMPANY = {
    'Pre-seed': 4000,
    'Seed': 5000,
    'Series A+': 6000
};

// Parameters for savings calculations
const PARAMETERS = {
    'Pre-seed': {
        model: 'polynomial',
        a: 100,          // Quadratic growth
        b: 35000,        // Linear component
        c: 20000         // Base savings
    },
    'Seed': {
        model: 'polynomial',
        a: 250,          // Strongest quadratic growth
        b: 80000,        // Strong linear component
        c: 50000         // Highest base savings
    },
    'Series A+': {
        model: 'polynomial',
        a: 50,           // Smallest quadratic growth
        b: 25000,        // Smallest linear component
        c: 15000         // Smallest base savings
    }
};

// Success rate multipliers based on reminder frequency
const SUCCESS_RATES = {
    'none': 0.10,      // 10% base success rate with no reminders
    'quarterly': 0.15, // 15% success rate with quarterly reminders
    'monthly': 0.30    // 30% success rate with monthly reminders
};

// Admin time savings parameters
const HOURLY_RATE = 150000 / 2080;  // $150,000 per year / (40 hours * 52 weeks)
