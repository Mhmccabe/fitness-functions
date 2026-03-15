#!/usr/bin/env bash
# scripts/run_fitness_checks.sh
#
# Runs the complete logging standards fitness function for this Python project.
#
# Steps:
#   1. Semgrep — static analysis of logging patterns
#   2. pytest  — tests with coverage report
#   3. Push metrics to SonarQube (if SONAR_PROJECT_KEY is set)
#   4. sonar-scanner — full static analysis (if sonar-scanner is on PATH)
#
# Exit code: 0 = all checks passed, non-zero = one or more failed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "$PROJECT_DIR"

SEMGREP_RESULTS="semgrep-results.json"
COVERAGE_XML="coverage.xml"
PASSED=true

echo "============================================================"
echo " Fitness Function: Python Logging Standards"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"
echo ""

# ── Step 1: Semgrep ───────────────────────────────────────────────────────────
echo ">>> Step 1: Semgrep — logging rules + required fields"
echo ""

if ! command -v semgrep &> /dev/null; then
  echo "  semgrep not found. Install with: pip install semgrep"
  exit 1
fi

semgrep \
  --config .semgrep/logging-rules.yml \
  --config .semgrep/required-fields-rules.yml \
  src/ \
  --json \
  --output "$SEMGREP_RESULTS" \
  --quiet

VIOLATIONS=$(python3 -c "
import json, sys
data = json.load(open('$SEMGREP_RESULTS'))
results = data.get('results', [])
print(len(results))
")

if [[ "$VIOLATIONS" -gt 0 ]]; then
  echo "  FAILED: $VIOLATIONS violation(s) found"
  # Print human-readable output for the CI log
  semgrep --config .semgrep/logging-rules.yml src/ --quiet 2>&1 || true
  PASSED=false
else
  echo "  PASSED: No logging violations"
fi

echo ""

# ── Step 2: pytest with coverage ─────────────────────────────────────────────
echo ">>> Step 2: Tests with coverage"
echo ""

if ! python3 -m pytest tests/ \
    --cov=src \
    --cov-report=xml:"$COVERAGE_XML" \
    --cov-report=term-missing \
    --tb=short \
    -q; then
  echo ""
  echo "  FAILED: Tests failed"
  PASSED=false
else
  COVERAGE=$(python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('$COVERAGE_XML')
rate = float(tree.getroot().get('line-rate', 0)) * 100
print(f'{rate:.1f}')
" 2>/dev/null || echo "N/A")
  echo ""
  echo "  PASSED: Tests passed (coverage: ${COVERAGE}%)"
fi

echo ""

# ── Step 3: Push metrics to SonarQube ────────────────────────────────────────
if [[ -n "${SONAR_PROJECT_KEY:-}" ]]; then
  echo ">>> Step 3: Pushing metrics to SonarQube"
  echo ""
  python3 scripts/push_logging_metrics.py || PASSED=false
  echo ""
else
  echo ">>> Step 3: SonarQube push — skipped (SONAR_PROJECT_KEY not set)"
  echo ""
fi

# ── Step 4: sonar-scanner ────────────────────────────────────────────────────
if command -v sonar-scanner &> /dev/null && [ -n "${SONAR_URL:-}" ]]; then
  echo ">>> Step 4: sonar-scanner"
  echo ""
  sonar-scanner
  echo ""
else
  echo ">>> Step 4: sonar-scanner — skipped (not on PATH or SONAR_URL not set)"
  echo ""
fi

# ── Summary ──────────────────────────────────────────────────────────────────
echo "============================================================"
if [[ "$PASSED" = true ]]; then
  echo " RESULT: ALL CHECKS PASSED"
  exit 0
else
  echo " RESULT: ONE OR MORE CHECKS FAILED"
  exit 1
fi
