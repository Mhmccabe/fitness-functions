'use strict';
/**
 * src/order-service-bad.js — INTENTIONALLY NON-COMPLIANT
 *
 * Violates every logging standard enforced by the fitness function.
 * Run Semgrep to see all violations:
 *
 *   semgrep --config .semgrep/logging-rules.yml src/order-service-bad.js
 *
 * Expected violations:
 *   Line 20 — no-console-log            (console.log)
 *   Line 26 — no-raw-pino-require       (require('pino') directly)
 *   Line 33 — no-template-literal-in-log (template literal in log.info)
 *   Line 40 — no-console-warn           (console.warn)
 *   Line 49 — no-console-error          (console.error)
 *   Line 52 — no-template-literal-in-log (template literal in log.error)
 */

const orders = new Map();

// VIOLATION: console.log instead of structured logger
console.log('order-service-bad module loaded');

// VIOLATION: require pino directly instead of the shared factory
const pino = require('pino');
const log = pino();

function processOrder(orderId, userId) {
  // VIOLATION: template literal in log call — free text, not queryable fields
  log.info(`Processing order ${orderId} for user ${userId}`);

  const order = orders.get(orderId);
  if (!order) {
    // VIOLATION: console.warn instead of structured logger
    console.warn('Order not found:', orderId);
    return { status: 'not_found' };
  }

  try {
    const result = chargePayment(order);
    log.info(`Order ${orderId} charged successfully`);
    return result;
  } catch (err) {
    // VIOLATION: console.error instead of structured logger
    console.error('Payment failed for order', orderId, err.message);
    // VIOLATION: template literal in log.error — and this is also log-and-rethrow
    log.error(`Payment failed: ${err.message}`);
    throw err;
  }
}

function chargePayment(order) {
  if (order.amount > 10_000) {
    throw new Error('Amount exceeds limit');
  }
  return { status: 'charged', amount: order.amount };
}

module.exports = { processOrder };
