"""
src/bad/order_api_bad.py — INTENTIONALLY NON-COMPLIANT

Violates the layered architecture rules enforced by the fitness function.
Run Semgrep to see all violations:

  semgrep --config .semgrep/architecture-rules.yml src/

Expected violations:
  Line 16 — no-repository-import-in-api (api imports repository directly)
  Line 17 — no-repository-import-in-api (api imports repository type)
"""

# VIOLATION: API layer imports from repository directly — bypasses service layer
from src.repositories import order_repository
from src.repositories.order_repository import Order


def get_order_bad(order_id: str) -> dict:
    # VIOLATION: data access logic in the API layer
    order = order_repository.find_by_id(order_id)
    if order is None:
        return {"error": "not_found"}
    return order.to_dict()
