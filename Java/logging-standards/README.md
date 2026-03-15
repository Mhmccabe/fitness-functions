# Java — Logging Standards Fitness Function

This example enforces Java logging standards as an automated fitness function. For the full conceptual background, see [tutorial.md](../../tutorial.md).

---

## Standards enforced

### logging-rules.yml — how to log

| Rule | What it prevents |
|---|---|
| No `java.util.logging` | Mixed log formats; JUL bypasses SLF4J configuration |
| No direct Logback imports | Implementation coupling; prevents swapping the log backend |
| No string concatenation in log calls | Eager string allocation; use `{}` placeholders instead |
| Logger typed to own class | Misleading source attribution in log output |
| No `System.out.println` | Unstructured, unlevelled output bypassing the logger |

### required-fields-rules.yml — what to log

| Rule | Required field(s) | Triggered when |
|---|---|---|
| `http-event-missing-request-id` | `requestId={}` | Any `request.*` event |
| `http-request-completed-missing-status-code` | `statusCode={}` | `request.completed` event |
| `http-request-completed-missing-duration` | `durationMs={}` | `request.completed` event |
| `batch-event-missing-job-id` | `jobId={}` | Any `job.*` event |
| `batch-job-completed-missing-record-count` | `recordCount={}` | `job.completed` event |
| `etl-event-missing-pipeline-id` | `pipelineId={}` | Any `pipeline.*` event |
| `etl-pipeline-completed-missing-row-counts` | `rowsIn={}`, `rowsOut={}` | `pipeline.completed` event |
| `async-event-missing-message-id` | `messageId={}` | Any `message.*` event |
| `async-event-missing-queue-name` | `queueName={}` | Any `message.*` event |
| `error-log-missing-exception-or-reason` | exception arg or `reason={}` | Any `log.error()` |

---

## Quick start

```bash
# Install semgrep (Python required)
pip install semgrep

# Run all fitness checks
./scripts/run_fitness_checks.sh

# Or run Semgrep only — see violations in OrderServiceBad.java
semgrep --config .semgrep/logging-rules.yml src/main/

# Maven build + tests
mvn clean verify
```

---

## Key files

| File | Purpose |
|---|---|
| `.semgrep/logging-rules.yml` | Semgrep rules — one per standard |
| `src/main/java/example/OrderServiceBad.java` | Intentional violations |
| `src/main/java/example/OrderServiceGood.java` | Compliant reference |
| `src/main/java/example/CorrelationFilter.java` | HTTP filter that sets MDC correlation ID |
| `sonar-project.properties` | SonarQube configuration |
| `scripts/run_fitness_checks.sh` | One command to run all checks |

---

## Moving from Warning to Error

Semgrep violations currently produce a **warning** — the build stays green but the summary shows a ⚠️ count. Once your team has fixed existing violations and wants to enforce the standard as a hard gate, promote it to an error:

### Step 1 — Fix all violations

```bash
semgrep --config .semgrep/logging-rules.yml src/main/ --exclude="*Bad.java"
```

Work through each finding:

- Replace `java.util.logging` / Logback imports with SLF4J: `import org.slf4j.Logger; import org.slf4j.LoggerFactory;`
- Replace string concatenation with `{}` placeholders: `logger.info("order.started orderId={}", orderId)`
- Replace `System.out.println` with `logger.info("event.name")`
- Ensure logger is typed to its own class: `LoggerFactory.getLogger(MyClass.class)`

### Step 2 — Confirm zero violations locally

```bash
semgrep --config .semgrep/logging-rules.yml src/main/ --exclude="*Bad.java"
# Expected: "Findings: 0"
```

### Step 3 — Promote to error in the workflow

In [`.github/workflows/fitness-java-logging.yml`](../../.github/workflows/fitness-java-logging.yml), change:

```yaml
        continue-on-error: true   # warning
```

to:

```yaml
        continue-on-error: false  # error — blocks the build
```

And restore the exit code:

```python
sys.exit(1 if count > 0 else 0)
```

Once merged, any new violation will fail the build and block the PR.

---

## SLF4J parameterised logging pattern

```java
// BAD — eager string allocation
logger.info("Processing order " + orderId + " for user " + userId);

// GOOD — {} placeholders evaluated lazily (only if log level is active)
logger.info("order.processing_started orderId={} userId={}", orderId, userId);
```

## MDC correlation context pattern

```java
// In the HTTP filter (CorrelationFilter.java)
MDC.put("correlationId", correlationId);

try {
    chain.doFilter(request, response);
} finally {
    MDC.remove("correlationId");  // Always clean up in thread pools
}
```

Every log line emitted during the request now carries `correlationId` automatically, regardless of which service class produces it.

---

## SonarQube built-in rules (complement Semgrep)

SonarQube's built-in Java rules cover additional logging anti-patterns:

| Rule | What it catches |
|---|---|
| `java:S2629` | Logging args should not require evaluation (same as our Semgrep rule) |
| `java:S4792` | Configuring loggers is security-sensitive |
| `java:S1166` | Exception handlers should preserve original exception |
| `java:S2139` | Exceptions should be logged or rethrown — not both |

Semgrep and SonarQube are complementary: SonarQube covers general anti-patterns across all projects, while Semgrep enforces your organisation-specific conventions (SLF4J only, no JUL, MDC required).
