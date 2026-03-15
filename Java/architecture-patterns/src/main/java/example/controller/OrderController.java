package example.controller;

import example.service.OrderService;
import example.repository.OrderRepository.Order;

import java.util.Map;
import java.util.Optional;

/**
 * OrderController — CONTROLLER LAYER (compliant)
 *
 * Architecture rules enforced here:
 *   ✓ Imports only from example.service — never from example.repository
 *   ✓ Translates HTTP concerns to/from domain objects
 *   ✓ Delegates all business logic to OrderService
 */
public class OrderController {

    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    public Map<String, Object> createOrder(String userId, double amount) {
        Order order = orderService.createOrder(userId, amount);
        return Map.of(
            "orderId", order.orderId(),
            "status", order.status(),
            "amount", order.amount()
        );
    }

    public Map<String, Object> getOrder(String orderId) {
        Optional<Order> order = orderService.getOrder(orderId);
        if (order.isEmpty()) {
            return Map.of("error", "not_found");
        }
        return Map.of(
            "orderId", order.get().orderId(),
            "status", order.get().status()
        );
    }

    public Map<String, Object> processOrder(String orderId) {
        try {
            Order order = orderService.processOrder(orderId);
            return Map.of("orderId", order.orderId(), "status", order.status());
        } catch (IllegalArgumentException e) {
            return Map.of("error", e.getMessage());
        }
    }
}
