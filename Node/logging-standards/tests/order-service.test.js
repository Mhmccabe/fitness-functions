'use strict';

const { processOrder, createOrder } = require('../src/order-service-good');

describe('OrderService', () => {
  test('createOrder returns a pending order with orderId', () => {
    const result = createOrder('user-1', 100);
    expect(result.orderId).toBeDefined();
    expect(result.status).toBe('pending');
    expect(result.amount).toBe(100);
  });

  test('processOrder returns not_found for unknown orderId', () => {
    const result = processOrder('nonexistent-id', 'user-1');
    expect(result.status).toBe('not_found');
  });

  test('processOrder charges a valid order', () => {
    const { orderId } = createOrder('user-2', 500);
    const result = processOrder(orderId, 'user-2');
    expect(result.status).toBe('charged');
  });

  test('processOrder throws for amount exceeding limit', () => {
    const { orderId } = createOrder('user-3', 20000);
    expect(() => processOrder(orderId, 'user-3')).toThrow('Amount exceeds limit');
  });
});
