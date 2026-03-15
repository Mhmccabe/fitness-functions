#!/usr/bin/env bash
# scripts/setup_sonarqube_metrics.sh
#
# One-time admin setup: registers custom metric definitions and creates
# the Fitness Functions quality gate in SonarQube.
#
# Requires:
#   SONAR_URL   — e.g. https://sonar.example.com
#   SONAR_TOKEN — admin-level token
#
# Run once per SonarQube instance. Safe to re-run (duplicate creates are ignored).

set -euo pipefail

: "${SONAR_URL:?SONAR_URL must be set}"
: "${SONAR_TOKEN:?SONAR_TOKEN must be set}"

AUTH=(-u "${SONAR_TOKEN}:")

echo "=== Registering custom metric definitions ==="

register_metric() {
  local key="$1" name="$2" type="$3" domain="$4"
  echo "  → $key ($type)"
  curl -sf -X POST "${SONAR_URL}/api/custom_metrics/create" \
    "${AUTH[@]}" \
    --data "key=${key}&name=${name}&type=${type}&domain=${domain}" \
    > /dev/null || echo "    (already exists — skipping)"
}

# Observability layer
register_metric "logging_violations"        "Logging standard violations"          "INT"   "Observability"
register_metric "missing_correlation_ids"   "Missing correlation ID log lines"     "INT"   "Observability"

# Performance layer
register_metric "load_test_p95_ms"          "Load test P95 latency (ms)"           "FLOAT" "Performance"
register_metric "load_test_p99_ms"          "Load test P99 latency (ms)"           "FLOAT" "Performance"
register_metric "load_test_error_rate_pct"  "Load test error rate (%)"             "FLOAT" "Performance"

# Frontend layer
register_metric "lighthouse_performance"    "Lighthouse performance score"         "INT"   "Frontend"
register_metric "lighthouse_accessibility"  "Lighthouse accessibility score"       "INT"   "Frontend"
register_metric "bundle_size_kb"            "JS bundle size (KB)"                  "FLOAT" "Frontend"

echo ""
echo "=== Creating Fitness Functions quality gate ==="

# Create the gate
GATE_RESPONSE=$(curl -sf -X POST "${SONAR_URL}/api/qualitygates/create" \
  "${AUTH[@]}" \
  --data "name=Fitness+Functions+Gate")

GATE_ID=$(echo "$GATE_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [[ -z "$GATE_ID" ]]; then
  echo "  Gate may already exist. Fetching existing gate ID..."
  GATE_ID=$(curl -sf "${SONAR_URL}/api/qualitygates/list" \
    "${AUTH[@]}" \
    | grep -o '"id":"[^"]*","name":"Fitness Functions Gate"' \
    | cut -d'"' -f4)
fi

echo "  Gate ID: ${GATE_ID}"
echo ""
echo "=== Adding quality gate conditions ==="

add_condition() {
  local metric="$1" op="$2" error="$3" label="$4"
  echo "  → ${label}: ${metric} ${op} ${error}"
  curl -sf -X POST "${SONAR_URL}/api/qualitygates/create_condition" \
    "${AUTH[@]}" \
    --data "gateId=${GATE_ID}&metric=${metric}&op=${op}&error=${error}" \
    > /dev/null
}

# Security
add_condition "new_security_rating"          "GT" "1"   "New security rating must be A"
add_condition "new_security_hotspots_reviewed" "LT" "100" "All new security hotspots must be reviewed"

# Reliability
add_condition "new_reliability_rating"       "GT" "1"   "New reliability rating must be A"

# Maintainability
add_condition "new_maintainability_rating"   "GT" "1"   "New maintainability rating must be A"
add_condition "new_cognitive_complexity"     "GT" "15"  "New cognitive complexity ≤ 15"
add_condition "new_duplicated_lines_density" "GT" "3"   "New duplication ≤ 3%"
add_condition "new_sqale_debt_ratio"         "GT" "5"   "New technical debt ratio ≤ 5%"

# Coverage
add_condition "new_coverage"                 "LT" "80"  "New code coverage ≥ 80%"

# Observability (custom)
add_condition "logging_violations"           "GT" "0"   "Zero logging standard violations"

# Performance (custom) — set thresholds appropriate to your service
add_condition "load_test_p95_ms"             "GT" "500" "P95 latency ≤ 500ms"
add_condition "load_test_error_rate_pct"     "GT" "1"   "Error rate ≤ 1%"

echo ""
echo "=== Setting gate as default for all projects ==="
curl -sf -X POST "${SONAR_URL}/api/qualitygates/set_as_default" \
  "${AUTH[@]}" \
  --data "id=${GATE_ID}" \
  > /dev/null

echo ""
echo "Done. Gate '${GATE_ID}' is now the default."
echo "Visit ${SONAR_URL}/quality_gates to review it."
