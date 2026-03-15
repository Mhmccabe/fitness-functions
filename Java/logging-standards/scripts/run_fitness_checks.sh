#!/usr/bin/env bash
# scripts/run_fitness_checks.sh
#
# Runs the logging standards fitness function for this Java project.
#
# Steps:
#   1. Semgrep — static analysis of logging patterns
#   2. Maven build + tests with JaCoCo coverage
#   3. sonar-scanner — SonarQube analysis (if configured)
#
# Prerequisites: semgrep, mvn, sonar-scanner (optional)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "$PROJECT_DIR"

SEMGREP_RESULTS="semgrep-results.json"
PASSED=true

echo "============================================================"
echo " Fitness Function: Java Logging Standards"
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
  src/main/ \
  --json \
  --output "$SEMGREP_RESULTS" \
  --quiet

VIOLATIONS=$(python3 -c "
import json
data = json.load(open('$SEMGREP_RESULTS'))
print(len(data.get('results', [])))
")

if [ "$VIOLATIONS" -gt 0 ]; then
  echo "  FAILED: $VIOLATIONS violation(s) found"
  semgrep --config .semgrep/logging-rules.yml src/main/ --quiet 2>&1 || true
  PASSED=false
else
  echo "  PASSED: No logging violations"
fi

echo ""

# ── Step 2: Maven build + tests ───────────────────────────────────────────────
echo ">>> Step 2: Maven build + tests"
echo ""

if command -v mvn &> /dev/null; then
  if mvn clean verify -q; then
    echo "  PASSED: Build and tests succeeded"
  else
    echo "  FAILED: Build or tests failed"
    PASSED=false
  fi
else
  echo "  mvn not found — skipping build step"
fi

echo ""

# ── Step 3: sonar-scanner ────────────────────────────────────────────────────
if command -v sonar-scanner &> /dev/null && [ -n "${SONAR_URL:-}" ]; then
  echo ">>> Step 3: sonar-scanner"
  sonar-scanner
  echo ""
else
  echo ">>> Step 3: sonar-scanner — skipped (not on PATH or SONAR_URL not set)"
  echo ""
fi

# ── Summary ──────────────────────────────────────────────────────────────────
echo "============================================================"
if [ "$PASSED" = true ]; then
  echo " RESULT: ALL CHECKS PASSED"
  exit 0
else
  echo " RESULT: ONE OR MORE CHECKS FAILED"
  exit 1
fi
