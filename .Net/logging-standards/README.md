# .NET — Logging Standards Fitness Function

This example enforces .NET logging standards as an automated fitness function. For the full conceptual background, see [tutorial.md](../../tutorial.md).

---

## Standards enforced

### logging-rules.yml — how to log

| Rule | What it prevents |
|---|---|
| No `Console.WriteLine` / `Console.Write` | Unstructured output bypassing ILogger pipeline |
| No string interpolation in log calls | Eagerly-evaluated free text; prevents structured field extraction |
| No string concatenation in log calls | Same as above |
| No direct `Logger<T>` instantiation | Bypasses DI-configured Serilog provider and enrichers |
| No `Debug.WriteLine` | Dev-only output that leaks into production binaries |

### required-fields-rules.yml — what to log

| Rule | Required placeholder(s) | Triggered when |
|---|---|---|
| `http-event-missing-request-id` | `{RequestId}` | Any `request.*` event |
| `http-request-completed-missing-status-code` | `{StatusCode}` | `request.completed` event |
| `http-request-completed-missing-duration` | `{DurationMs}` | `request.completed` event |
| `batch-event-missing-job-id` | `{JobId}` | Any `job.*` event |
| `batch-job-completed-missing-record-count` | `{RecordCount}` | `job.completed` event |
| `etl-event-missing-pipeline-id` | `{PipelineId}` | Any `pipeline.*` event |
| `etl-pipeline-completed-missing-row-counts` | `{RowsIn}`, `{RowsOut}` | `pipeline.completed` event |
| `async-event-missing-message-id` | `{MessageId}` | Any `message.*` event |
| `async-event-missing-queue-name` | `{QueueName}` | Any `message.*` event |
| `error-log-missing-exception-or-reason` | exception arg or `{Reason}` | Any `LogError()` |

---

## Quick start

```bash
# Install semgrep (Python required)
pip install semgrep

# Run all fitness checks
./scripts/run_fitness_checks.sh

# Or run steps individually:

# Semgrep — see violations (excludes *Bad.cs teaching examples)
semgrep --config .semgrep/logging-rules.yml src/ --exclude="*Bad.cs"

# Confirm bad examples DO trigger violations
semgrep --config .semgrep/logging-rules.yml src/ --include="*Bad.cs"

# dotnet tests
dotnet test
```

---

## Structured message template pattern

```csharp
// BAD — string interpolation, free text in logs
_logger.LogInformation($"Processing order {orderId} for {userId}");

// GOOD — structured message template with {Property} placeholders
// Serilog/MSEL extracts OrderId and UserId as queryable fields
_logger.LogInformation(
    "order.processing_started {OrderId} {UserId}",
    orderId, userId);
```

## Correlation scope pattern

```csharp
// Bind correlation context for the duration of this operation.
// All log calls within the using block carry OrderId and UserId.
using var scope = _logger.BeginScope(new Dictionary<string, object>
{
    ["OrderId"] = orderId,
    ["UserId"]  = userId,
});

_logger.LogInformation("order.processing_started {OrderId}", orderId);
// ... every log line here carries OrderId and UserId automatically
```

## Serilog configuration (Program.cs)

```csharp
Log.Logger = new LoggerConfiguration()
    .Enrich.FromLogContext()           // Picks up BeginScope() properties
    .Enrich.WithMachineName()
    .WriteTo.Console(new CompactJsonFormatter())
    .CreateLogger();

builder.Host.UseSerilog();
```

The service code only ever sees `ILogger<T>`. Swapping Serilog for another provider requires no service code changes.

---

## Key files

| File | Purpose |
|---|---|
| `.semgrep/logging-rules.yml` | Semgrep rules — one per standard |
| `src/OrderServiceBad.cs` | Intentional violations |
| `src/OrderServiceGood.cs` | Compliant reference |
| `src/Program.cs` | Serilog configuration and DI setup |
| `sonar-project.properties` | SonarQube configuration |
| `scripts/run_fitness_checks.sh` | One command to run all checks |

---

## SonarQube built-in rules (complement Semgrep)

| Rule | What it catches |
|---|---|
| `cs:S2629` | Message template args should not require evaluation |
| `cs:S4792` | Configuring loggers is security-sensitive |
| `cs:S2139` | Exceptions should be logged or rethrown — not both |

Semgrep enforces your organisation-specific conventions on top of SonarQube's general rules.
