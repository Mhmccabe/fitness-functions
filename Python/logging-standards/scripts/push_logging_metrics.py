#!/usr/bin/env python3
"""
scripts/push_logging_metrics.py

Reads Semgrep JSON output and pytest-cov XML output, then pushes
the computed metrics into SonarQube as custom measures.

Usage:
    semgrep --config .semgrep/logging-rules.yml src/ --json > semgrep-results.json
    pytest tests/ --cov=src --cov-report=xml:coverage.xml
    python scripts/push_logging_metrics.py

Environment variables:
    SONAR_URL         — e.g. https://sonar.example.com (default: http://localhost:9000)
    SONAR_TOKEN       — token with Execute Analysis permission
    SONAR_PROJECT_KEY — project key in SonarQube
"""

from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET

import requests

SONAR_URL = os.environ.get("SONAR_URL", "http://localhost:9000")
SONAR_TOKEN = os.environ.get("SONAR_TOKEN", "")
PROJECT_KEY = os.environ.get("SONAR_PROJECT_KEY", "")

SEMGREP_RESULTS_PATH = "semgrep-results.json"
COVERAGE_XML_PATH = "coverage.xml"


def count_semgrep_violations(path: str) -> dict[str, int]:
    """
    Parse Semgrep JSON output and return violation counts by rule ID
    plus a total.
    """
    try:
        with open(path) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Warning: {path} not found — assuming 0 violations", file=sys.stderr)
        return {"total": 0}

    results = data.get("results", [])
    by_rule: dict[str, int] = {}
    for finding in results:
        rule_id = finding.get("check_id", "unknown")
        by_rule[rule_id] = by_rule.get(rule_id, 0) + 1

    total = sum(by_rule.values())
    return {"total": total, **by_rule}


def parse_coverage_pct(path: str) -> float:
    """
    Parse pytest-cov XML (Cobertura format) and return overall line coverage %.
    Returns -1.0 if the file is not found.
    """
    try:
        tree = ET.parse(path)
    except FileNotFoundError:
        print(f"Warning: {path} not found — skipping coverage metric", file=sys.stderr)
        return -1.0

    root = tree.getroot()
    line_rate = root.get("line-rate", "0")
    return round(float(line_rate) * 100, 1)


def push_metric(metric_key: str, value: int | float) -> None:
    """Push a single custom measure to SonarQube."""
    if not PROJECT_KEY:
        print(f"  (dry run) {metric_key} = {value}", file=sys.stderr)
        return

    response = requests.post(
        f"{SONAR_URL}/api/custom_measures/create",
        auth=(SONAR_TOKEN, ""),
        data={
            "projectKey": PROJECT_KEY,
            "metricKey": metric_key,
            "value": str(value),
        },
        timeout=30,
    )
    try:
        response.raise_for_status()
        print(f"  ✓ {metric_key} = {value}")
    except requests.HTTPError as exc:
        print(f"  ✗ {metric_key}: {exc} — {response.text}", file=sys.stderr)


def main() -> None:
    if not SONAR_TOKEN and PROJECT_KEY:
        print("Warning: SONAR_TOKEN is not set", file=sys.stderr)

    print("=== Parsing Semgrep results ===")
    violations = count_semgrep_violations(SEMGREP_RESULTS_PATH)
    total_violations = violations["total"]
    print(f"  Total violations: {total_violations}")
    for rule, count in violations.items():
        if rule != "total":
            print(f"    {rule}: {count}")

    print("")
    print("=== Parsing coverage report ===")
    coverage_pct = parse_coverage_pct(COVERAGE_XML_PATH)
    if coverage_pct >= 0:
        print(f"  Line coverage: {coverage_pct}%")

    print("")
    print("=== Pushing metrics to SonarQube ===")
    push_metric("logging_violations", total_violations)
    if coverage_pct >= 0:
        push_metric("test_coverage_pct", coverage_pct)

    print("")
    if total_violations > 0:
        print(f"FAILED: {total_violations} logging standard violation(s) detected.")
        print("Fix the violations listed above, then re-run.")
        sys.exit(1)
    else:
        print("PASSED: No logging violations.")


if __name__ == "__main__":
    main()
