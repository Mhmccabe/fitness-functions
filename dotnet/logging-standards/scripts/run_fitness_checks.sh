#!/usr/bin/env bash
# scripts/run_fitness_checks.sh
#
# Runs the logging standards fitness function for this .NET project.
#
# Steps:
#   1. Semgrep — static analysis of logging patterns
#   2. dotnet test — unit tests with Coverlet coverage
#   3. sonar-scanner — SonarQube analysis (if configured)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "$PROJECT_DIR"

SEMGREP_RESULTS="semgrep-results.json"
PASSED=true

echo "============================================================"
echo " Fitness Function: .NET Logging Standards"
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

# Exclude *Bad.cs teaching examples from enforcement
semgrep \
  --config .semgrep/logging-rules.yml \
  --config .semgrep/required-fields-rules.yml \
  src/ \
  --exclude="*Bad.cs" \
  --json \
  --output "$SEMGREP_RESULTS" \
  --quiet

VIOLATIONS=$(python3 -c "
import json
data = json.load(open('$SEMGREP_RESULTS'))
print(len(data.get('results', [])))
")

if [[ "$VIOLATIONS" -gt 0 ]]; then
  echo "  FAILED: $VIOLATIONS violation(s) found"
  semgrep --config .semgrep/logging-rules.yml src/ --exclude="*Bad.cs" --quiet 2>&1 || true
  PASSED=false
else
  echo "  PASSED: No logging violations in production files"
fi

# Verify bad files DO trigger violations
echo ""
echo "  Verifying bad example files trigger violations..."
BAD_VIOLATIONS=$(semgrep \
  --config .semgrep/logging-rules.yml \
  src/ \
  --include="*Bad.cs" \
  --json 2>/dev/null \
  | python3 -c "import json,sys; print(len(json.load(sys.stdin).get('results', [])))")

if [[ "$BAD_VIOLATIONS" -gt 0 ]]; then
  echo "  ✓ Bad examples trigger $BAD_VIOLATIONS violations as expected"
else
  echo "  ⚠ Warning: Bad examples trigger no violations — rules may not be working"
fi

echo ""

# ── Step 2: dotnet test ───────────────────────────────────────────────────────
echo ">>> Step 2: dotnet test with coverage"
echo ""

if command -v dotnet &> /dev/null; then
  if dotnet test \
      --collect:"XPlat Code Coverage" \
      --results-directory TestResults \
      --logger "console;verbosity=quiet" \
      -- DataCollectionRunSettings.DataCollectors.DataCollector.Configuration.Format=opencover; then
    echo "  PASSED: Tests passed"
  else
    echo "  FAILED: Tests failed"
    PASSED=false
  fi
else
  echo "  dotnet not found — skipping test step"
fi

echo ""

# ── Step 3: sonar-scanner ────────────────────────────────────────────────────
if command -v sonar-scanner &> /dev/null && [ -n "${SONAR_URL:-}" ]]; then
  echo ">>> Step 3: sonar-scanner"
  sonar-scanner
  echo ""
else
  echo ">>> Step 3: sonar-scanner — skipped (not on PATH or SONAR_URL not set)"
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
