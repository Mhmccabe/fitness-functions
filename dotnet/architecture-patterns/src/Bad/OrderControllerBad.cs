// BAD EXAMPLE — INTENTIONALLY NON-COMPLIANT
// Excluded from compilation via the test project's direct-compile approach.
//
// Violates the layered architecture rules enforced by the fitness function.
//
// Expected Semgrep violations:
//   Line 5  — no-repository-using-in-controller (using Repositories in controller file)
//   Line 18 — no-repository-using-in-controller (new OrderRepository() in controller)
//
// NetArchTest violations (detected in ArchitectureTests.cs):
//   - Controllers namespace depends on Repositories namespace

using ArchitecturePatterns.Repositories; // VIOLATION: controller imports repository namespace

namespace ArchitecturePatterns.Bad;

public class OrderControllerBad
{
    // VIOLATION: controller holds direct reference to repository
    private readonly OrderRepository _repository = new OrderRepository();

    public Dictionary<string, object> GetOrder(string orderId)
    {
        // VIOLATION: data access logic in the controller layer
        var order = _repository.FindById(orderId);
        if (order is null)
            return new Dictionary<string, object> { ["error"] = "not_found" };

        return new Dictionary<string, object>
        {
            ["orderId"] = order.OrderId,
            ["status"]  = order.Status,
        };
    }
}
