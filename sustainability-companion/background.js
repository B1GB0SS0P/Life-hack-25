// const API_BASE = 'https://your-api-host.com/api/score';
const API_BASE = 'http://localhost:4000/api/score';
const CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24h

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'fetchScore' && msg.upc) {
    const key = `score:${msg.upc}`;
    chrome.storage.local.get(key, ({ [key]: cached }) => {
      const now = Date.now();
      // if (cached && now - cached.ts < CACHE_TTL_MS) {
      //   sendResponse({ success: true, data: cached.data, fromCache: true });
      // } else {
        console.log(`🔄CHECK THIS [Eco] Fetching score for UPC ${msg.upc}...`);
        fetch(`${API_BASE}?upc=${msg.upc}`)
          .then(res => {
            if (!res.ok) throw new Error(`Status ${res.status}`);
            return res.json();
          })
          .then(data => {
            chrome.storage.local.set({ [key]: { ts: now, data } }, () => {
              sendResponse({ success: true, data, fromCache: false });
            });
          })
          .catch(err => sendResponse({ success: false, error: err.message }));
      // }
    });
    return true; // keep channel open
  }
});
