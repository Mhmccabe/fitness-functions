# Python — Logging Standards Fitness Function

This example enforces logging standards in a Python service as an automated fitness function that runs in CI and tracks compliance over time via SonarQube.

For the full conceptual background, see [tutorial.md](../../tutorial.md).

---

## Standards enforced

### logging-rules.yml — how to log

| Rule | What it prevents |
|---|---|
| No `print()` | Unstructured output that bypasses log levels and aggregation |
| No stdlib `logging` | Mixed log formats; structlog is the single approved logger |
| No f-strings in log calls | Eagerly-evaluated free text; prevents queryable field extraction |
| No log-and-raise | Duplicate log entries as exceptions propagate up the stack |
| No `logging.getLogger()` | Any direct use of the stdlib logger, even without a bare import |

### required-fields-rules.yml — what to log

| Rule | Required field(s) | Triggered when |
|---|---|---|
| `http-event-missing-request-id` | `request_id=` | Any `request.*` event |
| `http-request-completed-missing-status-code` | `status_code=` | `request.completed` event |
| `http-request-completed-missing-duration` | `duration_ms=` | `request.completed` event |
| `batch-event-missing-job-id` | `job_id=` | Any `job.*` event |
| `batch-job-completed-missing-record-count` | `record_count=` | `job.completed` event |
| `batch-job-completed-missing-duration` | `duration_ms=` | `job.completed` event |
| `etl-event-missing-pipeline-id` | `pipeline_id=` | Any `pipeline.*` event |
| `etl-pipeline-completed-missing-row-counts` | `rows_in=`, `rows_out=` | `pipeline.completed` event |
| `async-event-missing-message-id` | `message_id=` | Any `message.*` event |
| `async-event-missing-queue-name` | `queue_name=` | Any `message.*` event |
| `async-message-processed-missing-attempt` | `attempt=` | `message.processed` event |
| `error-event-missing-reason` | `reason=` or `exc_info=` | Any `log.error()` / `log.warning()` |

---

## Quick start

```bash
# Install dependencies (Python 3.11+)
pip install -e ".[dev]"

# Run all fitness checks
./scripts/run_fitness_checks.sh

# Or run steps individually:

# 1. Semgrep — see violations in app_bad.py
semgrep --config .semgrep/logging-rules.yml src/

# 2. Tests with coverage
pytest tests/ --cov=src --cov-report=term-missing

# 3. Push metrics (requires SONAR_URL, SONAR_TOKEN, SONAR_PROJECT_KEY)
python scripts/push_logging_metrics.py
```

---

## File layout

```
.
├── .semgrep/
│   └── logging-rules.yml        ← Semgrep rules (one per logging standard)
├── .github/
│   └── workflows/
│       └── fitness-python-logging.yml  ← CI pipeline
├── src/
│   ├── app_bad.py               ← Intentional violations — verify Semgrep catches them
│   ├── app_good.py              ← Compliant reference — verify Semgrep finds nothing
│   └── order_service.py        ← Realistic service used in tests
├── tests/
│   └── test_order_service.py
├── scripts/
│   ├── run_fitness_checks.sh    ← One command to run everything
│   └── push_logging_metrics.py ← Pushes violation count to SonarQube
├── sonar-project.properties
└── pyproject.toml
```

---

## Verifying the rules work

```bash
# Should report violations in app_bad.py — none in app_good.py
semgrep --config .semgrep/logging-rules.yml src/app_bad.py
semgrep --config .semgrep/logging-rules.yml src/app_good.py
```

Expected output for `app_bad.py`:
```
Findings:
  no-print-statement        src/app_bad.py:15
  no-bare-logging-import    src/app_bad.py:20
  no-logging-getlogger      src/app_bad.py:23
  no-fstring-in-log         src/app_bad.py:34
  no-fstring-in-log         src/app_bad.py:44
  no-log-and-raise          src/app_bad.py:51
```

---

## Tracking over time

After CI pushes metrics to SonarQube, use the trend report to see progress:

```bash
# From the repository root
export SONAR_URL=https://sonar.example.com
export SONAR_TOKEN=your_token
python scripts/trend_report.py --project fitness-functions-python-logging --days 30
```

---

## CI pipeline

The [GitHub Actions workflow](.github/workflows/fitness-python-logging.yml) runs on every push and weekly:

1. **Semgrep** — detect logging violations (fails if any found)
2. **pytest + coverage** — run tests, generate `coverage.xml`
3. **sonar-scanner** — full static analysis, uploads coverage
4. **Push custom metrics** — violation count → `logging_violations` metric in SonarQube
5. **Quality gate** — blocks merge if gate fails

---

## SonarQube setup

Before the first run, register the custom metric and gate condition (admin only):

```bash
# From the repository root
export SONAR_URL=https://sonar.example.com
export SONAR_TOKEN=your_admin_token
./scripts/setup_sonarqube_metrics.sh
```

Then set `SONAR_TOKEN` and `SONAR_HOST_URL` as repository secrets in GitHub.
