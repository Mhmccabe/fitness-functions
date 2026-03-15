# Node Architecture Patterns — Fitness Function

Enforces a strict **Routes → Controllers → Services → Repositories** layered architecture using [dependency-cruiser](https://github.com/sverweij/dependency-cruiser) and Semgrep.

## Rules enforced

| # | Rule | Tool | Severity |
|---|---|---|---|
| 1 | Controllers must not import from repositories | dependency-cruiser + Semgrep | Error |
| 2 | Routes must not import services directly (skips controller) | dependency-cruiser + Semgrep | Error |
| 3 | Routes must not import repositories (two layers deep) | dependency-cruiser | Error |
| 4 | Services must not import controllers (upward dependency) | dependency-cruiser + Semgrep | Error |
| 5 | No circular dependencies | dependency-cruiser | Error |

## Project structure

```
src/
├── routes/order-routes.js          ✓ imports controllers only
├── controllers/order-controller.js ✓ imports services only
├── services/order-service.js       ✓ imports repositories only
├── repositories/order-repository.js✓ no upward imports
└── bad/order-controller-bad.js     ✗ intentional violations (teaching example)

tests/
└── order-service.test.js           Jest unit tests
```

## Running locally

```bash
# Run all checks (dependency-cruiser + jest)
npm test

# Run only architecture check
npm run arch

# Run only unit tests
npm run unit

# Run Semgrep
semgrep --config .semgrep/architecture-rules.yml src/ --exclude="*-bad.js"
```

## Moving from warning to error

The CI pipeline currently treats violations as **warnings**. To promote to a hard gate:

1. Remove `|| true` from the Semgrep step in `.github/workflows/fitness-node-architecture.yml`
2. Remove `continue-on-error: true` from the SonarQube step
3. Add a violation threshold check: if violations > 0, exit 1
