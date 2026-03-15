"""
tests/test_order_service.py

Tests for OrderService. These exist to:
  1. Verify the service logic is correct
  2. Contribute to the test coverage metric tracked by SonarQube
  3. Demonstrate that compliant logging does not interfere with testability

Run with:
    pytest tests/ --cov=src --cov-report=term-missing
"""

from __future__ import annotations

import pytest
import structlog
import structlog.testing

from src.order_service import (
    Order,
    OrderNotFoundError,
    OrderService,
    PaymentDeclinedError,
)


SAMPLE_ITEMS = [
    {"sku": "WIDGET-1", "price": 9.99, "qty": 2},
    {"sku": "GADGET-A", "price": 24.99, "qty": 1},
]


@pytest.fixture()
def service() -> OrderService:
    return OrderService()


@pytest.fixture()
def capture_logs():
    """
    Returns a structlog CapturingLogger context.
    Lets tests assert on structured log events without real I/O.
    """
    with structlog.testing.capture_logs() as logs:
        yield logs


class TestCreateOrder:
    def test_creates_order_with_correct_total(self, service: OrderService) -> None:
        order = service.create_order(user_id="u-1", items=SAMPLE_ITEMS)
        assert isinstance(order, Order)
        assert order.user_id == "u-1"
        assert order.total == pytest.approx(9.99 * 2 + 24.99)

    def test_assigns_unique_order_id(self, service: OrderService) -> None:
        order_a = service.create_order(user_id="u-1", items=SAMPLE_ITEMS)
        order_b = service.create_order(user_id="u-1", items=SAMPLE_ITEMS)
        assert order_a.order_id != order_b.order_id

    def test_initial_status_is_pending(self, service: OrderService) -> None:
        order = service.create_order(user_id="u-1", items=SAMPLE_ITEMS)
        assert order.status == "pending"

    def test_logs_order_created_event(self, service: OrderService, capture_logs) -> None:
        order = service.create_order(user_id="u-1", items=SAMPLE_ITEMS)
        created_events = [e for e in capture_logs if e.get("event") == "order.created"]
        assert len(created_events) == 1
        assert created_events[0]["order_id"] == order.order_id
        assert created_events[0]["item_count"] == 2


class TestGetOrder:
    def test_retrieves_existing_order(self, service: OrderService) -> None:
        created = service.create_order(user_id="u-1", items=SAMPLE_ITEMS)
        fetched = service.get_order(created.order_id)
        assert fetched.order_id == created.order_id

    def test_raises_for_unknown_order(self, service: OrderService) -> None:
        with pytest.raises(OrderNotFoundError):
            service.get_order("does-not-exist")

    def test_logs_warning_for_unknown_order(self, service: OrderService, capture_logs) -> None:
        with pytest.raises(OrderNotFoundError):
            service.get_order("missing-id")
        warnings = [e for e in capture_logs if e.get("event") == "order.not_found"]
        assert len(warnings) == 1
        assert warnings[0]["order_id"] == "missing-id"


class TestSubmitOrder:
    def test_submits_pending_order(self, service: OrderService) -> None:
        order = service.create_order(user_id="u-1", items=SAMPLE_ITEMS)
        result = service.submit_order(order.order_id, payment_token="tok_visa")
        assert result.status == "submitted"

    def test_raises_for_declined_payment(self, service: OrderService) -> None:
        order = service.create_order(user_id="u-1", items=SAMPLE_ITEMS)
        with pytest.raises(PaymentDeclinedError):
            service.submit_order(order.order_id, payment_token="DECLINE")

    def test_raises_if_already_submitted(self, service: OrderService) -> None:
        order = service.create_order(user_id="u-1", items=SAMPLE_ITEMS)
        service.submit_order(order.order_id, payment_token="tok_visa")
        with pytest.raises(ValueError, match="not in pending state"):
            service.submit_order(order.order_id, payment_token="tok_visa")

    def test_logs_submission_event(self, service: OrderService, capture_logs) -> None:
        order = service.create_order(user_id="u-1", items=SAMPLE_ITEMS)
        service.submit_order(order.order_id, payment_token="tok_visa")
        submitted_events = [e for e in capture_logs if e.get("event") == "order.submitted"]
        assert len(submitted_events) == 1
        assert submitted_events[0]["order_id"] == order.order_id

    def test_logs_payment_declined_event(self, service: OrderService, capture_logs) -> None:
        order = service.create_order(user_id="u-1", items=SAMPLE_ITEMS)
        with pytest.raises(PaymentDeclinedError):
            service.submit_order(order.order_id, payment_token="DECLINE")
        declined_events = [e for e in capture_logs if e.get("event") == "order.payment_declined"]
        assert len(declined_events) == 1


class TestCancelOrder:
    def test_cancels_pending_order(self, service: OrderService) -> None:
        order = service.create_order(user_id="u-1", items=SAMPLE_ITEMS)
        result = service.cancel_order(order.order_id, reason="customer_request")
        assert result.status == "cancelled"

    def test_raises_for_already_cancelled(self, service: OrderService) -> None:
        order = service.create_order(user_id="u-1", items=SAMPLE_ITEMS)
        service.cancel_order(order.order_id, reason="test")
        with pytest.raises(ValueError, match="Cannot cancel"):
            service.cancel_order(order.order_id, reason="again")

    def test_logs_cancel_event_with_reason(self, service: OrderService, capture_logs) -> None:
        order = service.create_order(user_id="u-1", items=SAMPLE_ITEMS)
        service.cancel_order(order.order_id, reason="fraud_detected")
        cancel_events = [e for e in capture_logs if e.get("event") == "order.cancelled"]
        assert len(cancel_events) == 1
        assert cancel_events[0]["cancel_reason"] == "fraud_detected"
