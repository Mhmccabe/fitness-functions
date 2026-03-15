
## What SonarQube can track as fitness functions

### Security — its strongest capability

SonarQube's security rules are divided into two types: security-injection rules and security-configuration rules. For injection vulnerabilities, it uses taint analysis technology on source code to detect flows from user-controlled inputs to sensitive sinks.

It provides dedicated reports to track application security against OWASP Top 10, ASVS 4.0, and CWE Top 25 standards — and these can be used as quality gate conditions that block a build.

Configure these as hard quality gate conditions:

```properties
# sonar-project.properties
sonar.projectKey=my-service
sonar.qualitygate.wait=true   # block the pipeline until gate resolves
```

Then in the SonarQube UI (or via API), set your security quality gate:

```bash
# Create quality gate via API
curl -X POST "$SONAR_URL/api/qualitygates/create" \
  -u "$SONAR_TOKEN:" \
  --data-urlencode "name=Security Fitness Gate"

# Add condition: zero new critical security issues
curl -X POST "$SONAR_URL/api/qualitygates/create_condition" \
  -u "$SONAR_TOKEN:" \
  --data "gateId=$GATE_ID&metric=new_security_rating&op=GT&error=1"
  # Rating 1 = A. GT 1 means anything worse than A fails.

# Add condition: security hotspots must be reviewed
curl -X POST "$SONAR_URL/api/qualitygates/create_condition" \
  -u "$SONAR_TOKEN:" \
  --data "gateId=$GATE_ID&metric=new_security_hotspots_reviewed&op=LT&error=100"
```

What it detects out of the box across languages:

| Vulnerability type | Example |
|---|---|
| SQL injection | `query = "SELECT * FROM users WHERE id = " + userId` |
| XSS | Unsanitised user input written to DOM/response |
| Path traversal | User-controlled file path passed to `File()` |
| Weak cryptography | MD5, SHA1 for password hashing |
| Hardcoded credentials | `password = "s3cr3t"` in source code |
| XXE injection | XML parser with external entities enabled |
| LDAP injection | User input in LDAP filter |
| Secrets in config | 400+ patterns in YAML, JSON, `.env` files |

As of 2025.x, SonarQube's secrets detection now covers over 400 distinct secret patterns powered by 346 rules, including newly added rules for passwords and secrets in YAML and JSON files.

---

### Maintainability / Code Quality — the bread and butter

These map directly to fitness function conditions in a quality gate:

```bash
# Complexity fitness function — fail if cognitive complexity > threshold on new code
curl -X POST "$SONAR_URL/api/qualitygates/create_condition" \
  -u "$SONAR_TOKEN:" \
  --data "gateId=$GATE_ID&metric=new_cognitive_complexity&op=GT&error=15"

# Technical debt ratio — fail if new code introduces > 5% debt ratio
curl -X POST "$SONAR_URL/api/qualitygates/create_condition" \
  -u "$SONAR_TOKEN:" \
  --data "gateId=$GATE_ID&metric=new_sqale_debt_ratio&op=GT&error=5"

# Duplication — fail if new code duplicates > 3%
curl -X POST "$SONAR_URL/api/qualitygates/create_condition" \
  -u "$SONAR_TOKEN:" \
  --data "gateId=$GATE_ID&metric=new_duplicated_lines_density&op=GT&error=3"
```

Every measurable metric in SonarQube:

```
new_bugs                        # new bugs introduced
new_code_smells                 # maintainability issues in new code
new_cognitive_complexity        # how hard new code is to understand
new_cyclomatic_complexity       # branching complexity
new_duplicated_lines_density    # duplication % on new code
new_coverage                    # test coverage on new code
new_line_coverage               # line coverage on new code
new_branch_coverage             # branch coverage on new code
new_vulnerabilities             # new security vulnerabilities
new_security_hotspots_reviewed  # % of hotspots reviewed
new_security_rating             # A/B/C/D/E security grade
new_reliability_rating          # A/B/C/D/E reliability grade
new_maintainability_rating      # A/B/C/D/E maintainability grade
new_sqale_debt_ratio            # technical debt ratio
new_technical_debt              # raw minutes of technical debt
```

---

### Architecture fitness functions — new in 2025

Through its new Design & Architecture feature, SonarQube Server can now verify the architecture and design of Java source code by verifying the code structure against architecture and design patterns. This is currently Java-only and was introduced in the 2025.2 release. For other stacks, you still need ArchUnit, dependency-cruiser, or import-linter.

---

### Test coverage as a quality gate

The "Clean as You Code" approach lets you focus gates on new code only, avoiding being blocked by legacy debt:

```properties
# sonar-project.properties

# Point to your test coverage report
sonar.coverage.jacoco.xmlReportPaths=target/site/jacoco/jacoco.xml   # Java/Maven
sonar.javascript.lcov.reportPaths=coverage/lcov.info                  # JS/TS
sonar.python.coverage.reportPaths=coverage.xml                        # Python
sonar.cs.opencover.reportsPaths=**/coverage.opencover.xml             # .NET

# Focus on new code only
sonar.newCode.referenceBranch=main
```

Gate condition — block PR if new code coverage drops below 80%:

```bash
curl -X POST "$SONAR_URL/api/qualitygates/create_condition" \
  -u "$SONAR_TOKEN:" \
  --data "gateId=$GATE_ID&metric=new_coverage&op=LT&error=80"
```

---

### Custom metrics via the API — the extension mechanism

SonarQube doesn't natively measure observability or runtime performance, but you can push external metric values into it via the Web API and then gate on them. This is how you bridge it with tools that do:

```python
# scripts/push_fitness_metrics.py
# Run AFTER your test/analysis stages, push results into SonarQube

import requests

SONAR_URL = os.environ["SONAR_URL"]
SONAR_TOKEN = os.environ["SONAR_TOKEN"]
PROJECT_KEY = os.environ["SONAR_PROJECT_KEY"]

def push_custom_metric(metric_key: str, value: float):
    """Push an externally computed metric into SonarQube."""
    response = requests.post(
        f"{SONAR_URL}/api/custom_measures/create",
        auth=(SONAR_TOKEN, ""),
        data={
            "projectKey": PROJECT_KEY,
            "metricKey": metric_key,
            "value": str(value),
        }
    )
    response.raise_for_status()

# Push k6 p95 latency result from a load test
push_custom_metric("load_test_p95_ms", 320.5)

# Push Lighthouse performance score
push_custom_metric("lighthouse_performance", 87)

# Push number of missing correlation ID log lines (from log analysis)
push_custom_metric("missing_correlation_ids", 0)
```

For this to work you first register the custom metric definitions:

```bash
# Register a custom metric (done once, admin only)
curl -X POST "$SONAR_URL/api/custom_metrics/create" \
  -u "$SONAR_TOKEN:" \
  --data "key=load_test_p95_ms&name=Load test P95 latency (ms)&type=FLOAT&domain=Performance"

curl -X POST "$SONAR_URL/api/custom_metrics/create" \
  -u "$SONAR_TOKEN:" \
  --data "key=lighthouse_performance&name=Lighthouse performance score&type=INT&domain=Frontend"
```

Then gate on them:

```bash
curl -X POST "$SONAR_URL/api/qualitygates/create_condition" \
  -u "$SONAR_TOKEN:" \
  --data "gateId=$GATE_ID&metric=load_test_p95_ms&op=GT&error=500"
  # Fail if P95 latency exceeds 500ms
```

---

### Observability — what SonarQube can and can't do

SonarQube has no built-in concept of "are you logging correctly" or "do you have tracing". What it *can* do is enforce coding rules that approximate observability standards:

**What SonarQube rules cover natively:**

```
# These built-in rules flag observability anti-patterns:
java:S2629   # Logging arguments should not require evaluation (string concat in logs)
java:S4792   # Configuring loggers is security-sensitive
java:S1166   # Exception handlers should preserve the original exception
java:S2139   # Exceptions should be either logged or rethrown, not both
python:S2629 # Logging format strings shouldn't be evaluated eagerly
javascript:S2228 # Console logging should not be used in production
```

**What SonarQube can't enforce** (use ArchUnit / Semgrep / custom rules):
- "Every service method must have a `@WithSpan` annotation"
- "All HTTP filters must set MDC correlation ID"
- "Async tasks must propagate MDC context"
- "Only SLF4J facade is permitted — no direct Logback"
- "Logger must be typed to its own class"

For those, pair SonarQube with ArchUnit (Java) or Semgrep (all stacks):

```yaml
# semgrep-rules/observability.yml — runs alongside SonarQube in the same pipeline stage
rules:
  - id: require-structured-logging
    languages: [python]
    severity: ERROR
    message: "Lambda handlers must use structlog or powertools for structured logging"
    pattern-not-inside: |
      import structlog
      ...
    pattern: |
      def lambda_handler(event, context):
          ...

  - id: no-print-in-production
    languages: [python, javascript, typescript]
    severity: ERROR
    message: "Use a logger instead of print/console.log"
    patterns:
      - pattern: print(...)
```

---

### Performance — what SonarQube measures vs what it misses

SonarQube measures *static code indicators* of performance problems:

| SonarQube detects statically | Won't detect |
|---|---|
| Inefficient string concatenation in loops | Actual latency under load |
| N+1 query patterns (some rules) | Memory pressure at scale |
| Unnecessary object creation | Cold start time in Lambda |
| Thread contention patterns | Network I/O bottlenecks |
| High cognitive complexity (correlates with perf bugs) | Cache hit rates |

For real performance fitness functions, run these in the same Harness pipeline as a separate stage and push results back via the custom metrics API shown above:

```yaml
# Harness pipeline stage — performance fitness function
- stage:
    name: Performance Fitness Functions
    steps:
      - step:
          name: k6 load test
          type: Run
          spec:
            image: grafana/k6
            command: |
              k6 run --out json=results.json performance/load-test.js
              # Extract P95 and push to SonarQube
              P95=$(jq '.metrics.http_req_duration.values["p(95)"]' results.json)
              curl -X POST "$SONAR_URL/api/custom_measures/create" \
                -u "$SONAR_TOKEN:" \
                --data "projectKey=$PROJECT_KEY&metricKey=load_test_p95_ms&value=$P95"
```

---

### The honest picture: SonarQube's scope

SonarQube can identify risks in the code, but requires a human eye to sort alerts and does not detect flaws linked to execution or configuration. It analyses the source code without executing it — so it misses vulnerabilities that only appear at runtime.

Think of SonarQube's role in a fitness function strategy as the **static analysis layer** — it catches the largest surface area of code-level problems with the lowest friction. It integrates with every language, every CI/CD system, and produces a single quality gate verdict. But it intentionally stops at the boundary of the source file.

The full fitness function picture for a mature pipeline looks like this:

| Layer | Tool | What it gates on |
|---|---|---|
| Static analysis | SonarQube | Security, complexity, coverage, duplication, smells |
| Architecture | ArchUnit / dependency-cruiser | Layer boundaries, naming, cycles |
| Observability standards | Semgrep / ArchUnit rules | Logging patterns, tracing annotations |
| Secrets | SonarQube + Gitleaks | Hardcoded credentials, 400+ patterns |
| Dependencies | SonarQube Advanced Security / OWASP Dependency-Check | CVEs in third-party libs |
| Performance | k6 / Gatling + custom metric push | Latency thresholds, throughput |
| Frontend | Lighthouse CI + bundlesize | Core Web Vitals, bundle size budget |
| Infrastructure | Checkov + OPA | IaC security, required tags, cost limits |

SonarQube covers the first two rows deeply, contributes to secrets and dependencies, and can *receive* results from all the others via its custom metrics API — making it a good central dashboard even for the things it can't measure itself.