const CACHE = new Map();
const TTL_MS = (Number(process.env.CACHE_TTL) || 86400) * 1000;

function get(key) {
  const entry = CACHE.get(key);
  if (!entry) return null;
  if (Date.now() > entry.expiry) {
    CACHE.delete(key);
    return null;
  }
  return entry.value;
}

function set(key, value) {
  CACHE.set(key, {
    value,
    expiry: Date.now() + TTL_MS
  });
}

module.exports = { get, set };
