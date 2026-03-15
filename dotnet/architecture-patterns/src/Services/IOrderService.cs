using ArchitecturePatterns.Repositories;

namespace ArchitecturePatterns.Services;

public interface IOrderService
{
    Order CreateOrder(string userId, decimal amount);
    Order? GetOrder(string orderId);
    Order ProcessOrder(string orderId);
}
