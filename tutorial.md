# Fitness Functions: A Practical Tutorial

## What is a fitness function?

The term comes from evolutionary computing, where a fitness function scores how close a candidate solution is to the desired goal. Neal Ford, Rebecca Parsons, and Patrick Kua borrowed it in *Building Evolutionary Architectures* (O'Reilly, 2017) to describe any mechanism that provides an objective, automated assessment of an architectural characteristic.

In plain terms: **a fitness function is an executable test that verifies your system still has a property you care about.**

Unlike a unit test, which verifies a single behaviour, a fitness function verifies a system-wide property — security posture, module coupling, logging compliance, test coverage, latency budget. It runs in your CI/CD pipeline and fails the build when the property is violated.

```
Fitness function = automated check + quality threshold + pipeline gate
```

### Why this matters

Code quality degrades gradually. No single commit destroys a codebase — it is the accumulated weight of a hundred small shortcuts. Without automated constraints, every code review becomes a subjective negotiation about standards that should be non-negotiable.

Fitness functions flip this: they make the standard **executable**. The constraint lives in the repository alongside the code. It runs on every PR. It is not a suggestion.

---

## The ratchet principle

A fitness function is most powerful when it is a **ratchet**: once you improve a metric, the gate tightens to prevent regression.

SonarQube's "Clean as You Code" mode implements this naturally — it gates on *new* code only, so you can improve incrementally without being blocked by historical debt. But you track the overall trend too, so you know whether the codebase is getting better or worse over time.

```
Ratchet: current best → new floor → never go back
```

Track both:
- **Gate on new code** — so the PR can never make things worse
- **Trend the overall metric** — so you can see whether old debt is being paid down

---

## The 7-layer fitness function strategy

A mature pipeline should enforce constraints at every layer. No single tool covers all of them.

| Layer | Primary tool | What it gates on |
|---|---|---|
| Static analysis | SonarQube | Security, complexity, coverage, duplication, smells |
| Architecture | ArchUnit (Java) / dependency-cruiser (Node) / NDepend (.Net) | Layer boundaries, naming, dependency cycles |
| Observability standards | Semgrep | Logging patterns, structured output, tracing annotations |
| Secrets | SonarQube + Gitleaks | Hardcoded credentials, 400+ secret patterns |
| Dependencies | SonarQube Advanced Security / OWASP Dependency-Check | CVEs in third-party libraries |
| Performance | k6 / Gatling + custom metric push to SonarQube | Latency thresholds, throughput |
| Frontend / Infra | Lighthouse CI / Checkov + OPA | Core Web Vitals, IaC policy, cost limits |

These tools are not alternatives — they are **complementary layers**. SonarQube covers static analysis and secrets deeply. Semgrep fills the observability gap. Architecture tools enforce structural constraints. Performance tools measure runtime reality.

---

## SonarQube as the central hub

SonarQube acts as the reporting and gating hub even for the things it cannot measure directly. The key mechanism is its **custom metrics API**: you run an external tool, extract a number, and push it into SonarQube. The quality gate can then block on it.

### Quality gate lifecycle

```
1. sonar-scanner runs → analysis sent to SonarQube
2. SonarQube evaluates quality gate conditions
3. sonar.qualitygate.wait=true → pipeline blocks until verdict
4. Gate PASSED → PR can merge
5. Gate FAILED → PR is blocked; developer sees which condition failed
```

### Clean as You Code

Set `sonar.newCode.referenceBranch=main` in `sonar-project.properties`. All gate conditions then apply to **new code only**. This prevents legacy debt from blocking current work while still enforcing that new contributions meet the standard.

### Registering custom metrics (one-time, admin)

```bash
# Register the metric definition
curl -X POST "$SONAR_URL/api/custom_metrics/create" \
  -u "$SONAR_TOKEN:" \
  --data "key=logging_violations&name=Logging standard violations&type=INT&domain=Observability"

# Add a gate condition: zero violations required
curl -X POST "$SONAR_URL/api/qualitygates/create_condition" \
  -u "$SONAR_TOKEN:" \
  --data "gateId=$GATE_ID&metric=logging_violations&op=GT&error=0"
```

See `scripts/setup_sonarqube_metrics.sh` for a complete setup script.

### Pushing external results

```python
# After running Semgrep, count violations and push
def push_metric(metric_key: str, value: int | float):
    requests.post(
        f"{SONAR_URL}/api/custom_measures/create",
        auth=(SONAR_TOKEN, ""),
        data={"projectKey": PROJECT_KEY, "metricKey": metric_key, "value": str(value)},
    ).raise_for_status()

push_metric("logging_violations", semgrep_violation_count)
```

---

## Semgrep for observability standards

SonarQube's built-in rules catch some logging anti-patterns (`java:S2629`, `python:S2629`) but cannot enforce organisation-specific conventions like:

- "All services must use `structlog` — not the stdlib `logging` module"
- "Logger must be injected as `ILogger<T>`, not instantiated directly"
- "Every SLF4J logger must be typed to its own class"
- "No `console.log` — use the shared `pino` factory"

Semgrep fills this gap. It uses pattern-matching rules written in YAML. The rules live in the repository, run in CI, and produce a machine-countable violation list that you push to SonarQube.

```yaml
# .semgrep/logging-rules.yml
rules:
  - id: no-print-statement
    languages: [python]
    severity: ERROR
    message: "Use structlog instead of print() in production code"
    pattern: print(...)
```

```bash
# Count violations, fail if any
VIOLATIONS=$(semgrep --config .semgrep/logging-rules.yml src/ --json \
  | jq '.results | length')
if [ "$VIOLATIONS" -gt 0 ]; then exit 1; fi
```

---

## Required log fields

Structured logging ensures your log output is machine-readable. Required field standards ensure it is also machine-*useful* — carrying the context that makes alerting, correlation, and filtering reliable.

Without a field standard, you end up with structlog output that is technically JSON but practically unqueryable: correlation IDs missing from half the services, no duration on completion events, error logs with no indication of why something failed.

### Baseline fields (all events)

These fields must appear on every log event. They are enforced **structurally** — set once in the logger factory or processor chain, not repeated at every call site.

| Field | Description | How enforced |
|---|---|---|
| `correlation_id` | Trace/request ID linking all log lines for one unit of work | Set in logger factory / HTTP middleware; propagated via `log.bind()` |
| `service` | Service name | Set as a base field in the logger factory |
| `event` | Dot-namespaced event name e.g. `order.created` | Convention; the `no-fstring-in-log` Semgrep rule prevents free-text event names |
| `level` | Log level (info/warn/error/debug) | Output by the logging framework automatically |

### Workload-tier fields

Different workload types need additional fields. These are enforced by `.semgrep/required-fields-rules.yml` — Semgrep matches on the event name prefix and checks that the required fields are present in the call.

#### HTTP requests — events prefixed `request.*`

| Field | Description |
|---|---|
| `request_id` | Unique ID for this HTTP request |
| `method` | HTTP verb (GET, POST, etc.) |
| `path` | URL path |
| `status_code` | HTTP response code — required on `request.completed` |
| `duration_ms` | Request duration in milliseconds — required on `request.completed` |

```python
# Python / structlog — bind at the handler boundary
bound_log = log.bind(request_id=request_id, method=method, path=path)
# ... handler logic ...
bound_log.info("request.completed", status_code=200, duration_ms=42)
```

#### Batch jobs — events prefixed `job.*`

| Field | Description |
|---|---|
| `job_id` | Unique ID for this job run |
| `job_name` | Name/type of the job |
| `record_count` | Records processed — required on `job.completed` |
| `duration_ms` | Total job duration — required on `job.completed` |
| `status` | Terminal status: `completed`, `failed`, `partial` |

```python
bound_log = log.bind(job_id=job_id, job_name="nightly-reconciliation")
bound_log.info("job.started")
# ... job logic ...
bound_log.info("job.completed", record_count=14_203, duration_ms=8_421, status="completed")
```

#### ETL pipelines — events prefixed `pipeline.*`

| Field | Description |
|---|---|
| `pipeline_id` | Unique ID for this pipeline run |
| `source` | Data source identifier |
| `destination` | Data destination identifier |
| `rows_in` | Rows read from source — required on `pipeline.completed` |
| `rows_out` | Rows written to destination — required on `pipeline.completed` |
| `error_count` | Rows rejected/errored — required on `pipeline.completed` |

```python
bound_log = log.bind(pipeline_id=run_id, source="s3://raw", destination="postgres://dw")
bound_log.info("pipeline.started")
# ... ETL logic ...
bound_log.info("pipeline.completed", rows_in=50_000, rows_out=49_871, error_count=129)
```

#### Async / queue workers — events prefixed `message.*`

| Field | Description |
|---|---|
| `message_id` | Unique message/task ID |
| `queue_name` | Queue or topic name |
| `attempt` | Attempt number (1 = first try) — required on `message.processed` |
| `duration_ms` | Processing duration |

```python
bound_log = log.bind(message_id=msg.id, queue_name="orders-to-fulfill", attempt=msg.receive_count)
bound_log.info("message.received")
# ... handler logic ...
bound_log.info("message.processed", duration_ms=312)
```

### How the Semgrep rules work

Each workload tier has its own rule file: `.semgrep/required-fields-rules.yml`. The rules use a `patterns` + `pattern-not` approach:

```yaml
- id: http-event-missing-request-id
  languages: [python]
  severity: ERROR
  message: "Events prefixed 'request.' must include request_id="
  patterns:
    - pattern: $LOG.$M("request.$EVT", ...)
    - pattern-not: $LOG.$M("request.$EVT", ..., request_id=..., ...)
```

This matches any log call whose event name starts with `request.` — and flags it if `request_id=` is absent. Run both rule files together:

```bash
semgrep \
  --config .semgrep/logging-rules.yml \
  --config .semgrep/required-fields-rules.yml \
  src/
```

### Error events — always include a reason

Regardless of workload type, every `log.error()` or `log.warning()` call must include either a `reason` field (for expected failure modes) or an exception reference (for unexpected errors):

```python
# Expected failure — use reason=
log.warning("payment.declined", reason="insufficient_funds", order_id=order_id)

# Unexpected error — pass exc_info or the exception
log.error("payment.gateway_timeout", exc_info=True, order_id=order_id)
```

Without one of these, on-call engineers cannot distinguish a card decline from a network timeout from a bug.

---

## Tracking metrics over time

A single quality gate gives you a pass/fail on each commit. Trends tell you whether the codebase is improving or decaying over weeks and months.

### SonarQube history API

```bash
# Get metric history for the last 30 analyses
curl -s "$SONAR_URL/api/measures/search_history" \
  -u "$SONAR_TOKEN:" \
  --data "component=$PROJECT_KEY&metrics=coverage,logging_violations,new_bugs&ps=30"
```

The response contains a time-series array per metric. `scripts/trend_report.py` queries this API and renders a readable table with trend indicators.

### Scheduled CI runs

Beyond per-commit analysis, schedule a weekly full scan to build trend data even in quiet periods. In GitHub Actions:

```yaml
on:
  push:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'   # every Monday at 06:00 UTC
```

### Reading the trend report

```
$ python scripts/trend_report.py --project my-service --days 30

Metric                    2026-02-17  2026-02-24  2026-03-03  2026-03-10  Trend
coverage                  71.2        73.8        74.1        76.4        ↑
logging_violations        12          8           3           0           ↑
new_bugs                  0           0           1           0           ~
new_security_rating       A           A           A           A           ~
```

Trend indicators: `↑` improving, `↓` degrading, `~` stable.

---

## The logging standards fitness function — end-to-end walkthrough

This section walks through the Python example in `Python/logging-standards/`. The same pattern repeats in Java, Node, and .Net.

### The problem

Without automated enforcement, logging standards drift:

```python
# Grows organically across a codebase:
print(f"Processing order {order_id}")              # no log level, no structure
import logging; logging.info("done")               # stdlib, not structlog
logger.error(f"Failed: {e}")                       # f-string, not structured
except Exception as e:
    logger.error("something broke")
    raise                                           # log-and-raise: duplicate noise
```

After six months, your observability platform receives a mixture of plain text and structured JSON. Correlation IDs appear in some services and not others. Alerting becomes unreliable.

### The fitness function

1. **Semgrep rules** detect each violation type statically
2. **Violation count pushed to SonarQube** as `logging_violations`
3. **Quality gate** fails if `logging_violations > 0`
4. **Trend report** shows whether compliance is improving

### Running it locally

```bash
cd Python/logging-standards

# Install dependencies
pip install -e ".[dev]"

# Run all fitness checks
./scripts/run_fitness_checks.sh

# View violation detail
semgrep --config .semgrep/logging-rules.yml src/

# Run tests with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

### What the bad example violates

`src/app_bad.py` intentionally breaks every rule so you can verify that Semgrep catches them:

| Violation | Line | Rule triggered |
|---|---|---|
| `print()` call | 8 | `no-print-statement` |
| `import logging` | 12 | `no-bare-logging-import` |
| f-string in log call | 21 | `no-fstring-in-log` |
| log-and-raise | 31 | `no-log-and-raise` |

### What the good example does

`src/app_good.py` demonstrates every standard in practice:

```python
import structlog

log = structlog.get_logger()

def process_order(order_id: str, user_id: str) -> dict:
    bound_log = log.bind(order_id=order_id, user_id=user_id)
    bound_log.info("order.processing_started")
    try:
        result = _do_work(order_id)
        bound_log.info("order.completed", result_status=result["status"])
        return result
    except ValueError as exc:
        # Log OR raise — not both
        raise ValueError(f"Invalid order {order_id}") from exc
```

Structured fields (`order_id`, `user_id`, `result_status`) are queryable in any log aggregation platform. The event name is a dot-namespaced string, not a free-form sentence.

---

## Extending to other stacks

Each language folder follows the same structure:

```
<language>/logging-standards/
├── README.md                  ← Quick start for this stack
├── sonar-project.properties   ← SonarQube project config
├── .semgrep/
│   └── logging-rules.yml      ← Stack-specific Semgrep rules
├── src/
│   ├── *_bad.*                ← Intentional violations (annotated)
│   └── *_good.*               ← Compliant reference implementation
└── scripts/
    └── run_fitness_checks.sh  ← One command to run all checks
```

| Stack | Logger standard | Key rules enforced |
|---|---|---|
| Python | `structlog` | No `print`, no stdlib `logging`, no f-strings in logs |
| Java | SLF4J + Logback | No `java.util.logging`, no direct Logback, parameterised `{}` args |
| Node | `pino` | No `console.log/warn/error`, shared logger factory, structured fields |
| .Net | `ILogger<T>` + Serilog | No `Console.Write`, injected `ILogger<T>`, no string interpolation in log calls |

---

## Adding your own fitness function

To add a new fitness function to any project:

1. **Define the standard** — write it as a one-sentence rule, e.g. "All HTTP handlers must set a `X-Correlation-ID` response header."
2. **Write a Semgrep rule** (or ArchUnit test / OPA policy) that detects violations
3. **Register a custom metric** in SonarQube (`scripts/setup_sonarqube_metrics.sh` as a template)
4. **Push the violation count** after each CI run (`scripts/push_logging_metrics.py` as a template)
5. **Add a quality gate condition** that fails if `violations > 0`
6. **Add to `trend_report.py`** so the metric appears in your trending dashboard

The pattern is always the same: detect → count → push → gate → trend.

---

## Further reading

- [Building Evolutionary Architectures](https://www.oreilly.com/library/view/building-evolutionary-architectures/9781492097532/) — Neal Ford, Rebecca Parsons, Patrick Kua
- [SonarQube quality gates documentation](https://docs.sonarsource.com/sonarqube/latest/user-guide/quality-gates/)
- [Semgrep rule writing guide](https://semgrep.dev/docs/writing-rules/overview/)
- [structlog documentation](https://www.structlog.org/en/stable/)
- `readme.md` in this repository — SonarQube capability reference
