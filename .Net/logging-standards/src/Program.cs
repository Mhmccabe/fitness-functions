using FitnessFunctions.Logging.Good;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Serilog;
using Serilog.Events;

// ── Configure Serilog as the logging provider ──────────────────────────────
//
// Serilog is the structured logging backend. It:
//   - Outputs JSON to stdout (for container runtimes and log aggregators)
//   - Enriches every log event with machine name, thread ID, and environment
//   - Can be extended with additional sinks (Seq, Elastic, etc.) without
//     changing any service code — the service only uses ILogger<T>
//
Log.Logger = new LoggerConfiguration()
    .MinimumLevel.Information()
    .MinimumLevel.Override("Microsoft", LogEventLevel.Warning)
    .MinimumLevel.Override("System", LogEventLevel.Warning)
    .Enrich.FromLogContext()           // Picks up ILogger.BeginScope() properties
    .Enrich.WithMachineName()
    .Enrich.WithEnvironmentName()
    .WriteTo.Console(new Serilog.Formatting.Compact.CompactJsonFormatter())
    .CreateLogger();

var builder = Host.CreateDefaultBuilder(args)
    .UseSerilog()  // Replace the default Microsoft logging with Serilog
    .ConfigureServices(services =>
    {
        services.AddScoped<OrderServiceGood>();
    });

var host = builder.Build();

// ── Example usage ──────────────────────────────────────────────────────────
var serviceProvider = host.Services;
using var scope = serviceProvider.CreateScope();
var orderService = scope.ServiceProvider.GetRequiredService<OrderServiceGood>();

var order = orderService.CreateOrder("user-123", 99.99m);
var processed = orderService.ProcessOrder(order.OrderId, order.UserId);

Log.Information("Example run completed {Status}", processed.Status);
Log.CloseAndFlush();
