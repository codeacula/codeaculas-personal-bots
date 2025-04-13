```plaintext
Write tests using a behavior-first mindset. Prefer clarity, reliability, and focus. Apply the following principles:

- **TDD First**: Write the test before implementing the feature. Let the test drive the design.
- **BDD Style Naming**: Use names like `should_return_X_when_Y_given_Z` to describe behavior clearly.
- **AAA Pattern**: Organize each test into:
  - Arrange: Set up data, mocks, and context
  - Act: Run the function or behavior under test
  - Assert: Validate the output or side effects

- **Keep tests focused**:
  - Test one behavior or outcome per test.
  - Use mocks to isolate units and prevent external side effects.
  - Prefer parameterized tests to reduce repetition.

- **Prefer readability over cleverness**:
  - Use meaningful variable names in tests
  - Explain intent through naming, not comments
  - Avoid deeply nested or overly abstract test setups

- **Test the interface, not the implementation**:
  - Don't overfit tests to internal details
  - Focus on public behavior and outcomes

- **Ensure all tests pass before committing code**
```