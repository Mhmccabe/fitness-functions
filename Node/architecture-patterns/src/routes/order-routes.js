'use strict';
/**
 * src/routes/order-routes.js — ROUTES LAYER (compliant)
 *
 * Architecture rules enforced here:
 *   ✓ Imports only from controllers — never from services or repositories
 *   ✓ Declares HTTP routes and delegates to controllers
 */

const controller = require('../controllers/order-controller');

/**
 * Registers order routes on an Express-compatible router.
 * @param {object} router - Express router instance
 */
function registerRoutes(router) {
  router.post('/orders', controller.createOrder);
  router.get('/orders/:orderId', controller.getOrder);
  router.post('/orders/:orderId/process', controller.processOrder);
}

module.exports = { registerRoutes };
