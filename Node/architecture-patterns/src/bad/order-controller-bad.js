'use strict';
/**
 * src/bad/order-controller-bad.js — INTENTIONALLY NON-COMPLIANT
 *
 * Violates the layered architecture rules enforced by the fitness function.
 * Run dependency-cruiser to see all violations:
 *
 *   npx depcruise --config .dependency-cruiser.cjs src/bad
 *
 * Expected violations:
 *   Line 14 — no-repository-in-controller (controller imports repository directly)
 *
 * Semgrep will also flag:
 *   Line 14 — no-repository-import-in-controller
 */

// VIOLATION: controller imports repository directly — bypasses service layer
const repository = require('../repositories/order-repository');

function getOrder(req, res) {
  // VIOLATION: business logic and data access in the controller
  const order = repository.findById(req.params.orderId);
  if (!order) {
    return res.status(404).json({ error: 'not_found' });
  }
  return res.json(order);
}

module.exports = { getOrder };
