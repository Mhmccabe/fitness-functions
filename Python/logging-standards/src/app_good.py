"""
src/app_good.py — FULLY COMPLIANT reference implementation

Demonstrates every logging standard enforced by the fitness function:

  ✓ structlog only — no print(), no stdlib logging
  ✓ Structured key=value fields — no f-strings in log calls
  ✓ Event names are dot-namespaced strings, not free-form sentences
  ✓ Context bound at function entry — no repeated field passing
  ✓ Log OR raise — never both in the same except block
  ✓ Correlation ID bound at the request boundary
"""

from __future__ import annotations

import structlog

log = structlog.get_logger()

ORDER_DB: dict[str, dict] = {}


def handle_request(request_id: str, order_id: str, user_id: str) -> dict:
    """
    Entry point for a request.

    Binds correlation context at the boundary so every log line emitted
    within this call tree carries request_id, order_id, and user_id
    without repeating them at every call site.
    """
    bound_log = log.bind(request_id=request_id, order_id=order_id, user_id=user_id)
    bound_log.info("request.received")

    result = process_order(order_id=order_id, user_id=user_id, log=bound_log)

    bound_log.info("request.completed", status=result["status"])
    return result


def process_order(order_id: str, user_id: str, log: structlog.BoundLogger | None = None) -> dict:
    """Process an order end-to-end."""
    if log is None:
        log = structlog.get_logger().bind(order_id=order_id, user_id=user_id)

    log.info("order.processing_started")

    try:
        order = _fetch_order(order_id)
    except KeyError:
        # Log the outcome, return — do not re-raise (request is handled)
        log.warning("order.not_found")
        return {"status": "not_found"}

    try:
        result = _charge_payment(order)
    except ValueError as exc:
        # Raise with context — the caller decides whether to log
        # Do NOT log here as well
        raise ValueError(f"Payment rejected for order {order_id}") from exc

    log.info("order.completed", result_status=result["status"], amount=order.get("amount"))
    return result


def _fetch_order(order_id: str) -> dict:
    if order_id not in ORDER_DB:
        raise KeyError(order_id)
    return ORDER_DB[order_id]


def _charge_payment(order: dict) -> dict:
    if order.get("amount", 0) > 10_000:
        raise ValueError("Amount exceeds limit")
    return {"status": "charged", "amount": order.get("amount")}
