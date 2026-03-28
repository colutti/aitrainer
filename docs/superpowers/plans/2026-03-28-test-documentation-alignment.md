# Test Documentation Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align test documentation, the run-system-tests skill, and the Makefile with the containerized test workflow that actually exists in this repository.

**Architecture:** Keep the existing script-based verification flow as the source of truth, expose the missing documented Makefile targets as thin wrappers, and update repo docs plus the local skill docs to reference those real entrypoints and coverage artifacts. Verification should prove the new Makefile targets execute successfully in the current checkout.

**Tech Stack:** GNU Make, bash scripts, Podman/Docker compose, Markdown docs.

---

### Task 1: Map the current test entrypoints into Make targets

**Files:**
- Modify: `Makefile`
- Reference: `scripts/verify/quick.sh`
- Reference: `scripts/verify/e2e.sh`
- Reference: `docker-compose.test.yml`

- [ ] Add phony targets for `test-once`, `e2e`, and `test-backend-cov` as thin wrappers over the existing scripts and compose command.
- [ ] Keep `verify` and `verify-all` intact, and avoid inventing new workflows beyond the documented ones.
- [ ] Make `test-once` run the current full containerized validation path that exists in this repo now.

### Task 2: Update repository documentation to match the real workflow

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`

- [ ] Rewrite the testing sections so they distinguish between verification, per-suite coverage, and Playwright execution-only status.
- [ ] Replace stale references to nonexistent commands with the Makefile targets and script-backed commands that now exist.
- [ ] Document the generated coverage and Playwright report locations where helpful.

### Task 3: Update the local run-system-tests skill docs

**Files:**
- Modify: `.codex/skills/run-system-tests/SKILL.md`
- Modify: `.codex/skills/run-system-tests/references/test-matrix.md`

- [ ] Replace assumptions about missing Makefile targets with the targets added in Task 1.
- [ ] Keep the skill aligned with the current repository behavior, including backend/frontend/admin coverage and Playwright execution-only reporting.

### Task 4: Verify the updated workflow and commit the pending tree

**Files:**
- Verify: `Makefile`
- Verify: `README.md`
- Verify: `AGENTS.md`
- Verify: `.codex/skills/run-system-tests/SKILL.md`
- Verify: `.codex/skills/run-system-tests/references/test-matrix.md`

- [ ] Run `make test-once` and confirm the full containerized workflow passes through the new target.
- [ ] Run `make test-backend-cov` and confirm backend coverage still executes through containers.
- [ ] Run `make e2e` and confirm Playwright still passes and emits the HTML report path.
- [ ] Review `git status`, stage all pending changes, and create one non-amended commit describing the documentation and workflow alignment plus any already-pending repository work.
