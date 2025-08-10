
const { createLogger, format, transports } = require('winston');
const logger = createLogger({
  level: process.env.NODE_ENV === 'production' ? 'info' : 'debug',
  format: format.combine(format.timestamp(), format.errors({ stack: true }), format.splat(), format.json()),
  defaultMeta: { service: 'algal-bloom-backend' },
  transports: [ new transports.Console({ format: format.combine(format.colorize(), format.simple()) }) ],
});
module.exports = logger;
