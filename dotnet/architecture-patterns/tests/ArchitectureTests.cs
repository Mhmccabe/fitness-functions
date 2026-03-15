using NetArchTest.Rules;
using Xunit;

namespace ArchitecturePatterns.Tests;

/// <summary>
/// ArchitectureTests — enforces layered architecture using NetArchTest.
///
/// Rules:
///   1. Controllers must not depend on Repositories namespace
///   2. Services must not depend on Controllers namespace
///   3. Controller class names must end with "Controller"
///   4. Service class names must end with "Service"
/// </summary>
public class ArchitectureTests
{
    private static readonly Types AllTypes = Types
        .InNamespace("ArchitecturePatterns")
        .That()
        .DoNotResideInNamespace("ArchitecturePatterns.Bad");

    [Fact]
    public void Controllers_ShouldNotDependOn_Repositories()
    {
        var result = AllTypes
            .ResideInNamespace("ArchitecturePatterns.Controllers")
            .ShouldNot()
            .HaveDependencyOn("ArchitecturePatterns.Repositories")
            .GetResult();

        Assert.True(result.IsSuccessful,
            "Controllers must not import from the Repositories namespace. " +
            "Use IOrderService instead.");
    }

    [Fact]
    public void Services_ShouldNotDependOn_Controllers()
    {
        var result = AllTypes
            .ResideInNamespace("ArchitecturePatterns.Services")
            .ShouldNot()
            .HaveDependencyOn("ArchitecturePatterns.Controllers")
            .GetResult();

        Assert.True(result.IsSuccessful,
            "Services must not depend on the Controllers namespace.");
    }

    [Fact]
    public void ControllerClasses_ShouldHaveSuffix_Controller()
    {
        var result = AllTypes
            .ResideInNamespace("ArchitecturePatterns.Controllers")
            .Should()
            .HaveNameEndingWith("Controller")
            .GetResult();

        Assert.True(result.IsSuccessful,
            "All types in the Controllers namespace must be named *Controller.");
    }

    [Fact]
    public void ServiceClasses_ShouldHaveSuffix_Service()
    {
        var result = Types
            .InNamespace("ArchitecturePatterns.Services")
            .That()
            .AreClasses()
            .Should()
            .HaveNameEndingWith("Service")
            .GetResult();

        Assert.True(result.IsSuccessful,
            "All classes in the Services namespace must be named *Service.");
    }
}
