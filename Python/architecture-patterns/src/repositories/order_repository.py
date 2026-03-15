"""
src/repositories/order_repository.py — DATA ACCESS LAYER (compliant)

Architecture rules enforced here:
  ✓ No imports from api or services packages
  ✓ Owns all storage interaction
  ✓ Returns plain data dicts; no HTTP concerns
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Order:
    order_id: str
    user_id: str
    amount: float
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


_store: dict[str, Order] = {}


def find_by_id(order_id: str) -> Optional[Order]:
    return _store.get(order_id)


def save(order: Order) -> Order:
    _store[order.order_id] = order
    return order
