using System;
using System.Collections.Generic;
using Microsoft.Extensions.Logging;

namespace FitnessFunctions.Logging.Bad;

/// <summary>
/// OrderServiceBad — INTENTIONALLY NON-COMPLIANT
///
/// This class violates every logging standard enforced by the fitness function.
/// Run Semgrep against this file to see all violations detected:
///
///   semgrep --config .semgrep/logging-rules.yml src/OrderServiceBad.cs
///
/// Expected violations:
///   Line 25 — no-console-writeline           (Console.WriteLine)
///   Line 34 — no-string-interpolation-in-log ($"..." in LogInformation)
///   Line 41 — no-string-interpolation-in-log ($"..." in LogWarning)
///   Line 50 — no-string-concat-in-log        (string + in LogError)
///   Line 52 — no-console-writeline           (Console.WriteLine in catch)
/// </summary>
public class OrderServiceBad
{
    // ILogger is injected correctly here — the violations are in the method bodies
    private readonly ILogger<OrderServiceBad> _logger;
    private readonly Dictionary<string, Order> _orders = new();

    public OrderServiceBad(ILogger<OrderServiceBad> logger)
    {
        _logger = logger;
        // VIOLATION: Console.WriteLine at construction time
        Console.WriteLine("OrderServiceBad created");
    }

    public Order ProcessOrder(string orderId, string userId)
    {
        // VIOLATION: string interpolation in log call — eagerly evaluated free text
        _logger.LogInformation($"Processing order {orderId} for user {userId}");

        if (!_orders.TryGetValue(orderId, out var order))
        {
            // VIOLATION: string interpolation in LogWarning
            _logger.LogWarning($"Order {orderId} not found for user {userId}");
            throw new KeyNotFoundException($"Order {orderId} not found");
        }

        try
        {
            ChargePayment(order);
            return order;
        }
        catch (InvalidOperationException ex)
        {
            // VIOLATION: string concatenation in LogError
            _logger.LogError("Payment failed for order " + orderId + ": " + ex.Message);
            // VIOLATION: Console.WriteLine as well
            Console.WriteLine("ERROR: " + ex.Message);
            throw; // log-and-rethrow: duplicate noise in log aggregation
        }
    }

    private static void ChargePayment(Order order)
    {
        if (order.Amount > 10_000)
            throw new InvalidOperationException("Amount exceeds limit");

        order.Status = "charged";
    }
}

public record Order(string OrderId, string UserId, decimal Amount)
{
    public string Status { get; set; } = "pending";
}
