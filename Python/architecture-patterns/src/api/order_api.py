"""
src/api/order_api.py — API LAYER (compliant)

Architecture rules enforced here:
  ✓ Imports only from src.services — never from src.repositories
  ✓ Translates HTTP/request concerns to/from domain objects
  ✓ Delegates all business logic to order_service
"""

from __future__ import annotations
from typing import Any

from src.services import order_service


def create_order(user_id: str, amount: float) -> dict[str, Any]:
    order = order_service.create_order(user_id, amount)
    return order.to_dict()


def get_order(order_id: str) -> dict[str, Any]:
    order = order_service.get_order(order_id)
    if order is None:
        return {"error": "not_found"}
    return order.to_dict()


def process_order(order_id: str) -> dict[str, Any]:
    try:
        order = order_service.process_order(order_id)
        return order.to_dict()
    except ValueError as exc:
        return {"error": str(exc)}
