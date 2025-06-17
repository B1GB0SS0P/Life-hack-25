// background.js or service-worker.js

// This URL should point to your Node.js server, which then calls Python.
// If your Node.js server runs on port 4000, this is correct.
const API_BASE = 'http://localhost:4000/api/score';

// The default weights, to be used if none are in storage
const defaultWeights = {
    environmental: { ghg: 35, material: 15, water: 10, packaging: 20, eol: 20 },
    social: { labour: 10, safety: 10, trade: 20, sourcing: 20, community: 20, health: 20 },
    governance: { affordability: 20, circular: 25, local: 30, resilience: 15, innovation: 10 }
};


chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.action === 'fetchScore' && msg.upc) {
        // We wrap the logic in an async function to use 'await'
        const fetchAndRespond = async () => {
            try {
                // 1. Get the user's saved weights from storage
                const prefs = await new Promise(resolve => {
                    chrome.storage.sync.get({ weights: defaultWeights }, resolve);
                });

                // 2. Prepare the request body
                const bodyPayload = {
                    upc: msg.upc,
                    weights: prefs.weights
                };
                
                console.log(`[Eco] Fetching score for UPC ${msg.upc} with custom weights...`);

                // 3. Make the correct POST request
                const response = await fetch(API_BASE, { // Note: The URL has no query parameters
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(bodyPayload)
                });

                if (!response.ok) {
                    throw new Error(`Server returned status ${response.status}`);
                }

                const data = await response.json();

                // Note: Your caching logic was correctly commented out. The key `score:${msg.upc}`
                // is no longer valid because the score can change if the weights change.
                // You would need a more complex key that includes a hash of the weights.
                // For now, it's best to leave caching disabled.

                sendResponse({ success: true, data: data, fromCache: false });

            } catch (err) {
                console.error('[Eco] Fetch failed:', err);
                sendResponse({ success: false, error: err.message });
            }
        };

        fetchAndRespond();

        return true; // Keep the message channel open for the async response
    }
});