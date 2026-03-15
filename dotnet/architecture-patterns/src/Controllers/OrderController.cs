using ArchitecturePatterns.Services;

namespace ArchitecturePatterns.Controllers;

/// <summary>
/// OrderController — CONTROLLER LAYER (compliant)
///
/// Architecture rules enforced here:
///   ✓ Uses only ArchitecturePatterns.Services — never Repositories
///   ✓ Translates request/response concerns to/from domain objects
///   ✓ Injects IOrderService via constructor
/// </summary>
public class OrderController
{
    private readonly IOrderService _service;

    public OrderController(IOrderService service)
    {
        _service = service;
    }

    public Dictionary<string, object> CreateOrder(string userId, decimal amount)
    {
        var order = _service.CreateOrder(userId, amount);
        return new Dictionary<string, object>
        {
            ["orderId"] = order.OrderId,
            ["status"]  = order.Status,
            ["amount"]  = order.Amount,
        };
    }

    public Dictionary<string, object> GetOrder(string orderId)
    {
        var order = _service.GetOrder(orderId);
        if (order is null)
            return new Dictionary<string, object> { ["error"] = "not_found" };

        return new Dictionary<string, object>
        {
            ["orderId"] = order.OrderId,
            ["status"]  = order.Status,
        };
    }

    public Dictionary<string, object> ProcessOrder(string orderId)
    {
        try
        {
            var order = _service.ProcessOrder(orderId);
            return new Dictionary<string, object>
            {
                ["orderId"] = order.OrderId,
                ["status"]  = order.Status,
            };
        }
        catch (ArgumentException ex)
        {
            return new Dictionary<string, object> { ["error"] = ex.Message };
        }
    }
}
