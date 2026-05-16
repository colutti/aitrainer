# Plan and Hevy Consistency Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** stop destructive plan/hevy updates and make the current architecture safe enough to support future explicit reconciliation.

**Architecture:** keep the current singleton `UserPlan`, but harden it so partial updates preserve untouched training state. For Hevy, fetch routines completely, expose safer identifiers, and reject destructive exercise-list replacements unless explicitly intended.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, Pytest, MongoDB, Hevy API

---

### Task 1: Lock in plan merge regressions

**Files:**
- Modify: `backend/tests/test_plan_service.py`
- Modify: `backend/tests/test_master_plan_service.py`

- [ ] Add failing tests proving omitted routines and omitted weekly schedule entries are preserved on plan update.
- [ ] Add failing tests proving `timeline.start_date` and `created_at` are preserved on non-structural updates.
- [ ] Run targeted tests and confirm failure.

### Task 2: Fix singleton plan merge semantics

**Files:**
- Modify: `backend/src/services/plan_service.py`
- Modify: `backend/src/repositories/plan_repository.py`
- Modify: `backend/src/api/endpoints/plan.py`
- Test: `backend/tests/test_plan_service.py`
- Test: `backend/tests/test_master_plan_service.py`
- Test: `backend/tests/integration/test_plan_endpoints.py`

- [ ] Implement merge logic that preserves omitted routines and omitted weekly schedule items instead of replacing the whole program.
- [ ] Preserve original `created_at` and timeline start on updates.
- [ ] Make API validation use the latest stored plan consistently.
- [ ] Add/adjust repository singleton enforcement to use a unique user key.
- [ ] Run targeted tests and confirm pass.

### Task 3: Lock in Hevy pagination and destructive update regressions

**Files:**
- Modify: `backend/tests/unit/services/test_hevy_tools.py`
- Modify: `backend/tests/unit/services/test_hevy_service.py`

- [ ] Add failing tests proving routine lookup reads across all Hevy pages.
- [ ] Add failing tests proving single-exercise replacement cannot accidentally overwrite a full routine via `update_hevy_routine`.
- [ ] Add failing tests proving list responses expose enough identity/count data for safe follow-up.
- [ ] Run targeted tests and confirm failure.

### Task 4: Harden Hevy service and tools

**Files:**
- Modify: `backend/src/services/hevy_service.py`
- Modify: `backend/src/services/hevy_tools.py`
- Test: `backend/tests/unit/services/test_hevy_tools.py`
- Test: `backend/tests/unit/services/test_hevy_service.py`

- [ ] Add service-level helper(s) to fetch all routines safely across pages.
- [ ] Update tools to use exact IDs where possible and scan all pages when resolving titles.
- [ ] Make `list_hevy_routines` expose routine IDs and full-page context.
- [ ] Reject structural exercise-list replacement unless the caller explicitly opts into a full rebuild.
- [ ] Keep single-exercise replacement on the dedicated tool path.
- [ ] Run targeted tests and confirm pass.

### Task 5: Tighten graph/prompt guardrails

**Files:**
- Modify: `backend/src/services/graph/conversation_graph.py`
- Modify: `backend/src/services/agents/config/prompts/training_specialist.md`
- Modify: `backend/src/services/agents/config/prompts/coach_reply.md`
- Modify: `backend/tests/unit/services/test_conversation_graph.py`

- [ ] Add regression tests ensuring the coach does not imply complete Hevy review without evidence.
- [ ] Tighten coach/training behavior so incomplete tool evidence is surfaced as uncertainty instead of invented technical failures.
- [ ] Run targeted tests and confirm pass.

### Task 6: Verify backend surface and document outcomes

**Files:**
- Modify: `AGENTS.md`

- [ ] Update project operational guidance if validation workflow or behavioral guarantees changed.
- [ ] Run backend validation gates after the last edit.
- [ ] Summarize remaining gaps toward full drift/reconciliation architecture.
