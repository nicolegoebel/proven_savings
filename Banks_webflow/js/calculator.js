// Slider value to client count conversion
function sliderToClients(value) {
    if (value === 0) return 0;
    // Convert slider value (0-100) to exponential scale (1-2M)
    return Math.round(Math.exp(Math.log(1) + (Math.log(2000000) - Math.log(1)) * (value / 100)));
}

// Client count to slider value conversion
function clientsToSlider(clients) {
    if (clients === 0) return 0;
    // Convert client count (1-2M) to slider value (0-100)
    return Math.round((Math.log(clients) - Math.log(1)) / (Math.log(2000000) - Math.log(1)) * 100);
}

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
    const startupSliderValue = parseInt(document.getElementById('startup-slider').value) || 0;
    const smeSliderValue = parseInt(document.getElementById('sme-slider').value) || 0;
    
    const startupClients = sliderToClients(startupSliderValue);
    const smeClients = sliderToClients(smeSliderValue);
    
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
        `With ${engagementText} engagement, our database estimates that approximately `;
    
    // Calculate SME savings
    const smeSavings = calculateSavings(smeClients, 'sme');
    document.getElementById('sme-total').textContent = formatCurrency(smeSavings.totalSavings);
    document.getElementById('sme-active').textContent = smeSavings.engagedClients.toLocaleString();
    document.getElementById('sme-per-client').textContent = formatCurrency(smeSavings.savingsPerActiveClient);
    document.getElementById('sme-engagement-text').textContent = 
        `With ${engagementText} engagement, our database estimates that approximately `;
    
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
        
        // Configure slider
        slider.min = 0;
        slider.max = 100;
        slider.value = 0;
        slider.step = 1;
        
        // Update display when slider moves
        slider.addEventListener('input', function() {
            const value = parseInt(this.value) || 0;
            const clients = sliderToClients(value);
            display.textContent = `${clients.toLocaleString()} clients`;
        });
        
        // Initialize display
        display.textContent = '0 clients';
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
