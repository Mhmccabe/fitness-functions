#!/usr/bin/env bash
# scripts/run_fitness_checks.sh
#
# Runs the architecture fitness function for this Node project.
#
# Steps:
#   1. Semgrep — static analysis of architecture patterns
#   2. dependency-cruiser — enforce layer boundaries
#   3. Jest — unit tests with coverage
#   4. sonar-scanner — SonarQube analysis (if configured)
#
# Prerequisites: node, semgrep, sonar-scanner (optional)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "$PROJECT_DIR"

SEMGREP_RESULTS="semgrep-results.json"
PASSED=true

echo "============================================================"
echo " Fitness Function: Node Architecture Patterns"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"
echo ""

# ── Step 1: Semgrep ───────────────────────────────────────────────────────────
echo ">>> Step 1: Semgrep — architecture rules"

if ! command -v semgrep &> /dev/null; then
  echo "  semgrep not found. Install with: pip install semgrep" >&2
  exit 1
fi

semgrep \
  --config .semgrep/architecture-rules.yml \
  src/ \
  --exclude="*-bad.js" \
  --json \
  --output "$SEMGREP_RESULTS" \
  --quiet \
  --no-autofix \
  --metrics=off || true

VIOLATIONS=$(python3 -c "
import json
data = json.load(open('$SEMGREP_RESULTS'))
print(len(data.get('results', [])))
")

if [[ "$VIOLATIONS" -gt 0 ]]; then
  echo "  WARNING: $VIOLATIONS violation(s) found"
  PASSED=false
else
  echo "  PASSED: No architecture violations"
fi

echo ""

# ── Step 2: dependency-cruiser + Jest ─────────────────────────────────────────
echo ">>> Step 2: dependency-cruiser + Jest tests"
echo ""

if command -v node &> /dev/null; then
  npm install --silent
  if npm test; then
    echo "  PASSED: Architecture checks and tests succeeded"
  else
    echo "  FAILED: Architecture checks or tests failed" >&2
    PASSED=false
  fi
else
  echo "  node not found — skipping" >&2
fi

echo ""

# ── Step 3: sonar-scanner ─────────────────────────────────────────────────────
if command -v sonar-scanner &> /dev/null && [[ -n "${SONAR_URL:-}" ]]; then
  echo ">>> Step 3: sonar-scanner"
  sonar-scanner
  echo ""
else
  echo ">>> Step 3: sonar-scanner — skipped (not on PATH or SONAR_URL not set)"
  echo ""
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo "============================================================"
if [[ "$PASSED" = true ]]; then
  echo " RESULT: ALL CHECKS PASSED"
  exit 0
else
  echo " RESULT: ONE OR MORE CHECKS FAILED"
  exit 1
fi
