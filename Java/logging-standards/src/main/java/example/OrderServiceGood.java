package example;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * OrderServiceGood — FULLY COMPLIANT reference implementation
 *
 * Demonstrates every logging standard enforced by the fitness function:
 *
 *   ✓ SLF4J only — no JUL, no direct Logback, no System.out
 *   ✓ Logger typed to its own class
 *   ✓ Parameterised {} placeholders — no string concatenation
 *   ✓ MDC used for correlation context (set by CorrelationFilter upstream)
 *   ✓ No log-and-throw — caller decides whether to log exceptions
 */
public class OrderServiceGood {

    // SLF4J facade, typed to own class
    private static final Logger log = LoggerFactory.getLogger(OrderServiceGood.class);

    private final Map<String, Map<String, Object>> orders = new HashMap<>();

    /**
     * Process an order.
     *
     * The correlation ID is expected to be set in MDC by the HTTP filter
     * (see CorrelationFilter.java) before this method is called.
     */
    public Map<String, Object> processOrder(String orderId, String userId) {
        // Bind request-scoped fields to MDC so every log line in this call carries them
        MDC.put("orderId", orderId);
        MDC.put("userId", userId);

        try {
            log.info("order.processing_started");

            Map<String, Object> order = orders.get(orderId);
            if (order == null) {
                // Parameterised placeholder — lazy evaluation, no string allocation
                log.warn("order.not_found orderId={} userId={}", orderId, userId);
                return Map.of("status", "not_found");
            }

            Map<String, Object> result = chargePayment(order);

            log.info("order.completed status={} amount={}", result.get("status"), result.get("amount"));
            return result;

        } finally {
            // Always clean up MDC to prevent context leaks in thread-pool environments
            MDC.remove("orderId");
            MDC.remove("userId");
        }
    }

    /**
     * Raises without logging — the caller decides whether this exception
     * warrants a log entry. No duplicate log entries.
     */
    private Map<String, Object> chargePayment(Map<String, Object> order) {
        double amount = (double) order.getOrDefault("amount", 0.0);
        if (amount > 10_000) {
            throw new IllegalArgumentException("Amount exceeds limit: " + amount);
        }
        return Map.of("status", "charged", "amount", amount);
    }

    public Map<String, Object> createOrder(String userId, double amount) {
        String orderId = UUID.randomUUID().toString();
        Map<String, Object> order = new HashMap<>();
        order.put("orderId", orderId);
        order.put("userId", userId);
        order.put("amount", amount);
        orders.put(orderId, order);

        log.info("order.created orderId={} userId={} amount={}", orderId, userId, amount);
        return order;
    }
}
