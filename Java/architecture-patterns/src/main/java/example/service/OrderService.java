package example.service;

import example.repository.OrderRepository;
import example.repository.OrderRepository.Order;

import java.util.Optional;
import java.util.UUID;

/**
 * OrderService — SERVICE LAYER (compliant)
 *
 * Architecture rules enforced here:
 *   ✓ Imports only from example.repository — never from example.controller
 *   ✓ Owns business logic; delegates storage to OrderRepository
 *   ✓ Returns domain objects, not HTTP responses
 */
public class OrderService {

    private final OrderRepository repository;

    public OrderService(OrderRepository repository) {
        this.repository = repository;
    }

    public Order createOrder(String userId, double amount) {
        String orderId = UUID.randomUUID().toString();
        Order order = new Order(orderId, userId, amount, "pending");
        return repository.save(order);
    }

    public Optional<Order> getOrder(String orderId) {
        return repository.findById(orderId);
    }

    public Order processOrder(String orderId) {
        Order order = repository.findById(orderId)
            .orElseThrow(() -> new IllegalArgumentException("Order not found: " + orderId));

        if (order.amount() > 10_000) {
            throw new IllegalArgumentException("Amount exceeds limit");
        }

        Order charged = new Order(order.orderId(), order.userId(), order.amount(), "charged");
        return repository.save(charged);
    }
}
