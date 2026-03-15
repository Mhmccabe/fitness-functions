package example;

import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.lang.ArchRule;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.classes;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;
import static com.tngtech.archunit.library.Architectures.layeredArchitecture;
import static com.tngtech.archunit.library.dependencies.SlicesRuleDefinition.slices;

/**
 * ArchitectureTest — enforces layered architecture using ArchUnit.
 *
 * Rules:
 *   1. Controllers must not access repositories directly
 *   2. Services must not access controllers
 *   3. No circular dependencies between packages
 *   4. Controller classes must reside in the controller package
 *   5. Service classes must reside in the service package
 */
class ArchitectureTest {

    private static JavaClasses classes;

    @BeforeAll
    static void importClasses() {
        classes = new ClassFileImporter()
            .withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS)
            .importPackages("example");
    }

    @Test
    void layeredArchitectureIsRespected() {
        layeredArchitecture()
            .consideringOnlyDependenciesInLayers()
            .layer("Controller").definedBy("example.controller..")
            .layer("Service").definedBy("example.service..")
            .layer("Repository").definedBy("example.repository..")
            .whereLayer("Controller").mayOnlyAccessLayers("Service")
            .whereLayer("Service").mayOnlyAccessLayers("Repository")
            .check(classes);
    }

    @Test
    void controllersMustNotDependOnRepositories() {
        ArchRule rule = noClasses()
            .that().resideInAPackage("example.controller..")
            .should().dependOnClassesThat().resideInAPackage("example.repository..")
            .because("Controllers must delegate to Services, not access Repositories directly");
        rule.check(classes);
    }

    @Test
    void servicesMustNotDependOnControllers() {
        ArchRule rule = noClasses()
            .that().resideInAPackage("example.service..")
            .should().dependOnClassesThat().resideInAPackage("example.controller..")
            .because("Services must not depend on the controller layer");
        rule.check(classes);
    }

    @Test
    void noCircularDependencies() {
        slices().matching("example.(*)..").should().beFreeOfCycles().check(classes);
    }

    @Test
    void controllerClassesMustResideInControllerPackage() {
        ArchRule rule = classes()
            .that().haveSimpleNameEndingWith("Controller")
            .and().doNotHaveSimpleName("OrderControllerBad")
            .should().resideInAPackage("example.controller..")
            .because("Controller classes must be in the controller package");
        rule.check(classes);
    }

    @Test
    void serviceClassesMustResideInServicePackage() {
        ArchRule rule = classes()
            .that().haveSimpleNameEndingWith("Service")
            .should().resideInAPackage("example.service..")
            .because("Service classes must be in the service package");
        rule.check(classes);
    }
}
