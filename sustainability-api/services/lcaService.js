/**
 * Mock LCA lookup by UPC.
 * Replace with real database or external-service calls.
 */
async function fetchScoresForUpc(upc) {
  // pseudo-random but stable based on UPC string
  const seed = upc.split('').reduce((sum, ch) => sum + ch.charCodeAt(0), 0);
  const clamp = x => Math.max(0, Math.min(100, Math.round(x)));
  const carbonScore    = clamp((seed * 37) % 101);
  const materialScore  = clamp((seed * 73) % 101);
  const endOfLifeScore = clamp((seed * 59) % 101);

  return {
    upc,
    carbonScore,
    materialScore,
    endOfLifeScore,
    source: 'mock-ecoinvent-v1.0',
    fetchedAt: new Date().toISOString()
  };
}

module.exports = { fetchScoresForUpc };
