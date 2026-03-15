'use strict';

const { createOrder, getOrder, processOrder } = require('../src/services/order-service');

describe('OrderService', () => {
  test('createOrder returns a pending order with a UUID', () => {
    const order = createOrder('user-1', 100);
    expect(order.orderId).toBeDefined();
    expect(order.userId).toBe('user-1');
    expect(order.amount).toBe(100);
    expect(order.status).toBe('pending');
  });

  test('getOrder returns null for unknown order', () => {
    const result = getOrder('nonexistent');
    expect(result).toBeNull();
  });

  test('processOrder returns charged status', () => {
    const order = createOrder('user-2', 500);
    const result = processOrder(order.orderId);
    expect(result.status).toBe('charged');
  });

  test('processOrder throws when amount exceeds limit', () => {
    const order = createOrder('user-3', 15000);
    expect(() => processOrder(order.orderId)).toThrow('Amount exceeds limit');
  });
});
