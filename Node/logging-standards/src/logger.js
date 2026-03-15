'use strict';
/**
 * src/logger.js — Shared pino logger factory
 *
 * All loggers in this service MUST be created through createLogger().
 * This ensures:
 *   - Consistent configuration across all modules
 *   - Redaction of sensitive fields (passwords, tokens)
 *   - Log level controlled by LOG_LEVEL environment variable
 *   - Structured JSON output with base fields (service, version, env)
 *   - Error serialiser that includes stack traces as structured fields
 */

const pino = require('pino');

const BASE_FIELDS = {
  service: process.env.SERVICE_NAME || 'unknown-service',
  version: process.env.SERVICE_VERSION || 'unknown',
  env: process.env.NODE_ENV || 'development',
};

const REDACTED_PATHS = [
  'password',
  'token',
  'secret',
  'authorization',
  'req.headers.authorization',
  'req.headers.cookie',
];

/**
 * Creates a child logger bound to the given context fields.
 *
 * @param {Object} context — static fields bound to every log line from this logger
 *   e.g. { module: 'order-service', requestId: '...' }
 * @returns {pino.Logger}
 */
function createLogger(context = {}) {
  const base = pino(
    {
      level: process.env.LOG_LEVEL || 'info',
      base: BASE_FIELDS,
      redact: {
        paths: REDACTED_PATHS,
        censor: '[REDACTED]',
      },
      serializers: {
        err: pino.stdSerializers.err,
        req: pino.stdSerializers.req,
        res: pino.stdSerializers.res,
      },
      timestamp: pino.stdTimeFunctions.isoTime,
      formatters: {
        level(label) {
          return { level: label };
        },
      },
    },
    // In production, write to stdout for the container runtime to capture.
    // In test, suppress output by writing to a no-op stream.
    process.env.NODE_ENV === 'test'
      ? { write: () => {} }
      : process.stdout
  );

  return Object.keys(context).length > 0 ? base.child(context) : base;
}

module.exports = { createLogger };
