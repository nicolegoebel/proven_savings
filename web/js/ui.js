// Initialize chart
let savingsChart = null;

// Update the metrics table with calculation results
function updateResults(savings) {
    const resultsContainer = document.getElementById('results-rows');
    resultsContainer.innerHTML = '';
    
    let totalSavings = 0;
    
    // Add rows for each investment level
    Object.entries(savings.details).forEach(([level, data]) => {
        const row = document.createElement('div');
        row.className = 'table-row';
        row.innerHTML = `
            <div>${level}</div>
            <div>${formatValue(data.savings)}</div>
        `;
        resultsContainer.appendChild(row);
        totalSavings += data.savings;
    });
    
    // Update portfolio totals
    document.getElementById('total-savings').textContent = formatValue(totalSavings);
    
    // Update admin savings
    document.getElementById('admin-savings').textContent = formatValue(savings.adminSavings);
    
    // Update grand total (portfolio + admin savings)
    const grandTotal = totalSavings + savings.adminSavings;
    document.getElementById('grand-total-savings').textContent = formatValue(grandTotal);
}

// Calculate and update results
function updateCalculations() {
    const numCompaniesInput = document.getElementById('numCompanies');
    const reminderFrequencySelect = document.getElementById('reminderFrequency');
    const investmentLevelCheckboxes = document.getElementsByName('investmentLevel');
    
    const numCompanies = parseInt(numCompaniesInput.value) || 0;
    const reminderFrequency = reminderFrequencySelect.value;
    const selectedLevels = Array.from(investmentLevelCheckboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.value);
            
    if (selectedLevels.length === 0) {
        // If no levels selected, clear the table
        updateResults({
            totalSavings: 0,
            adminSavings: 0,
            details: {}
        });
        return;
    }
        
    const savings = calculateSavings(numCompanies, selectedLevels, reminderFrequency);
    updateResults(savings);
}

// Add event listeners
document.addEventListener('DOMContentLoaded', function() {
    const numCompaniesInput = document.getElementById('numCompanies');
    const reminderFrequencySelect = document.getElementById('reminderFrequency');
    const investmentLevelCheckboxes = document.getElementsByName('investmentLevel');
    
    // Add input validation for portfolio size
    numCompaniesInput.addEventListener('input', function() {
        let value = parseInt(this.value) || 0;
        if (value < 10) value = 10;
        if (value > 1600) value = 1600;
        this.value = value;
        updateCalculations();
    });
    
    // Add event listeners
    reminderFrequencySelect.addEventListener('change', updateCalculations);
    investmentLevelCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateCalculations);
    });
    
    // Initial calculation
    updateCalculations();
});
