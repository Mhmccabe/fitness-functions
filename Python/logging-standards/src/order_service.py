"""
src/order_service.py — Realistic service implementation

This is the "real" service code used in tests. It follows all logging
standards and demonstrates patterns you would use in a production service:

  - structlog with processor chain configured at startup
  - Context propagation via bound loggers
  - Structured events with consistent field names
  - Correlation ID injected at the HTTP boundary
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional

import structlog

log = structlog.get_logger()


@dataclass
class Order:
    order_id: str
    user_id: str
    items: list[dict] = field(default_factory=list)
    status: str = "pending"
    total: float = 0.0


class OrderNotFoundError(Exception):
    pass


class PaymentDeclinedError(Exception):
    pass


class OrderService:
    """
    Service for managing orders.

    All methods accept an optional `log` parameter so callers can inject
    a pre-bound logger carrying request-level context (request_id, user_id).
    If not provided, a fresh unbound logger is used — suitable for direct
    calls and tests.
    """

    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}

    def create_order(
        self,
        user_id: str,
        items: list[dict],
        log: Optional[structlog.BoundLogger] = None,
    ) -> Order:
        if log is None:
            log = structlog.get_logger().bind(user_id=user_id)

        order_id = str(uuid.uuid4())
        total = sum(item.get("price", 0) * item.get("qty", 1) for item in items)
        order = Order(order_id=order_id, user_id=user_id, items=items, total=total)
        self._orders[order_id] = order

        log.info(
            "order.created",
            order_id=order_id,
            item_count=len(items),
            total=total,
        )
        return order

    def get_order(
        self,
        order_id: str,
        log: Optional[structlog.BoundLogger] = None,
    ) -> Order:
        if log is None:
            log = structlog.get_logger().bind(order_id=order_id)

        order = self._orders.get(order_id)
        if order is None:
            log.warning("order.not_found", order_id=order_id)
            raise OrderNotFoundError(order_id)

        log.debug("order.fetched", order_id=order_id, status=order.status)
        return order

    def submit_order(
        self,
        order_id: str,
        payment_token: str,
        log: Optional[structlog.BoundLogger] = None,
    ) -> Order:
        if log is None:
            log = structlog.get_logger().bind(order_id=order_id)

        order = self.get_order(order_id, log=log)

        if order.status != "pending":
            log.warning(
                "order.submit_rejected",
                order_id=order_id,
                current_status=order.status,
                reason="not_pending",
            )
            raise ValueError(f"Order {order_id} is not in pending state")

        # Simulate payment — raise if token is the sentinel "DECLINE"
        if payment_token == "DECLINE":
            log.warning(
                "order.payment_declined",
                order_id=order_id,
                total=order.total,
            )
            raise PaymentDeclinedError(order_id)

        order.status = "submitted"
        log.info(
            "order.submitted",
            order_id=order_id,
            total=order.total,
            item_count=len(order.items),
        )
        return order

    def cancel_order(
        self,
        order_id: str,
        reason: str,
        log: Optional[structlog.BoundLogger] = None,
    ) -> Order:
        if log is None:
            log = structlog.get_logger().bind(order_id=order_id)

        order = self.get_order(order_id, log=log)

        if order.status in ("cancelled", "shipped"):
            log.warning(
                "order.cancel_rejected",
                order_id=order_id,
                current_status=order.status,
                reason="terminal_state",
            )
            raise ValueError(f"Cannot cancel order in state {order.status!r}")

        previous_status = order.status
        order.status = "cancelled"
        log.info(
            "order.cancelled",
            order_id=order_id,
            previous_status=previous_status,
            cancel_reason=reason,
        )
        return order
