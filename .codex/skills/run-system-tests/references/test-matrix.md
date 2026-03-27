# Test Matrix

## Source of Truth

- `Makefile`
- `docker-compose.test.yml`
- `frontend/vitest.config.ts`
- `frontend/admin/vitest.config.ts`
- `frontend/playwright.config.ts`

## Containerized Commands

### Full Suite

```bash
make test-once
```

Runs backend, frontend, admin, and Playwright e2e through the test stack.

### Backend Coverage

```bash
make test-backend-cov
```

Runs `pytest --cov=src --cov-report=html --cov-report=term-missing` in the backend test container.

### Frontend Coverage

```bash
$(COMPOSE_TEST) run --rm frontend-tests sh -lc "npm ci && npm test -- --coverage"
```

### Admin Coverage

```bash
$(COMPOSE_TEST) run --rm admin-tests sh -lc "npm ci && npm test -- --coverage"
```

### E2E

```bash
make e2e
```

Runs Playwright in the containerized test stack against the real backend and frontend services.

## Coverage Notes

- Frontend and admin coverage are produced by Vitest in containerized Node services.
- The current Playwright config does not define code coverage instrumentation.
- If e2e coverage is requested, only report it when the repository already emits a coverage artifact for the Playwright run.
- If no e2e coverage artifact exists, report e2e execution status and the HTML report instead of fabricating coverage.

## Output Expectations

- Report each suite separately.
- Include coverage percentages for suites that emit them.
- Include threshold failures and test failures explicitly.
- Keep the final answer grounded in container output only.
