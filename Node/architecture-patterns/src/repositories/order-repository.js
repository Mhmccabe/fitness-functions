'use strict';
/**
 * src/repositories/order-repository.js — DATA ACCESS LAYER (compliant)
 *
 * Architecture rules enforced here:
 *   ✓ No imports from controllers, services, or routes
 *   ✓ Owns all storage interaction
 *   ✓ Returns plain data objects; no HTTP concerns
 */

const orders = new Map();

function findById(orderId) {
  return orders.get(orderId) ?? null;
}

function save(order) {
  orders.set(order.orderId, order);
  return order;
}

module.exports = { findById, save };
