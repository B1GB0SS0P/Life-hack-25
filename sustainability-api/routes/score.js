// routes/score.js (This file is correct, no changes needed)

const express = require('express');
const crypto = require('crypto');
const { get, set } = require('../utils/cache');
const { fetchScoresForUpc } = require('../services/lcaService'); // It imports the function
const router = express.Router();

router.post('/', async (req, res, next) => {
    try {
        const { upc, weights } = req.body;
        console.log(`Received request for UPC: ${upc}`);

        if (!upc) {
            return res.status(400).json({ error: 'Missing upc parameter in body' });
        }

        const weightsHash = crypto.createHash('md5').update(JSON.stringify(weights || {})).digest('hex');
        const cacheKey = `score:${upc}:${weightsHash}`;

        let payload = get(cacheKey);
        if (payload) {
            console.log("Returning cached payload for key:", cacheKey);
            res.json(payload);
        } else {
            console.log("No cache hit. Fetching from service for key:", cacheKey);
            // This call correctly passes the whole body object
            payload = await fetchScoresForUpc(req.body);
            set(cacheKey, payload);
            res.json(payload);
        }
    } catch (err) {
        console.error('Error fetching scores:', err);
        next(err);
    }
});

module.exports = router;