// Range configurations
const ranges = {
    small: { min: 0, max: 100 },
    medium: { min: 100, max: 10000 },
    large: { min: 10000, max: 2000000 }
};

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

// Calculate savings
function calculateSavings(clients, type) {
    const baseAmount = 17858; // Base amount per active client per year at lowest engagement
    const typeMultiplier = type === 'sme' ? 0.7 : 1;
    
    // Calculate number of engaged clients and engagement multiplier
    const engagementLevel = document.querySelector('.engagement-btn.selected')?.dataset.level || 'rarely';
    const engagementConfig = {
        rarely: { percent: 0.01, multiplier: 1.0 },     // 1% of clients, base savings
        often: { percent: 0.03, multiplier: 1.03 },     // 3% of clients, 3% higher per client
        frequently: { percent: 0.05, multiplier: 1.05 }  // 5% of clients, 5% higher per client
    };
    
    const config = engagementConfig[engagementLevel];
    const engagedClients = Math.round(clients * config.percent);
    
    // Calculate savings per active client with engagement multiplier
    const savingsPerActiveClient = baseAmount * typeMultiplier * config.multiplier;
    
    // Calculate total savings based on active clients
    const totalSavings = engagedClients * savingsPerActiveClient;
    
    return {
        totalSavings: totalSavings,
        engagedClients: engagedClients,
        savingsPerActiveClient: savingsPerActiveClient
    };
}

// Update predictions
function updatePredictions() {
    const startupClients = parseInt(document.getElementById('startup-slider').value) || 0;
    const smeClients = parseInt(document.getElementById('sme-slider').value) || 0;
    
    // Get current engagement level
    const engagementLevel = document.querySelector('.engagement-btn.selected')?.dataset.level || 'rarely';
    const engagementText = {
        rarely: 'low',
        often: 'medium',
        frequently: 'high'
    }[engagementLevel];
    
    // Calculate startup savings
    const startupSavings = calculateSavings(startupClients, 'startup');
    document.getElementById('startup-total').textContent = formatCurrency(startupSavings.totalSavings);
    document.getElementById('startup-active').textContent = startupSavings.engagedClients.toLocaleString();
    document.getElementById('startup-per-client').textContent = formatCurrency(startupSavings.savingsPerActiveClient);
    document.getElementById('startup-engagement-text').textContent = 
        `At ${engagementText} engagement, historical data estimates that approximately `;
    
    // Calculate SME savings
    const smeSavings = calculateSavings(smeClients, 'sme');
    document.getElementById('sme-total').textContent = formatCurrency(smeSavings.totalSavings);
    document.getElementById('sme-active').textContent = smeSavings.engagedClients.toLocaleString();
    document.getElementById('sme-per-client').textContent = formatCurrency(smeSavings.savingsPerActiveClient);
    document.getElementById('sme-engagement-text').textContent = 
        `At ${engagementText} engagement, historical data estimates that approximately `;
    
    // Calculate and display combined savings
    const totalSavings = startupSavings.totalSavings + smeSavings.totalSavings;
    document.getElementById('total-savings').textContent = formatCurrency(totalSavings);
    
    document.getElementById('predictions').classList.remove('hidden');
}

// Initialize sliders
function initializeSliders() {
    ['startup', 'sme'].forEach(type => {
        const slider = document.getElementById(`${type}-slider`);
        const display = document.getElementById(`${type}-value`);
        
        // Update display when slider moves
        slider.addEventListener('input', function() {
            const value = parseInt(this.value) || 0;
            display.textContent = `${value.toLocaleString()} clients`;
        });
        
        // Handle range selection
        document.querySelectorAll(`input[name="${type}-range"]`).forEach(radio => {
            radio.addEventListener('change', function() {
                const range = this.id.split('-')[1];
                const config = ranges[range];
                
                slider.min = config.min;
                slider.max = config.max;
                slider.value = config.min; // Start with minimum value for this range
                
                // Adjust step size based on range
                if (range === 'large') {
                    slider.step = 100; // For 10K-2M range, use steps of 100
                } else {
                    slider.step = Math.max(1, Math.floor((config.max - config.min) / 100));
                }
                
                display.textContent = `${config.min.toLocaleString()} clients`;
            });
        });
        
        // Initialize with small range
        slider.min = ranges.small.min;
        slider.max = ranges.small.max;
        slider.value = ranges.small.min;
        slider.step = 1;
        display.textContent = `${ranges.small.min.toLocaleString()} clients`;
    });
}

// Initialize engagement buttons
function initializeEngagementButtons() {
    document.querySelectorAll('.engagement-btn').forEach(button => {
        button.addEventListener('click', function() {
            document.querySelectorAll('.engagement-btn').forEach(btn => btn.classList.remove('selected'));
            this.classList.add('selected');
        });
    });
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize calculate button
    document.getElementById('calculate-btn').addEventListener('click', function() {
        updatePredictions();
    });

    initializeSliders();
    initializeEngagementButtons();
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
