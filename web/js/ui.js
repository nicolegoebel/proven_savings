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

// Format currency values
function formatValue(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

// Add event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const numCompaniesInput = document.getElementById('numCompanies');
    const numCompaniesValue = document.getElementById('numCompaniesValue');
    const investmentLevels = document.getElementsByName('investmentLevel');
    const reminderFrequency = document.getElementById('reminderFrequency');
    const calculateButton = document.getElementById('calculateButton');
    const resultsRows = document.getElementById('results-rows');
    const totalSavings = document.getElementById('total-savings');
    const adminSavings = document.getElementById('admin-savings');
    const grandTotalSavings = document.getElementById('grand-total-savings');

    // Format currency values
    function formatValue(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value);
    }

    // Update results based on current inputs
    function updateResults() {
        const numCompanies = parseInt(numCompaniesInput.value);
        const selectedLevels = Array.from(investmentLevels)
            .filter(cb => cb.checked)
            .map(cb => cb.value);
            
        if (selectedLevels.length === 0) {
            alert('Please select at least one investment level.');
            return;
        }

        const results = calculateSavings(numCompanies, selectedLevels, reminderFrequency.value);
        
        // Clear previous results
        resultsRows.innerHTML = '';
        
        // Add row for each investment level
        Object.entries(results.details).forEach(([level, detail]) => {
            const row = document.createElement('div');
            row.className = 'table-row';
            row.innerHTML = `
                <div>${level}</div>
                <div>${formatValue(detail.savings)}</div>
            `;
            resultsRows.appendChild(row);
        });
        
        // Update totals
        totalSavings.textContent = formatValue(results.totalSavings);
        adminSavings.textContent = formatValue(results.adminSavings);
        grandTotalSavings.textContent = formatValue(results.totalSavings + results.adminSavings);
    }

    // Update slider value display and trigger calculation
    function updateSlider() {
        // Update the display value
        numCompaniesValue.textContent = numCompaniesInput.value;
        // Update calculations
        updateResults();
    }

    // Add event listeners
    numCompaniesInput.addEventListener('input', updateSlider);
    calculateButton.addEventListener('click', updateResults);
    investmentLevels.forEach(cb => cb.addEventListener('change', updateResults));
    reminderFrequency.addEventListener('change', updateResults);

    // Initial update
    updateSlider();
});
