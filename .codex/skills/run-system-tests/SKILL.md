---
name: run-system-tests
description: Run the FityQ test suite in containers only, including backend, frontend, admin, and Playwright e2e. Use when asked to execute all tests, collect per-suite coverage, validate the full system, or report test results from the repo's official containerized flow.
---

# Run System Tests

## Overview

Use this skill to run the project's official validation path without ever running tests directly on the host. Prefer Makefile targets and container services as the source of truth.

## Rules

- Run tests only through containers.
- Prefer `make` targets defined by the repository.
- Report coverage separately per suite.
- Treat Playwright e2e coverage as conditional: only report code coverage if the stack already produces it. Otherwise report execution status plus the generated Playwright report.
- Do not fall back to host-local `pytest`, `npm test`, or `npx playwright test`.

## Workflow

### 1. Run the full suite first

Start with the repository's official full suite:

```bash
make test-once
```

Use this when the user wants to validate the whole system and does not need per-suite coverage details.

### 2. Collect per-suite coverage

Run the coverage-capable suites separately so each result is attributable to one layer:

```bash
make test-backend-cov
```

For frontend and admin, run the container services with coverage enabled inside the container, not on the host:

```bash
$(COMPOSE_TEST) run --rm frontend-tests sh -lc "npm ci && npm test -- --coverage"
$(COMPOSE_TEST) run --rm admin-tests sh -lc "npm ci && npm test -- --coverage"
```

If the repository later adds Makefile targets for those containerized coverage commands, prefer the Makefile targets over inline commands.

### 3. Run e2e in containers

Run Playwright through the containerized test stack:

```bash
make e2e
```

If a user explicitly asks for e2e coverage, inspect the repo's Playwright and build configuration first. Only report code coverage if the stack already emits a coverage artifact. If it does not, say so plainly and return the Playwright execution report instead of inventing a host-side workaround.

### 4. Summarize results

- Report backend, frontend, admin, and e2e separately.
- Include coverage percentages and any threshold failures for suites that produce coverage.
- Include the Playwright report location when e2e runs.
- If a suite cannot produce coverage in the current stack, say that it is execution-only and do not guess a number.

## References

Read this reference when you need the exact project commands and current containerized coverage expectations:

- [test-matrix.md](references/test-matrix.md)
