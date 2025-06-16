/**
 * Mock LCA lookup by UPC.
 * Replace with real database or external-service calls.
 */
async function fetchScoresForUpc(upc) {
  console.log("Fetching scores for UPC:", upc);
  const response = await fetch("http://127.0.0.1:5001/api/assess", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ upc: upc }),
  });

  if (!response.ok) {
    throw new Error(`Server returned an error: ${response.statusText}`);
  }

  const realData = await response.json();
  console.log("Real data fetched:", realData);
  // // pseudo-random but stable based on UPC string
  // const seed = upc.split("").reduce((sum, ch) => sum + ch.charCodeAt(0), 0);
  // const clamp = (x) => Math.max(0, Math.min(100, Math.round(x)));
  // const carbonScore = clamp((seed * 37) % 101);
  // const materialScore = clamp((seed * 73) % 101);
  // const endOfLifeScore = clamp((seed * 59) % 101);

  return realData
  // return {
  //   upc,
  //   carbonScore,
  //   materialScore,
  //   endOfLifeScore,
  //   source: "mock-ecoinvent-v1.0",
  //   fetchedAt: new Date().toISOString(),
  // };
}

module.exports = { fetchScoresForUpc };
