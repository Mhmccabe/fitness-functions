'use strict';
/**
 * src/services/order-service.js — SERVICE LAYER (compliant)
 *
 * Architecture rules enforced here:
 *   ✓ Imports only from repositories — never from controllers or routes
 *   ✓ Owns all business logic
 *   ✓ Delegates storage to order-repository
 */

const { randomUUID } = require('node:crypto');
const repository = require('../repositories/order-repository');

function createOrder(userId, amount) {
  const order = { orderId: randomUUID(), userId, amount, status: 'pending' };
  return repository.save(order);
}

function getOrder(orderId) {
  return repository.findById(orderId);
}

function processOrder(orderId) {
  const order = repository.findById(orderId);
  if (!order) {
    return { status: 'not_found' };
  }
  if (order.amount > 10_000) {
    throw new Error('Amount exceeds limit');
  }
  return repository.save({ ...order, status: 'charged' });
}

module.exports = { createOrder, getOrder, processOrder };
