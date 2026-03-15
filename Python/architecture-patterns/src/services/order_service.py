"""
src/services/order_service.py — SERVICE LAYER (compliant)

Architecture rules enforced here:
  ✓ Imports only from src.repositories — never from src.api
  ✓ Owns all business logic
  ✓ Delegates storage to order_repository
"""

from __future__ import annotations
import uuid
from typing import Optional

from src.repositories import order_repository
from src.repositories.order_repository import Order


def create_order(user_id: str, amount: float) -> Order:
    order = Order(
        order_id=str(uuid.uuid4()),
        user_id=user_id,
        amount=amount,
        status="pending",
    )
    return order_repository.save(order)


def get_order(order_id: str) -> Optional[Order]:
    return order_repository.find_by_id(order_id)


def process_order(order_id: str) -> Order:
    order = order_repository.find_by_id(order_id)
    if order is None:
        raise ValueError(f"Order not found: {order_id}")
    if order.amount > 10_000:
        raise ValueError("Amount exceeds limit")
    charged = Order(order.order_id, order.user_id, order.amount, "charged")
    return order_repository.save(charged)
