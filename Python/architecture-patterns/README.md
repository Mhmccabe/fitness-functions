# Python Architecture Patterns — Fitness Function

Enforces a strict **API → Services → Repositories** layered architecture using [import-linter](https://import-linter.readthedocs.io/) and Semgrep.

## Rules enforced

| # | Rule | Tool | Severity |
|---|---|---|---|
| 1 | API layer must not import from repositories directly | import-linter + Semgrep | Error |
| 2 | Services must not import from the API layer (upward dep) | import-linter + Semgrep | Error |
| 3 | Layered contract: api → services → repositories | import-linter | Error |

## Project structure

```
src/
├── api/order_api.py             ✓ imports services only
├── services/order_service.py    ✓ imports repositories only
├── repositories/order_repository.py ✓ no upward imports
└── bad/order_api_bad.py         ✗ intentional violations (teaching example)

tests/
└── test_order_service.py        pytest unit tests
```

## Running locally

```bash
# Install deps
pip install -e ".[dev]"

# Run all checks
./scripts/run_fitness_checks.sh

# Run import-linter only
lint-imports

# Run pytest only
PYTHONPATH=. pytest tests/ --cov=src

# Run Semgrep
semgrep --config .semgrep/architecture-rules.yml src/
```

## Moving from warning to error

The CI pipeline currently treats violations as **warnings**. To promote to a hard gate:

1. Remove `|| true` from the Semgrep step in `.github/workflows/fitness-python-architecture.yml`
2. Remove `continue-on-error: true` from the SonarQube step
3. Add a violation threshold check: if violations > 0, exit 1
