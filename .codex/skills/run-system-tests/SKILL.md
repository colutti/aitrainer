---
name: run-system-tests
description: Run the FityQ test suite in containers only, including backend, frontend, admin, and Playwright e2e. Use when asked to execute all tests, collect per-suite coverage, validate the full system, or report test results from the repo's official containerized flow.
---

# Run System Tests

## Overview

Use this skill to run the project's official validation path without ever running tests directly on the host. Prefer Makefile targets first, then the repository's container scripts and compose services when a target does not exist.

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

In this repository, `make test-once` is a thin wrapper over the existing verify scripts and is the preferred full-suite entrypoint.

### 2. Collect per-suite coverage

Run the coverage-capable suites separately so each result is attributable to one layer:

```bash
make test-backend-cov
```

For frontend and admin, use the containerized Node test services with coverage enabled inside the container, not on the host:

```bash
./scripts/compose.sh -f docker-compose.test.yml run --rm frontend-tests sh -lc "npm ci && npm test -- --coverage"
./scripts/compose.sh -f docker-compose.test.yml run --rm admin-tests sh -lc "npm ci && npm test -- --coverage"
```

The current repository exposes `make test-backend-cov` but not dedicated Make targets for frontend or admin coverage, so use the compose commands above for those suites.

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
- Mention that the full-suite path also validates `backend-admin` through the verify stack even though coverage is only collected for backend, frontend, and admin frontend.

## References

Read this reference when you need the exact project commands and current containerized coverage expectations:

- [test-matrix.md](references/test-matrix.md)
