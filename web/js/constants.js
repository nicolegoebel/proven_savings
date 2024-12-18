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
        model: 'linear',
        slope: 142000.9,
        intercept: -61478.75
    },
    'Seed': {
        model: 'polynomial',
        a: 1245.44,  // x^2 coefficient
        b: 53613.65,  // x coefficient
        c: 220522.93  // constant term
    },
    'Series A+': {
        model: 'linear',
        slope: 111347.28,
        intercept: -72002.51
    }
};

// Success rate multipliers based on reminder frequency
const SUCCESS_RATES = {
    'none': 0.10,      // 10% success rate with no reminders
    'quarterly': 0.15,  // 15% success rate with quarterly reminders
    'monthly': 0.30    // 30% success rate with monthly reminders
};

// Admin time savings parameters
const HOURLY_RATE = 150000 / 2080;  // $150,000 per year / (40 hours * 52 weeks)
