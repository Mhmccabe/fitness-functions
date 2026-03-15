"""Tests for the service layer."""

import pytest
from src.services import order_service


def test_create_order_returns_pending():
    order = order_service.create_order("user-1", 100.0)
    assert order.order_id is not None
    assert order.user_id == "user-1"
    assert order.amount == 100.0
    assert order.status == "pending"


def test_get_order_returns_none_for_unknown():
    result = order_service.get_order("nonexistent")
    assert result is None


def test_process_order_charges_successfully():
    order = order_service.create_order("user-2", 500.0)
    result = order_service.process_order(order.order_id)
    assert result.status == "charged"


def test_process_order_raises_when_amount_exceeds_limit():
    order = order_service.create_order("user-3", 15_000.0)
    with pytest.raises(ValueError, match="Amount exceeds limit"):
        order_service.process_order(order.order_id)


def test_process_order_raises_when_not_found():
    with pytest.raises(ValueError, match="Order not found"):
        order_service.process_order("no-such-id")
