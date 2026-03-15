namespace ArchitecturePatterns.Repositories;

/// <summary>
/// OrderRepository — DATA ACCESS LAYER (compliant)
///
/// Architecture rules enforced here:
///   ✓ No using directives from Controllers or Services namespaces
///   ✓ Owns all storage interaction
///   ✓ Implements IOrderRepository interface
/// </summary>
public class OrderRepository : IOrderRepository
{
    private readonly Dictionary<string, Order> _store = new();

    public Order? FindById(string orderId) =>
        _store.TryGetValue(orderId, out var order) ? order : null;

    public Order Save(Order order)
    {
        _store[order.OrderId] = order;
        return order;
    }
}
