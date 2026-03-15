package example.bad;

import example.repository.OrderRepository;
import example.repository.OrderRepository.Order;

import java.util.Map;
import java.util.Optional;

/**
 * OrderControllerBad — INTENTIONALLY NON-COMPLIANT
 *
 * Violates the layered architecture rules enforced by the fitness function.
 * Run Semgrep to see all violations:
 *
 *   semgrep --config .semgrep/architecture-rules.yml src/main/
 *
 * Expected violations:
 *   Line 3  — no-repository-import-in-controller (controller imports repository directly)
 *   Line 4  — no-repository-import-in-controller (controller imports repository type)
 *   Line 30 — no-repository-import-in-controller (controller instantiates repository directly)
 *
 * ArchUnit will also flag this class during mvn test:
 *   - Classes in package 'bad' that act as controllers access repository layer directly
 */
public class OrderControllerBad {

    // VIOLATION: controller holds a direct reference to the repository
    // instead of going through the service layer
    private final OrderRepository repository;

    public OrderControllerBad() {
        // VIOLATION: controller instantiates repository directly — bypasses service layer
        this.repository = new OrderRepository();
    }

    public Map<String, Object> getOrder(String orderId) {
        // VIOLATION: business logic and data access in the controller
        Optional<Order> order = repository.findById(orderId);
        if (order.isEmpty()) {
            return Map.of("error", "not_found");
        }
        return Map.of("orderId", order.get().orderId(), "status", order.get().status());
    }
}
