
const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
const logger = require('./utils/logger');
const authRoutes = require('./routes/auth');
const bloomRoutes = require('./routes/bloom');
const errorHandler = require('./middleware/errorHandler');

const createApp = () => {
  const app = express();
  app.use(helmet());
  app.use(express.json({ limit: '1mb' }));
  app.use(express.urlencoded({ extended: true }));
  app.use(cors());
  if (process.env.NODE_ENV !== 'production') app.use(morgan('dev'));
  const limiter = rateLimit({ windowMs: 60*1000, max: 120 });
  app.use(limiter);
  app.get('/api/health', (req,res) => res.json({ status: 'ok', env: process.env.NODE_ENV }));
  app.use('/api/auth', authRoutes);
  app.use('/api/blooms', bloomRoutes);
  app.use((req,res,next) => res.status(404).json({ message: 'Not Found' }));
  app.use(errorHandler);
  return app;
};

module.exports = createApp;
