using System;
using System.Collections.Generic;
using Microsoft.Extensions.Logging;

namespace FitnessFunctions.Logging.Good;

/// <summary>
/// OrderServiceGood — FULLY COMPLIANT reference implementation
///
/// Demonstrates every logging standard enforced by the fitness function:
///
///   ✓ ILogger&lt;T&gt; injected via constructor — no direct instantiation
///   ✓ Structured message templates with {Property} placeholders
///   ✓ No Console.Write / Console.WriteLine
///   ✓ No string interpolation or concatenation in log calls
///   ✓ Throw OR log — never both in the same catch block
///   ✓ Scopes used for correlation context
/// </summary>
public class OrderServiceGood
{
    private readonly ILogger<OrderServiceGood> _logger;
    private readonly Dictionary<string, Order> _orders = new();

    // ILogger<T> injected by the DI container configured with Serilog
    public OrderServiceGood(ILogger<OrderServiceGood> logger)
    {
        _logger = logger;
    }

    public Order ProcessOrder(string orderId, string userId)
    {
        // Use a logging scope to bind correlation context.
        // Every log statement within the using block carries OrderId and UserId.
        using var scope = _logger.BeginScope(new Dictionary<string, object>
        {
            ["OrderId"] = orderId,
            ["UserId"] = userId,
        });

        // Structured template — {Property} placeholders, not string interpolation
        _logger.LogInformation("order.processing_started {OrderId} {UserId}", orderId, userId);

        if (!_orders.TryGetValue(orderId, out var order))
        {
            _logger.LogWarning("order.not_found {OrderId}", orderId);
            throw new KeyNotFoundException(orderId);
        }

        // Raise without logging — caller decides how to handle the exception
        ChargePayment(order);

        _logger.LogInformation(
            "order.completed {OrderId} {Status} {Amount}",
            orderId, order.Status, order.Amount);

        return order;
    }

    public Order CreateOrder(string userId, decimal amount)
    {
        var orderId = Guid.NewGuid().ToString();
        var order = new Order(orderId, userId, amount);
        _orders[orderId] = order;

        _logger.LogInformation(
            "order.created {OrderId} {UserId} {Amount}",
            orderId, userId, amount);

        return order;
    }

    public void CancelOrder(string orderId, string reason)
    {
        using var scope = _logger.BeginScope(new Dictionary<string, object>
        {
            ["OrderId"] = orderId,
        });

        if (!_orders.TryGetValue(orderId, out var order))
        {
            _logger.LogWarning("order.not_found {OrderId}", orderId);
            throw new KeyNotFoundException(orderId);
        }

        if (order.Status is "cancelled" or "shipped")
        {
            _logger.LogWarning(
                "order.cancel_rejected {OrderId} {Status} {Reason}",
                orderId, order.Status, "terminal_state");
            throw new InvalidOperationException($"Cannot cancel order in state {order.Status}");
        }

        var previousStatus = order.Status;
        order.Status = "cancelled";
        _logger.LogInformation(
            "order.cancelled {OrderId} {PreviousStatus} {CancelReason}",
            orderId, previousStatus, reason);
    }

    private static void ChargePayment(Order order)
    {
        if (order.Amount > 10_000)
            throw new InvalidOperationException($"Amount {order.Amount} exceeds limit");

        order.Status = "charged";
    }
}

public record Order(string OrderId, string UserId, decimal Amount)
{
    public string Status { get; set; } = "pending";
}
