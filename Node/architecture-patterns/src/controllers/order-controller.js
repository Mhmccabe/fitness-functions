'use strict';
/**
 * src/controllers/order-controller.js — CONTROLLER LAYER (compliant)
 *
 * Architecture rules enforced here:
 *   ✓ Imports only from services — never from repositories or routes
 *   ✓ Translates between HTTP concerns and domain objects
 *   ✓ Delegates all business logic to order-service
 */

const service = require('../services/order-service');

function createOrder(req, res) {
  const { userId, amount } = req.body;
  const order = service.createOrder(userId, amount);
  res.status(201).json(order);
}

function getOrder(req, res) {
  const order = service.getOrder(req.params.orderId);
  if (!order) {
    return res.status(404).json({ error: 'not_found' });
  }
  return res.json(order);
}

function processOrder(req, res) {
  try {
    const result = service.processOrder(req.params.orderId);
    if (result.status === 'not_found') {
      return res.status(404).json(result);
    }
    return res.json(result);
  } catch (err) {
    return res.status(422).json({ error: err.message });
  }
}

module.exports = { createOrder, getOrder, processOrder };
