
const logger = require('../utils/logger');
function errorHandler(err, req, res, next) {
  logger.error(err);
  const status = err.status || 500;
  const resp = { message: err.message || 'Internal Server Error' };
  if (process.env.NODE_ENV !== 'production') resp.stack = err.stack;
  res.status(status).json(resp);
}
module.exports = errorHandler;
