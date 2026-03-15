'use strict';
/**
 * src/order-service-good.js — FULLY COMPLIANT reference implementation
 *
 * Demonstrates every logging standard enforced by the fitness function:
 *
 *   ✓ Shared pino logger factory — no console.*, no direct pino require
 *   ✓ Structured object as first argument — no template literals in log calls
 *   ✓ Static dot-namespaced event names — queryable in any log aggregator
 *   ✓ Correlation context from caller — no repetition at every log site
 *   ✓ Throw OR log — never both in the same catch block
 */

const { createLogger } = require('./logger');
const { randomUUID } = require('crypto');

const log = createLogger({ module: 'order-service' });

const orders = new Map();

/**
 * Process an order.
 *
 * @param {string} orderId
 * @param {string} userId
 * @param {Object} [reqLog] — child logger pre-bound with request context
 *   (e.g. requestId, correlationId). Created by the HTTP handler and
 *   threaded through so all log lines share the same correlation fields.
 */
function processOrder(orderId, userId, reqLog) {
  const boundLog = (reqLog || log).child({ orderId, userId });

  boundLog.info({}, 'order.processing_started');

  const order = orders.get(orderId);
  if (!order) {
    boundLog.warn({}, 'order.not_found');
    return { status: 'not_found' };
  }

  // Raise the exception — the HTTP handler will catch it and decide whether
  // to log it. No duplicate log entries.
  const result = chargePayment(order);

  boundLog.info({ status: result.status, amount: result.amount }, 'order.completed');
  return result;
}

function createOrder(userId, amount) {
  const orderId = randomUUID();
  orders.set(orderId, { orderId, userId, amount });
  log.info({ orderId, userId, amount }, 'order.created');
  return { orderId, status: 'pending', amount };
}

function chargePayment(order) {
  if (order.amount > 10_000) {
    // Raise without logging — caller decides how to handle it
    const err = new Error('Amount exceeds limit');
    err.amount = order.amount;
    throw err;
  }
  return { status: 'charged', amount: order.amount };
}

module.exports = { processOrder, createOrder };
