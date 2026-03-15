using ArchitecturePatterns.Repositories;

namespace ArchitecturePatterns.Services;

/// <summary>
/// OrderService — SERVICE LAYER (compliant)
///
/// Architecture rules enforced here:
///   ✓ Uses only ArchitecturePatterns.Repositories — never Controllers
///   ✓ Owns all business logic
///   ✓ Injects IOrderRepository via constructor
/// </summary>
public class OrderService : IOrderService
{
    private readonly IOrderRepository _repository;

    public OrderService(IOrderRepository repository)
    {
        _repository = repository;
    }

    public Order CreateOrder(string userId, decimal amount)
    {
        var order = new Order(Guid.NewGuid().ToString(), userId, amount, "pending");
        return _repository.Save(order);
    }

    public Order? GetOrder(string orderId) => _repository.FindById(orderId);

    public Order ProcessOrder(string orderId)
    {
        var order = _repository.FindById(orderId)
            ?? throw new ArgumentException($"Order not found: {orderId}");

        if (order.Amount > 10_000m)
            throw new ArgumentException("Amount exceeds limit");

        return _repository.Save(order with { Status = "charged" });
    }
}
