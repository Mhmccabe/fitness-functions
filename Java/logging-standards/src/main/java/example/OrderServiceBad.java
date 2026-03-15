package example;

// VIOLATION: importing JUL instead of SLF4J
import java.util.logging.Logger;

// VIOLATION: importing Logback directly instead of SLF4J facade
import ch.qos.logback.classic.LoggerFactory;

import java.util.Map;
import java.util.HashMap;

/**
 * OrderServiceBad — INTENTIONALLY NON-COMPLIANT
 *
 * This class violates every logging standard enforced by the fitness function.
 * Run Semgrep against this file to see all violations detected:
 *
 *   semgrep --config .semgrep/logging-rules.yml src/main/
 *
 * Expected violations:
 *   Line 4  — no-jul-import          (java.util.logging import)
 *   Line 7  — no-direct-logback      (ch.qos.logback import)
 *   Line 21 — no-system-out-println  (System.out.println)
 *   Line 32 — no-string-concat-in-log (string + in logger.info call)
 *   Line 44 — no-string-concat-in-log (string + in logger.error call)
 */
public class OrderServiceBad {

    // VIOLATION: using JUL Logger type
    private static final Logger logger = Logger.getLogger(OrderServiceBad.class.getName());

    private final Map<String, Map<String, Object>> orders = new HashMap<>();

    public Map<String, Object> processOrder(String orderId, String userId) {
        // VIOLATION: System.out.println — no log level, not structured
        System.out.println("Processing order " + orderId);

        Map<String, Object> order = orders.get(orderId);
        if (order == null) {
            // VIOLATION: string concatenation in logger call
            logger.info("Order not found for id " + orderId + " user " + userId);
            return Map.of("status", "not_found");
        }

        try {
            Map<String, Object> result = chargePayment(order);
            return result;
        } catch (RuntimeException e) {
            // VIOLATION: string concatenation in logger.error
            logger.severe("Payment failed for order " + orderId + ": " + e.getMessage());
            throw e; // log-and-throw: duplicate noise in aggregated logs
        }
    }

    private Map<String, Object> chargePayment(Map<String, Object> order) {
        double amount = (double) order.getOrDefault("amount", 0.0);
        if (amount > 10_000) {
            throw new RuntimeException("Amount exceeds limit");
        }
        return Map.of("status", "charged", "amount", amount);
    }
}
