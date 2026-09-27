---
name: test-engineering
description: TDD red-green-refactor loop, automated unit tests, and Playwright E2E.
---

# Test Engineering & Quality Assurance

Integrates test-driven development (TDD), automated unit testing with Vitest, and browser automation with Playwright:

## 1. Test-Driven Development (TDD) Loop
1. **Red**: Write a failing test specifying expected behavior before writing production code.
2. **Green**: Write the minimal code necessary to pass the test.
3. **Refactor**: Clean up implementation while ensuring tests stay green.
- **Baseline**: Maintain 100% pass rate across all Vitest suites (`rtk npm test`).

## 2. Playwright End-to-End Automation
- **Role-Based Locators**: Use `page.getByRole()`, `page.getByLabel()`, and `page.getByText()`. Never rely on brittle CSS selectors.
- **Auto-Waiting**: Rely on built-in Playwright assertions (`expect(locator).toBeVisible()`). Never use arbitrary `waitForTimeout()`.
- **Page Object Model (POM)**: Encapsulate UI interactions into reusable page objects.
- **Visual Regression**: Validate spatial layouts, responsive canvas elements, and holographic components.
