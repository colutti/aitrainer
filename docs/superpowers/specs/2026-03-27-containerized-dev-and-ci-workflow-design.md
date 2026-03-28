# Containerized Dev And CI Workflow Design

Date: 2026-03-27
Status: Approved for planning

## Goal

Restructure the local development, verification, and CI-facing workflow so the project can be operated through a small set of intuitive commands, with implementation logic moved out of the `Makefile` and into containerized scripts.

The new workflow should isolate development, debugging, quality checks, testing, E2E, and security scanning from host-local differences as much as possible.

## Product Decision Summary

- Keep only a small public command surface in `Makefile`.
- Move orchestration logic into shell scripts under `scripts/`.
- Run official dev and verification workflows inside containers.
- Use one main development command:
  - `make dev`
- Use one fast validation command:
  - `make verify`
- Use one complete validation command:
  - `make verify-all`
- Remove old public `Makefile` commands instead of keeping a large compatibility layer.

## Public Command Surface

The final public `Makefile` should expose only these commands:

- `make dev`
- `make stop`
- `make reset`
- `make logs`
- `make verify`
- `make verify-all`

### Command Intent

- `dev`
  - starts the full local development environment
  - includes main app, admin app, and required dependencies
- `stop`
  - stops the running local development environment cleanly
- `reset`
  - performs a stronger cleanup and restarts from a clean containerized state
- `logs`
  - streams logs for the active development stack with useful grouping
- `verify`
  - runs the fast containerized validation gate
- `verify-all`
  - runs the full validation gate, including E2E and security scans

## Non-Goals

- No host-local official workflow for lint, typecheck, tests, or debugging.
- No large backward-compatible alias list in the new `Makefile`.
- No requirement to preserve the current command names.
- No partial split where some validation still depends on host `.venv` or host `npm`.

## Architecture Direction

### Makefile Role

The `Makefile` becomes a minimal public entrypoint only.

It should:

- map each public command to a script
- avoid embedding orchestration logic
- avoid repeating compose command fragments
- avoid long multi-step recipes inline

### Scripts Role

All orchestration logic should move into scripts.

Suggested layout:

- `scripts/lib/`
- `scripts/dev/`
- `scripts/verify/`

### `scripts/lib/`

Shared helpers for:

- compose invocation
- logging and status output
- environment checks
- cleanup utilities
- error formatting

Suggested internal files:

- `scripts/lib/compose.sh`
- `scripts/lib/log.sh`
- `scripts/lib/checks.sh`

### `scripts/dev/`

Development lifecycle scripts:

- `scripts/dev/dev.sh`
- `scripts/dev/stop.sh`
- `scripts/dev/reset.sh`
- `scripts/dev/logs.sh`

Responsibilities:

- combine the right compose files
- print what is starting or stopping
- surface service URLs
- fail with actionable messages if required container tools are not working

### `scripts/verify/`

Validation orchestration scripts:

- `scripts/verify/quick.sh`
- `scripts/verify/all.sh`
- optional internal helpers:
  - `scripts/verify/backend.sh`
  - `scripts/verify/backend-admin.sh`
  - `scripts/verify/frontend.sh`
  - `scripts/verify/frontend-admin.sh`
  - `scripts/verify/e2e.sh`
  - `scripts/verify/security.sh`

Responsibilities:

- run category checks in containers
- print current phase clearly
- stop on first failed stage
- preserve enough detail for debugging

## Compose Structure

Compose files should be split by responsibility rather than by exact final command.

Suggested structure:

- `compose/base.yml`
- `compose/dev.app.yml`
- `compose/dev.admin.yml`
- `compose/verify.yml`
- `compose/e2e.yml`
- `compose/security.yml`

### `compose/base.yml`

Contains shared infrastructure and common network/volume definitions:

- mongo
- qdrant
- stripe-mock
- networks
- persistent volumes

### `compose/dev.app.yml`

Contains main application development services:

- backend
- frontend

### `compose/dev.admin.yml`

Contains admin development services:

- backend-admin
- frontend-admin

### `compose/verify.yml`

Contains quality and test runner services:

- backend verify runner
- backend-admin verify runner
- frontend verify runner
- frontend-admin verify runner

These runners should execute the official fast validation gate in containers.

### `compose/e2e.yml`

Contains Playwright and any E2E-specific runner services.

### `compose/security.yml`

Contains security scan runner services, such as:

- semgrep
- dependency scanning or SCA tools

## Workflow Definitions

### `make dev`

Runs the full local development stack using:

- `compose/base.yml`
- `compose/dev.app.yml`
- `compose/dev.admin.yml`

Expected services:

- backend
- frontend
- backend-admin
- frontend-admin
- mongo
- qdrant
- stripe-mock

This replaces the current fragmented requirement to run multiple commands for main app, admin, and dependencies.

### `make verify`

Runs the fast validation gate using containers only.

Included:

- backend lint and type checks
- backend-admin lint and type checks
- frontend lint and type checks
- frontend-admin lint and type checks
- backend tests
- frontend tests
- frontend-admin tests

Excluded:

- Playwright E2E
- security scans

### `make verify-all`

Runs:

1. `verify`
2. E2E
3. security scans

This becomes the closest local equivalent to a full CI gate.

## Error Reporting And UX

The scripts should be more verbose and clearer than the current `Makefile`.

Each major step should print:

- what stage is running
- which compose stack is being invoked
- which service failed
- the exact command category that failed

Failure messages should prefer:

- short summary first
- actionable next step second

Example:

- `VERIFY FAILED: frontend typecheck`
- `Inspect logs with: make logs`

## Cleanup Semantics

### `make stop`

Stops the development stack cleanly without being destructive by default.

### `make reset`

Should perform a stronger cleanup for stale containers, orphans, and inconsistent local state.

It may remove:

- stopped containers for the project
- orphaned services for the project
- transient verification containers

It should avoid deleting unrelated containers.

Whether named volumes are removed by default in `reset` should be decided in implementation, but the default should prioritize predictable recovery from broken local state.

## Testing And Verification Strategy

### Scripts

Each public script path should be testable or at least dry-runnable with deterministic behavior where practical.

At minimum, implementation should verify:

- compose file combinations are correct
- command names map to the intended scripts
- `verify` and `verify-all` execute the intended stages in order

### Migration Verification

Before removing old commands, confirm:

- `make dev` fully replaces the old manual multi-command startup need
- `make verify` covers the fast daily quality gate
- `make verify-all` covers the complete gate

## Deletions And Simplification

The old `Makefile` command surface should be removed rather than preserved.

This includes:

- fragmented local app/admin startup commands
- duplicated test commands by implementation detail
- mixed host-local and containerized validation commands
- legacy debug/rebuild commands that are replaced by the new workflow

The goal is a smaller, clearer interface, not backward compatibility.

## Recommended Implementation Boundary

This design is focused enough for one implementation plan:

- simplify `Makefile`
- add script orchestration
- modularize compose files
- containerize the official dev and validation workflows
- remove obsolete public commands
