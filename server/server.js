
require('dotenv').config();
const http = require('http');
const createApp = require('./app');
const connectDB = require('./config/db');
const logger = require('./utils/logger');

const PORT = parseInt(process.env.PORT || '4000', 10);
const app = createApp();
connectDB(process.env.MONGO_URI || 'mongodb://localhost:27017/algal_bloom_db')
  .then(() => {
    const server = http.createServer(app);
    server.listen(PORT, () => { logger.info(`Server listening on port ${PORT}`); });
    const shutdown = (signal) => {
      logger.info(`Received ${signal}. Shutting down...`);
      server.close(() => { logger.info('HTTP server closed'); process.exit(0); });
      setTimeout(() => { logger.error('Forcing shutdown'); process.exit(1); }, 10000).unref();
    };
    process.on('SIGINT', () => shutdown('SIGINT'));
    process.on('SIGTERM', () => shutdown('SIGTERM'));
  })
  .catch((err) => { logger.error('Failed to start server', err); process.exit(1); });
