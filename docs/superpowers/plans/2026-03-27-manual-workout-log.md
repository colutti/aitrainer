# Manual Workout Log Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a manual workout logging flow with a lateral drawer, real create/save behavior, and user-history exercise suggestions while keeping the current Hevy-compatible workout log model.

**Architecture:** Extend the existing workout CRUD instead of adding a new entity. Keep the backend model unchanged for persisted workout logs, add a lightweight exercise-suggestions endpoint sourced from the user's existing logs, and rework the frontend workout drawer/store/API around that contract using TDD.

**Tech Stack:** FastAPI, Pytest, React 19, TypeScript, Zustand, React Hook Form, Vitest

---

### Task 1: Lock API contracts with tests

**Files:**
- Modify: `backend/tests/unit/api/test_workout_api.py`
- Modify: `frontend/src/features/workouts/api/workouts-api.test.ts`
- Modify: `frontend/src/shared/hooks/useWorkout.test.ts`

- [ ] Add failing backend tests for creating a manual workout and listing suggested exercise names.
- [ ] Run targeted backend tests and confirm they fail for the new exercise-suggestions contract.
- [ ] Add failing frontend API/store tests for create workout, fetch workout types, fetch exercise suggestions, and corrected `/workout` endpoints.
- [ ] Run targeted frontend tests and confirm they fail before implementation.

### Task 2: Implement backend support for manual logging helpers

**Files:**
- Modify: `backend/src/repositories/workout_repository.py`
- Modify: `backend/src/services/database.py`
- Modify: `backend/src/api/endpoints/workout.py`
- Verify: `backend/src/api/models/workout_log.py`

- [ ] Add repository/database support for distinct user exercise names from existing workout logs.
- [ ] Expose a `GET /workout/exercises` endpoint that returns sorted exercise names for the authenticated user.
- [ ] Keep `POST /workout` on the existing `WorkoutLog` shape with `source="manual"` allowed and no `external_id` requirement.
- [ ] Run targeted backend tests until green.

### Task 3: Align frontend workout data layer

**Files:**
- Modify: `frontend/src/features/workouts/api/workouts-api.ts`
- Modify: `frontend/src/shared/hooks/useWorkout.ts`
- Modify: `frontend/src/shared/types/workout.ts`

- [ ] Add client methods/types for create workout, fetch workout types, and fetch exercise suggestions.
- [ ] Refactor the workout store to use the `workoutsApi` contract and correct `/workout` endpoints.
- [ ] Add store actions needed by the drawer without over-expanding scope.
- [ ] Run targeted API/store tests until green.

### Task 4: Rebuild the workout drawer in TDD

**Files:**
- Modify: `frontend/src/features/workouts/components/WorkoutDrawer.test.tsx`
- Modify: `frontend/src/features/workouts/components/WorkoutDrawer.tsx`

- [ ] Write failing drawer tests for create mode, exercise suggestion rendering, add/remove exercise, add/duplicate/remove set, validation, and submit payload shape.
- [ ] Run the drawer tests and confirm the failures are real behavior gaps.
- [ ] Implement the minimal drawer behavior to pass: workout details section, expandable exercise cards, set rows, sticky actions, and submit handling.
- [ ] Keep exercise input free-form with assistive suggestions from user history.
- [ ] Re-run drawer tests until green.

### Task 5: Integrate the page flow

**Files:**
- Modify: `frontend/src/features/workouts/WorkoutsPage.tsx`
- Modify: `frontend/src/features/workouts/WorkoutsPage.test.tsx`
- Verify: `frontend/src/features/workouts/components/WorkoutsView.tsx`

- [ ] Add failing integration tests for opening the drawer, saving a new workout, refreshing the list, and surfacing errors without losing form state.
- [ ] Implement the page wiring needed for create/edit drawer flows using the existing page structure.
- [ ] Run page tests until green.

### Task 6: Verification

**Files:**
- No code changes required unless verification finds issues.

- [ ] Run targeted backend workout tests.
- [ ] Run targeted frontend workout tests.
- [ ] Run `cd frontend && npm run typecheck`.
- [ ] Fix any failures and re-run before claiming completion.
