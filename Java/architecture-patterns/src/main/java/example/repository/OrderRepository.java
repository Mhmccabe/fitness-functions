package example.repository;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

/**
 * OrderRepository — DATA ACCESS LAYER (compliant)
 *
 * Responsibilities:
 *   ✓ Owns all DB/storage interaction
 *   ✓ No imports from controller or service packages
 *   ✓ Exposes a clean interface consumed by the service layer only
 */
public class OrderRepository {

    private final Map<String, Order> store = new HashMap<>();

    public Optional<Order> findById(String orderId) {
        return Optional.ofNullable(store.get(orderId));
    }

    public Order save(Order order) {
        store.put(order.orderId(), order);
        return order;
    }

    public record Order(String orderId, String userId, double amount, String status) {}
}
