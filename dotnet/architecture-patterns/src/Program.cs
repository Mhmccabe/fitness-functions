// Entry point — wires up layers and demonstrates compliant architecture.
using ArchitecturePatterns.Repositories;
using ArchitecturePatterns.Services;
using ArchitecturePatterns.Controllers;

var repository = new OrderRepository();
var service = new OrderService(repository);
var controller = new OrderController(service);

var created = controller.CreateOrder("user-1", 250.00m);
Console.WriteLine($"Created: {created["orderId"]} — {created["status"]}");

var processed = controller.ProcessOrder((string)created["orderId"]);
Console.WriteLine($"Processed: {processed["orderId"]} — {processed["status"]}");
