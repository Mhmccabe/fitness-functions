"""
src/app_bad.py — INTENTIONALLY NON-COMPLIANT

This file violates every logging standard enforced by the fitness function.
Run Semgrep against this file to see all violations detected:

    semgrep --config .semgrep/logging-rules.yml src/app_bad.py
    semgrep --config .semgrep/required-fields-rules.yml src/app_bad.py

logging-rules.yml violations:
  Line 21  — no-print-statement      (print() instead of structlog)
  Line 26  — no-bare-logging-import  (import logging)
  Line 29  — no-logging-getlogger    (logging.getLogger())
  Line 40  — no-fstring-in-log       (f-string in log call)
  Line 47  — no-fstring-in-log       (%-format in log call)
  Line 55  — no-log-and-raise        (log then re-raise)

required-fields-rules.yml violations:
  Line 81  — http-event-missing-request-id        (request.received without request_id=)
  Line 86  — http-request-completed-missing-status-code  (request.completed without status_code=)
  Line 91  — batch-event-missing-job-id           (job.started without job_id=)
  Line 96  — batch-job-completed-missing-record-count   (job.completed without record_count=)
  Line 101 — error-event-missing-reason           (log.error without reason= or exc_info=)
"""

import os

# VIOLATION: print() — no log level, not structured, not aggregatable
print("Application starting up")


# VIOLATION: stdlib logging import
import logging

# VIOLATION: logging.getLogger() instead of structlog.get_logger()
logger = logging.getLogger(__name__)

ORDER_DB: dict[str, dict] = {}


def process_order(order_id: str, user_id: str) -> dict:
    # VIOLATION: f-string in log call — eagerly evaluated, free-text output
    logger.info(f"Processing order {order_id} for user {user_id}")

    try:
        order = _fetch_order(order_id)
    except KeyError:
        # VIOLATION: f-string in log call (% format variant)
        logger.error("Order %s not found for user %s" % (order_id, user_id))
        return {"status": "not_found"}

    try:
        result = _charge_payment(order)
        return result
    except RuntimeError as exc:
        # VIOLATION: log-and-raise — caller will also log this, producing duplicates
        logger.error("Payment failed for order %s: %s", order_id, str(exc))
        raise


def _fetch_order(order_id: str) -> dict:
    if order_id not in ORDER_DB:
        raise KeyError(order_id)
    return ORDER_DB[order_id]


def _charge_payment(order: dict) -> dict:
    if order.get("amount", 0) > 10_000:
        raise RuntimeError("Amount exceeds limit")
    return {"status": "charged", "amount": order.get("amount")}


# VIOLATION: print() at module level — not structured, no log level
print(f"Module loaded: {__name__}")


# =============================================================================
# REQUIRED FIELDS VIOLATIONS — violations of required-fields-rules.yml
#
# These use structlog (the correct logger) but are missing required fields
# for their workload type. This demonstrates that "using the right logger"
# is not sufficient — the right fields must also be present.
# =============================================================================

import structlog as _structlog

_log = _structlog.get_logger()


def handle_http_request_bad(request_id: str, method: str, path: str) -> dict:  # noqa: ARG001
    # VIOLATION: http-event-missing-request-id
    # request_id is available but deliberately not passed to the log call —
    # that omission is exactly what the rule catches.
    _log.info("request.received", method=method, path=path)

    # VIOLATION: http-request-completed-missing-status-code
    # request.completed event is missing status_code= and duration_ms=
    _log.info("request.completed", path=path)

    return {"status": 200}


def run_batch_job_bad(job_name: str) -> None:
    # VIOLATION: batch-event-missing-job-id
    # Event name starts with "job." but job_id= is absent
    _log.info("job.started", job_name=job_name)

    # VIOLATION: batch-job-completed-missing-record-count
    # job.completed is missing record_count= and duration_ms=
    _log.info("job.completed", job_name=job_name, status="completed")


def handle_payment_error_bad(order_id: str) -> None:
    # VIOLATION: error-event-missing-reason
    # log.error without reason= or exc_info= — no actionable context for on-call
    _log.error("payment.failed", order_id=order_id)
