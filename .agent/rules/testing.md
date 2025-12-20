# Testing Rules

## Cypress E2E Tests

### Test Structure

- Tests must be independent (no dependencies on other tests)
- Use descriptive test names
- Clean up test data after each test
- Use `beforeEach` for common setup

### Selectors

- **Always use `data-cy` attributes** for element selection
- Avoid fragile selectors (classes, tags)
- Never select by text content that might change

### Assertions

- Prefer `cy.should()` with assertions over `cy.wait()`
- Test both happy paths and error cases
- Verify UI feedback for user actions
- Check loading states and error messages

### Running Tests

- Run `/test` workflow before every commit
- Fix failing tests immediately
- Never skip tests without documenting why
- Run tests in CI/CD pipeline

## Backend Unit Tests

### Coverage

- Write tests for all new endpoints
- Test edge cases and error conditions
- Aim for 80%+ code coverage
- Test validation logic thoroughly

### Mocking

- Mock external APIs (Gemini, Mem0) in unit tests
- Use fixtures for test data
- Mock database calls for pure unit tests
- Integration tests should use test database

### Test Organization

- Group tests by feature/module
- Use descriptive test names
- Keep tests simple and focused
- Follow AAA pattern: Arrange, Act, Assert

## Quality Checks

### Pre-Commit Checklist

- [ ] Run `/format` workflow
- [ ] Run `/lint` workflow
- [ ] Run `/test` workflow
- [ ] All tests pass
- [ ] No new linter warnings
- [ ] Code is properly formatted

### Pre-Deploy Checklist

- [ ] All E2E tests pass
- [ ] Health check endpoint works
- [ ] No secrets in code
- [ ] Environment variables documented
- [ ] Logs don't contain sensitive data
- [ ] Build succeeds with `/rebuild`
