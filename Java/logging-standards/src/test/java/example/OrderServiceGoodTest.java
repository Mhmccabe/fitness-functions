package example;

import org.junit.jupiter.api.Test;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

class OrderServiceGoodTest {

    private final OrderServiceGood service = new OrderServiceGood();

    @Test
    void createOrder_returnsOrderWithExpectedFields() {
        Map<String, Object> order = service.createOrder("user-1", 100.0);
        assertNotNull(order.get("orderId"));
        assertEquals("user-1", order.get("userId"));
        assertEquals(100.0, order.get("amount"));
    }

    @Test
    void processOrder_returnsNotFoundForUnknownOrder() {
        Map<String, Object> result = service.processOrder("nonexistent", "user-1");
        assertEquals("not_found", result.get("status"));
    }

    @Test
    void processOrder_chargesValidOrder() {
        Map<String, Object> order = service.createOrder("user-2", 500.0);
        Map<String, Object> result = service.processOrder((String) order.get("orderId"), "user-2");
        assertEquals("charged", result.get("status"));
    }

    @Test
    void processOrder_throwsForAmountExceedingLimit() {
        Map<String, Object> order = service.createOrder("user-3", 20000.0);
        assertThrows(IllegalArgumentException.class, () ->
            service.processOrder((String) order.get("orderId"), "user-3"));
    }
}
