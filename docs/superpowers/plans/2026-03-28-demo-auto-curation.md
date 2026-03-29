# Demo Auto-Curation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace manual message-by-message demo curation with an automatic episode-based pipeline that publishes a read-only demo account and supports pruning published demo chat from admin.

**Architecture:** Extend the existing demo snapshot script into a deterministic pipeline that exports raw source data, segments messages into episodes, scores and reduces the best episodes, sanitizes the selected content, and publishes both chat data and demo curation metadata. Add admin backend/frontend surfaces to inspect and delete published demo episodes or messages without re-enabling normal writes for the demo account.

**Tech Stack:** FastAPI, Python 3.12+, MongoDB, React 19, TypeScript, Vitest, Pytest

---

### Task 1: Restore read-only demo account foundation in the main app

**Files:**
- Create: `backend/src/core/demo_access.py`
- Modify: `backend/src/api/models/user_profile.py`
- Modify: `backend/src/api/endpoints/user.py`
- Modify: `backend/src/api/endpoints/message.py`
- Modify: `backend/src/api/endpoints/workout.py`
- Modify: `backend/src/api/endpoints/nutrition.py`
- Modify: `backend/src/api/endpoints/weight.py`
- Modify: `backend/src/api/endpoints/trainer.py`
- Modify: `backend/src/api/endpoints/onboarding.py`
- Modify: `backend/src/api/endpoints/hevy.py`
- Modify: `backend/src/api/endpoints/memory.py`
- Modify: `backend/src/api/endpoints/telegram.py`
- Modify: `backend/src/api/endpoints/stripe.py`
- Modify: `backend/src/repositories/user_repository.py`
- Modify: `backend/src/services/database.py`
- Test: `backend/tests/unit/api/test_user_endpoints.py`
- Test: `backend/tests/unit/api/test_message_endpoints.py`
- Test: `backend/tests/unit/api/test_workout_routes_unit.py`
- Test: `backend/tests/unit/api/test_nutrition_api.py`
- Test: `backend/tests/unit/api/test_weight_api.py`

- [ ] **Step 1: Write failing backend tests for demo read-only behavior**
- [ ] **Step 2: Run targeted pytest commands and confirm the new tests fail for the expected reasons**
- [ ] **Step 3: Implement `is_demo` exposure plus a reusable write guard dependency**
- [ ] **Step 4: Apply the guard to mutable endpoints and the `/user/me` response**
- [ ] **Step 5: Re-run targeted backend tests until they pass**

### Task 2: Replace the raw demo export with episode-based auto-curation

**Files:**
- Create: `backend/scripts/demo_snapshot_lib.py`
- Modify: `backend/scripts/build_demo_snapshot.py`
- Test: `backend/tests/unit/scripts/test_demo_snapshot_lib.py`

- [ ] **Step 1: Write failing unit tests for timestamp parsing, episode segmentation, ranking quotas, message reduction, and publish payload shaping**
- [ ] **Step 2: Run `pytest backend/tests/unit/scripts/test_demo_snapshot_lib.py -v` and verify failures**
- [ ] **Step 3: Implement deterministic helpers for parsing, segmenting, scoring, selecting, reducing, sanitizing, and materializing demo chat**
- [ ] **Step 4: Extend the CLI flow with segment/rank/reduce metadata and published demo curation collections**
- [ ] **Step 5: Re-run the script unit tests and a local `export -> prepare` smoke path**

### Task 3: Add admin backend support for published demo pruning

**Files:**
- Modify: `backend-admin/src/api/endpoints/admin_users.py`
- Create: `backend-admin/tests/test_admin_users.py`

- [ ] **Step 1: Write failing backend-admin tests for listing demo snapshot metadata and deleting published demo episodes/messages**
- [ ] **Step 2: Run targeted pytest and confirm the failures are on missing behavior**
- [ ] **Step 3: Implement read APIs and delete actions for demo curation data in the existing admin users surface**
- [ ] **Step 4: Preserve demo-account protection for normal update/delete flows**
- [ ] **Step 5: Re-run backend-admin targeted tests until they pass**

### Task 4: Add admin frontend controls for inspecting and pruning demo chat

**Files:**
- Modify: `frontend/admin/src/types/admin-api.ts`
- Modify: `frontend/src/shared/types/admin.ts`
- Modify: `frontend/admin/src/features/admin/components/AdminUsersPage.tsx`
- Modify: `frontend/admin/src/features/admin/components/AdminUsersPage.test.tsx`

- [ ] **Step 1: Write failing Vitest coverage for demo snapshot rendering, episode listing, and delete actions**
- [ ] **Step 2: Run the targeted Vitest command and confirm the expected failures**
- [ ] **Step 3: Implement the demo overview, episode detail, and delete flows in the existing admin users UI**
- [ ] **Step 4: Keep demo users protected from normal edit/delete actions**
- [ ] **Step 5: Re-run the targeted frontend-admin tests until they pass**

### Task 5: Restore main frontend demo indicators and complete verification

**Files:**
- Modify: `frontend/src/shared/hooks/useAuth.ts`
- Modify: `frontend/src/shared/hooks/useAuth.test.ts`
- Modify: `frontend/src/features/chat/components/ChatView.tsx`
- Modify: `frontend/src/features/chat/components/ChatView.test.tsx`
- Modify: `frontend/src/shared/components/layout/PremiumLayout.tsx`
- Modify: `frontend/src/shared/components/layout/PremiumLayout.test.tsx`

- [ ] **Step 1: Write failing tests for `is_demo` auth state and chat/layout read-only indicators**
- [ ] **Step 2: Run targeted Vitest and verify the failures**
- [ ] **Step 3: Implement `is_demo` handling in auth, chat, and layout**
- [ ] **Step 4: Re-run targeted main frontend tests until they pass**
- [ ] **Step 5: Run surface validation gates**

### Task 6: Run final verification gates

**Files:**
- Modify: `docs/superpowers/specs/2026-03-28-demo-auto-curation-design.md` only if implementation forces a spec correction

- [ ] **Step 1: Run `cd backend && .venv/bin/ruff check src tests scripts/build_demo_snapshot.py scripts/demo_snapshot_lib.py`**
- [ ] **Step 2: Run `cd backend && .venv/bin/pylint src`**
- [ ] **Step 3: Run `cd backend-admin && .venv/bin/pylint src && .venv/bin/pyright src`**
- [ ] **Step 4: Run `cd frontend && npm run lint && npm run typecheck`**
- [ ] **Step 5: Run `cd frontend/admin && npm run lint && npm run typecheck`**
- [ ] **Step 6: Run the targeted pytest and Vitest suites touched by the implementation and record actual pass/fail status**

