namespace ArchitecturePatterns.Repositories;

public interface IOrderRepository
{
    Order? FindById(string orderId);
    Order Save(Order order);
}

public record Order(string OrderId, string UserId, decimal Amount, string Status);
