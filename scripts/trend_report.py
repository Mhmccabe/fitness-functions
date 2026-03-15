#!/usr/bin/env python3
"""
scripts/trend_report.py

Queries SonarQube's measures/search_history API and prints a time-series
trend table for a project's fitness function metrics.

Usage:
    python scripts/trend_report.py --project my-service-key [--days 30]

Environment variables:
    SONAR_URL    — e.g. https://sonar.example.com  (default: http://localhost:9000)
    SONAR_TOKEN  — user or analysis token with Browse permission
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import requests

SONAR_URL = os.environ.get("SONAR_URL", "http://localhost:9000")
SONAR_TOKEN = os.environ.get("SONAR_TOKEN", "")

# Metrics to include in the report, in display order
METRICS = [
    "coverage",
    "new_coverage",
    "new_bugs",
    "new_vulnerabilities",
    "new_security_rating",
    "new_reliability_rating",
    "new_maintainability_rating",
    "new_cognitive_complexity",
    "new_duplicated_lines_density",
    "logging_violations",
    "missing_correlation_ids",
    "load_test_p95_ms",
    "load_test_error_rate_pct",
    "lighthouse_performance",
]

# Metrics where lower is better (for trend arrow direction)
LOWER_IS_BETTER = {
    "new_bugs",
    "new_vulnerabilities",
    "new_cognitive_complexity",
    "new_duplicated_lines_density",
    "logging_violations",
    "missing_correlation_ids",
    "load_test_p95_ms",
    "load_test_error_rate_pct",
}


def fetch_history(project_key: str, metric: str, from_date: str) -> list[dict]:
    """Fetch measure history for a single metric."""
    all_values = []
    page = 1
    while True:
        resp = requests.get(
            f"{SONAR_URL}/api/measures/search_history",
            auth=(SONAR_TOKEN, ""),
            params={
                "component": project_key,
                "metrics": metric,
                "from": from_date,
                "ps": 100,
                "p": page,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        measures = data.get("measures", [])
        if not measures:
            break
        history = measures[0].get("history", [])
        all_values.extend(history)
        total = data.get("paging", {}).get("total", 0)
        if len(all_values) >= total:
            break
        page += 1
    return all_values


def fetch_all_metrics(project_key: str, days: int) -> dict[str, dict[str, str]]:
    """
    Returns: {metric_key: {date_str: value_str}}
    Only includes metrics that actually have data.
    """
    from_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    result: dict[str, dict[str, str]] = {}

    for metric in METRICS:
        try:
            history = fetch_history(project_key, metric, from_date)
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                continue  # metric not registered for this project
            raise
        if history:
            result[metric] = {entry["date"][:10]: entry.get("value", "") for entry in history}

    return result


def collect_dates(metric_data: dict[str, dict[str, str]]) -> list[str]:
    """Return all unique analysis dates across all metrics, sorted."""
    dates: set[str] = set()
    for values in metric_data.values():
        dates.update(values.keys())
    return sorted(dates)


def trend_arrow(values: list[str], metric: str) -> str:
    """Compute trend arrow from a series of value strings."""
    numeric = []
    for v in values:
        try:
            numeric.append(float(v))
        except (ValueError, TypeError):
            pass
    if len(numeric) < 2:
        return "~"
    delta = numeric[-1] - numeric[0]
    if abs(delta) < 0.001:
        return "~"
    improving = delta < 0 if metric in LOWER_IS_BETTER else delta > 0
    return "↑" if improving else "↓"


def format_value(value: str, metric: str) -> str:
    """Format a metric value for display."""
    if not value:
        return "-"
    # Security/reliability/maintainability ratings: 1=A, 2=B, etc.
    if "rating" in metric:
        mapping = {"1": "A", "2": "B", "3": "C", "4": "D", "5": "E"}
        return mapping.get(value, value)
    try:
        f = float(value)
        if f == int(f):
            return str(int(f))
        return f"{f:.1f}"
    except ValueError:
        return value


def print_table(project_key: str, metric_data: dict[str, dict[str, str]], dates: list[str]) -> None:
    # Pick up to 6 most recent dates for display width
    display_dates = dates[-6:]
    date_labels = [d[5:] for d in display_dates]  # MM-DD

    col_w = 12
    name_w = 36
    header = f"{'Metric':<{name_w}}" + "".join(f"{d:>{col_w}}" for d in date_labels) + f"{'Trend':>{col_w}}"
    separator = "-" * len(header)

    print(f"\nFitness function trend report — {project_key}")
    print(separator)
    print(header)
    print(separator)

    for metric in METRICS:
        if metric not in metric_data:
            continue
        values_by_date = metric_data[metric]
        row_values = [values_by_date.get(d, "") for d in display_dates]
        formatted = [format_value(v, metric) for v in row_values]
        arrow = trend_arrow(row_values, metric)
        row = f"{metric:<{name_w}}" + "".join(f"{v:>{col_w}}" for v in formatted) + f"{arrow:>{col_w}}"
        print(row)

    print(separator)
    print("↑ = improving  ↓ = degrading  ~ = stable")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="SonarQube fitness function trend report")
    parser.add_argument("--project", required=True, help="SonarQube project key")
    parser.add_argument("--days", type=int, default=30, help="Number of days of history (default: 30)")
    args = parser.parse_args()

    if not SONAR_TOKEN:
        print("Warning: SONAR_TOKEN is not set. Requests may fail for private projects.", file=sys.stderr)

    print(f"Fetching {args.days} days of history for '{args.project}' from {SONAR_URL} ...")

    try:
        metric_data = fetch_all_metrics(args.project, args.days)
    except requests.ConnectionError:
        print(f"Error: could not connect to {SONAR_URL}", file=sys.stderr)
        sys.exit(1)
    except requests.HTTPError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not metric_data:
        print("No metric data found. Check the project key and that analyses have run.")
        sys.exit(1)

    dates = collect_dates(metric_data)
    print_table(args.project, metric_data, dates)


if __name__ == "__main__":
    main()
