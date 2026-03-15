# Node.js — Logging Standards Fitness Function

This example enforces Node.js logging standards as an automated fitness function. For the full conceptual background, see [tutorial.md](../../tutorial.md).

---

## Standards enforced

### logging-rules.yml — how to log

| Rule | What it prevents |
|---|---|
| No `console.log/warn/error` | Unstructured output with no log level or structured fields |
| No direct `require('pino')` | Inconsistent logger configuration across modules |
| No template literals in log calls | Free-text that cannot be queried by field in log aggregation |

### required-fields-rules.yml — what to log

| Rule | Required field(s) | Triggered when |
|---|---|---|
| `http-event-missing-request-id` | `requestId` | Any `request.*` event |
| `http-request-completed-missing-status-code` | `statusCode` | `request.completed` event |
| `http-request-completed-missing-duration` | `durationMs` | `request.completed` event |
| `batch-event-missing-job-id` | `jobId` | Any `job.*` event |
| `batch-job-completed-missing-record-count` | `recordCount` | `job.completed` event |
| `etl-event-missing-pipeline-id` | `pipelineId` | Any `pipeline.*` event |
| `etl-pipeline-completed-missing-row-counts` | `rowsIn`, `rowsOut` | `pipeline.completed` event |
| `async-event-missing-message-id` | `messageId` | Any `message.*` event |
| `async-event-missing-queue-name` | `queueName` | Any `message.*` event |
| `error-event-missing-err-or-reason` | `err` or `reason` | Any `log.error()` |

---

## Quick start

```bash
# Install dependencies
npm install

# Install semgrep (Python required)
pip install semgrep

# Run all fitness checks
./scripts/run_fitness_checks.sh

# Or run steps individually:

# Semgrep — see violations (excludes *-bad.js teaching examples)
semgrep --config .semgrep/logging-rules.yml src/ --exclude="*-bad.js"

# Semgrep — confirm bad examples do trigger violations
semgrep --config .semgrep/logging-rules.yml src/ --include="*-bad.js"

# Tests with coverage
NODE_ENV=test npx jest --coverage
```

---

## Pino structured logging pattern

```javascript
// BAD — unstructured, unqueryable
console.log(`Processing order ${orderId}`);
log.info(`Order ${orderId} processed`);

// GOOD — structured fields + static event name
const log = createLogger({ module: 'order-service' });

// Pass a context object first, then the static event name
log.info({ orderId, userId }, 'order.processing_started');

// For errors, pino serialises the Error object as a structured field
log.error({ err, orderId }, 'order.payment_failed');
```

## Correlation context pattern

```javascript
// In your HTTP framework middleware
app.use((req, res, next) => {
  const correlationId = req.headers['x-correlation-id'] || randomUUID();
  res.setHeader('x-correlation-id', correlationId);

  // Bind to the request — thread through to service calls
  req.log = createLogger({ correlationId, requestId: req.id });
  next();
});

// In your route handler — pass req.log down
router.post('/orders', async (req, res) => {
  const result = await orderService.processOrder(orderId, userId, req.log);
  res.json(result);
});
```

---

## Key files

| File | Purpose |
|---|---|
| `.semgrep/logging-rules.yml` | Semgrep rules — one per standard |
| `src/logger.js` | Shared pino factory (use this in all modules) |
| `src/order-service-bad.js` | Intentional violations |
| `src/order-service-good.js` | Compliant reference |
| `sonar-project.properties` | SonarQube configuration |
| `scripts/run_fitness_checks.sh` | One command to run all checks |
