# Java Architecture Patterns — Fitness Function

Enforces a strict **Controller → Service → Repository** layered architecture using [ArchUnit](https://www.archunit.org/) and Semgrep.

## Rules enforced

| # | Rule | Tool | Severity |
|---|---|---|---|
| 1 | Controllers must not depend on repositories directly | ArchUnit + Semgrep | Error |
| 2 | Services must not depend on controllers | ArchUnit + Semgrep | Error |
| 3 | No circular dependencies between packages | ArchUnit | Error |
| 4 | Controller classes must reside in `example.controller` package | ArchUnit | Error |
| 5 | Service classes must reside in `example.service` package | ArchUnit | Error |

## Project structure

```
src/main/java/example/
├── controller/OrderController.java   ✓ calls service only
├── service/OrderService.java         ✓ calls repository only
├── repository/OrderRepository.java   ✓ data access, no upward refs
└── bad/OrderControllerBad.java       ✗ intentional violations (teaching example)

src/test/java/example/
└── ArchitectureTest.java             ArchUnit rules as JUnit 5 tests
```

## Running locally

```bash
# Run all checks
./scripts/run_fitness_checks.sh

# Run only ArchUnit tests
mvn test

# Run only Semgrep
semgrep --config .semgrep/architecture-rules.yml src/main/ --exclude="*Bad.java"
```

## Moving from warning to error

The CI pipeline currently treats violations as **warnings** — the build passes even with findings. To promote to a hard gate:

1. Remove `|| true` from the Semgrep step in `.github/workflows/fitness-java-architecture.yml`
2. Remove `continue-on-error: true` from the SonarQube step
3. Add a violation threshold check: if violations > 0, exit 1
