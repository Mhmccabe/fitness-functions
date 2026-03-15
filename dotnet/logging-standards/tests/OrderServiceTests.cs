using Microsoft.Extensions.Logging.Abstractions;
using FitnessFunctions.Logging.Good;
using Xunit;

namespace FitnessFunctions.Logging.Tests;

public class OrderServiceTests
{
    private readonly OrderServiceGood _sut = new(NullLogger<OrderServiceGood>.Instance);

    [Fact]
    public void CreateOrder_ReturnsOrderWithPendingStatus()
    {
        var order = _sut.CreateOrder("user-1", 100m);
        Assert.NotNull(order.OrderId);
        Assert.Equal("pending", order.Status);
        Assert.Equal(100m, order.Amount);
    }

    [Fact]
    public void ProcessOrder_ThrowsForUnknownOrder()
    {
        Assert.Throws<KeyNotFoundException>(() =>
            _sut.ProcessOrder("nonexistent", "user-1"));
    }

    [Fact]
    public void ProcessOrder_ChargesValidOrder()
    {
        var order = _sut.CreateOrder("user-2", 500m);
        var result = _sut.ProcessOrder(order.OrderId, "user-2");
        Assert.Equal("charged", result.Status);
    }

    [Fact]
    public void ProcessOrder_ThrowsForAmountExceedingLimit()
    {
        var order = _sut.CreateOrder("user-3", 20000m);
        Assert.Throws<InvalidOperationException>(() =>
            _sut.ProcessOrder(order.OrderId, "user-3"));
    }

    [Fact]
    public void CancelOrder_ThrowsForUnknownOrder()
    {
        Assert.Throws<KeyNotFoundException>(() =>
            _sut.CancelOrder("nonexistent", "test"));
    }

    [Fact]
    public void CancelOrder_CancelsValidOrder()
    {
        var order = _sut.CreateOrder("user-4", 100m);
        _sut.CancelOrder(order.OrderId, "customer_request");
        Assert.Equal("cancelled", order.Status);
    }
}
