const express = require('express');
const { get, set } = require('../utils/cache');
const { fetchScoresForUpc } = require('../services/lcaService');
const router = express.Router();

router.get('/', async (req, res, next) => {
  try {
    const { upc } = req.query;
    if (!upc) return res.status(400).json({ error: 'Missing upc parameter' });

    const cacheKey = `score:${upc}`;
    let payload = get(cacheKey);
    if (!payload) {
      payload = await fetchScoresForUpc(upc);
      set(cacheKey, payload);
    }
    res.json(payload);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
