// services/lcaService.js

// BEFORE (Your likely current code, which is incorrect)
// async function fetchScoresForUpc(upc) {

// AFTER (The corrected version)
async function fetchScoresForUpc({ upc, weights }) { // <-- The ONLY line that needs to change
  console.log("Fetching scores for UPC:", upc);

  // The rest of the function can now access 'upc' and 'weights' correctly
  const bodyPayload = {
    upc: upc,
    weights: weights,
  };

  // This fetch call goes to your Python server
  const response = await fetch("http://127.0.0.1:5001/api/assess", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(bodyPayload),
  });

  if (!response.ok) {
    throw new Error(`Python server returned an error: ${response.statusText}`);
  }

  return response.json();
}

module.exports = { fetchScoresForUpc };