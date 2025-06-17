// Default weights
const defaultWeights = {
    environmental: { ghg: 35, material: 15, water: 10, packaging: 20, eol: 20 },
    social: { labour: 10, safety: 10, trade: 20, sourcing: 20, community: 20, health: 20 },
    governance: { affordability: 20, circular: 25, local: 30, resilience: 15, innovation: 10 }
};

// Map IDs to weight object keys
const weightIds = {
    environmental: { ghg: 'ghg', material: 'material', water: 'water', packaging: 'packaging', eol: 'eol' },
    social: { labour: 'labour', safety: 'safety', trade: 'trade', sourcing: 'sourcing', community: 'community', health: 'health' },
    governance: { affordability: 'affordability', circular: 'circular', local: 'local', resilience: 'resilience', innovation: 'innovation' }
};

// Function to validate weights for a category
function validateCategoryWeights(category) {
    const ids = weightIds[category];
    let total = 0;
    for (const key in ids) {
        total += parseInt(document.getElementById(ids[key]).value, 10) || 0;
    }
    
    const validationDiv = document.getElementById(`${category.slice(0,3)}-validation`);
    if (total === 100) {
        validationDiv.textContent = `Total Weight: 100%`;
        validationDiv.className = 'validation-message validation-success';
        return true;
    } else {
        validationDiv.textContent = `Total Weight must be 100%. Current: ${total}%`;
        validationDiv.className = 'validation-message validation-error';
        return false;
    }
}


// Restore saved preferences and weights on load
document.addEventListener('DOMContentLoaded', () => {
    chrome.storage.sync.get({
        preferredMetric: 'environmentalScore',
        weights: defaultWeights
    }, prefs => {
        // Restore preferred metric
        document.getElementById('metric-select').value = prefs.preferredMetric;

        // Restore weights
        for (const category in prefs.weights) {
            for (const key in prefs.weights[category]) {
                const elementId = weightIds[category][key];
                if(elementId) {
                    document.getElementById(elementId).value = prefs.weights[category][key];
                }
            }
            // Initial validation check on load
            validateCategoryWeights(category);
        }
    });
    
    // Add event listeners to validate on input change
    document.querySelectorAll('.weight-input').forEach(input => {
        input.addEventListener('input', () => {
            // Find which category this input belongs to and validate it
            const category = Object.keys(weightIds).find(cat => Object.values(weightIds[cat]).includes(input.id));
            if(category) {
                validateCategoryWeights(category);
            }
        });
    });
});

// Save on click
document.getElementById('save-btn').onclick = () => {
    // Validate all categories first
    const isEnvValid = validateCategoryWeights('environmental');
    const isSocialValid = validateCategoryWeights('social');
    const isGovValid = validateCategoryWeights('governance');
    
    if (!isEnvValid || !isSocialValid || !isGovValid) {
        alert('Please ensure the weights for each category sum to 100%.');
        return;
    }

    // Get preferred metric
    const preferredMetric = document.getElementById('metric-select').value;
    
    // Build weights object from DOM
    const weightsToSave = {
        environmental: {},
        social: {},
        governance: {}
    };

    for (const category in weightIds) {
        for (const key in weightIds[category]) {
            const elementId = weightIds[category][key];
            weightsToSave[category][key] = parseInt(document.getElementById(elementId).value, 10);
        }
    }

    // Save to chrome storage
    chrome.storage.sync.set({
        preferredMetric: preferredMetric,
        weights: weightsToSave
    }, () => {
        alert('Preferences saved!');
    });
};