# .NET Architecture Patterns — Fitness Function

Enforces a strict **Controllers → Services → Repositories** layered architecture using [NetArchTest](https://github.com/BenMorris/NetArchTest) and Semgrep.

## Rules enforced

| # | Rule | Tool | Severity |
|---|---|---|---|
| 1 | Controllers must not depend on Repositories namespace | NetArchTest + Semgrep | Error |
| 2 | Services must not depend on Controllers namespace | NetArchTest + Semgrep | Error |
| 3 | Types in Controllers namespace must end with `Controller` | NetArchTest | Error |
| 4 | Classes in Services namespace must end with `Service` | NetArchTest | Error |

## Project structure

```
src/
├── Controllers/OrderController.cs    ✓ uses IOrderService only
├── Services/OrderService.cs          ✓ uses IOrderRepository only
├── Repositories/OrderRepository.cs   ✓ data access, no upward refs
└── Bad/OrderControllerBad.cs         ✗ intentional violations (teaching example)

tests/
└── ArchitectureTests.cs              NetArchTest rules as xUnit tests
```

## Running locally

```bash
# Run all checks
./scripts/run_fitness_checks.sh

# Run only NetArchTest
dotnet test ArchitecturePatterns.sln

# Run only Semgrep
semgrep --config .semgrep/architecture-rules.yml src/ --exclude="*Bad.cs"
```

## Moving from warning to error

The CI pipeline currently treats violations as **warnings**. To promote to a hard gate:

1. Remove `|| true` from the Semgrep step in `.github/workflows/fitness-dotnet-architecture.yml`
2. Remove `continue-on-error: true` from the SonarQube step
3. Add a violation threshold check: if violations > 0, exit 1
