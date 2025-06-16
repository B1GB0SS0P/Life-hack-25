require('dotenv').config();
const express = require('express');
const morgan = require('morgan');
const scoreRouter = require('./routes/score');

const app = express();
app.use(morgan('tiny'));
app.use(express.json());

// Mount score route
app.use('/api/score', scoreRouter);

// Healthcheck
app.get('/healthz', (_, res) => res.json({ status: 'ok' }));

// 404 handler
app.use((_, res) => res.status(404).json({ error: 'Not Found' }));

// Error handler
app.use((err, _, res, __) => {
  console.error(err);
  res.status(500).json({ error: 'Internal Server Error' });
});

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => console.log(`API listening on http://localhost:${PORT}`));
