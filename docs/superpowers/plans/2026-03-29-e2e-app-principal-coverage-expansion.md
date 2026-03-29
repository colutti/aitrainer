# E2E App Principal Coverage Expansion Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand Playwright so the main app is exercised end-to-end across every major feature area at least once, with each spec creating its own user through the real registration flow.

**Architecture:** Keep the current split between smoke and core suites, but make coverage explicit by feature area instead of by whatever happened to exist already. Normal-user specs must bootstrap their own fresh account via the UI registration and onboarding flow; shared auth state is not the foundation. Demo read-only remains its own isolated suite and does not satisfy normal-app coverage.

**Tech Stack:** Playwright, TypeScript, React app routes, shared test helpers in `frontend/e2e/helpers`, backend E2E login endpoint for deterministic bootstrap only where needed.

---

## Coverage Map

This plan closes the remaining gaps for the main app:

- Auth and onboarding
- Landing locale switch
- Dashboard reflection and regression states
- Workouts CRUD and workout history visibility
- Body: weight, nutrition/macros, and drawer behavior
- Metabolism
- Chat send/receive and assistant response rendering
- Memories CRUD and locale rendering for normal users
- Settings: profile, photo upload, trainer, subscription, integrations
- Integrations UI flows
- Layout regressions that already hurt us: scroll, logout visibility, navigation persistence

Admin coverage is intentionally out of scope for this round.

## Files to Touch

- Modify: `frontend/playwright.config.ts`
- Modify: `frontend/e2e/fixtures.ts`
- Modify: `frontend/e2e/helpers/bootstrap.ts`
- Modify: `frontend/e2e/helpers/ui-actions.ts`
- Modify: `frontend/e2e/helpers/api-client.ts` only if a feature needs direct verification of backend side effects after UI actions
- Create: `frontend/e2e/23-workouts-crud.spec.ts`
- Create: `frontend/e2e/24-body-weight-macros.spec.ts`
- Create: `frontend/e2e/25-metabolism-dashboard.spec.ts`
- Create: `frontend/e2e/26-chat-roundtrip.spec.ts`
- Create: `frontend/e2e/27-memories-locale-crud.spec.ts`
- Create: `frontend/e2e/28-settings-profile-photo.spec.ts`
- Create: `frontend/e2e/29-settings-trainer-subscription-integrations.spec.ts`
- Create: `frontend/e2e/30-dashboard-regressions.spec.ts`
- Modify: `frontend/e2e/20-landing-locale.spec.ts`
- Modify: `frontend/e2e/21-profile-photo.spec.ts`
- Modify: `frontend/e2e/22-demo-memory-locale.spec.ts` or replace it with a normal-user memory locale spec if the demo dataset remains read-only and sparse

## Task 1: Lock the Suite Matrix to the New Coverage Plan

**Files:**
- Modify: `frontend/playwright.config.ts`

- [ ] **Step 1: Update `testMatch` so each new spec is assigned to the correct project**

The config should map the new files into the existing tiers:

- `smoke-chromium`
  - `20-landing-locale.spec.ts` if we want locale coverage in smoke
  - the existing smoke files already covering auth, onboarding, navigation, and dashboard
- `core-chromium`
  - `21-profile-photo.spec.ts`
  - `23-workouts-crud.spec.ts`
  - `24-body-weight-macros.spec.ts`
  - `25-metabolism-dashboard.spec.ts`
  - `26-chat-roundtrip.spec.ts`
  - `27-memories-locale-crud.spec.ts`
  - `28-settings-profile-photo.spec.ts`
  - `29-settings-trainer-subscription-integrations.spec.ts`
  - `30-dashboard-regressions.spec.ts`
- `demo-readonly`
  - keep only the demo-specific read-only spec

- [ ] **Step 2: Re-run the suite selection mentally against the route map**

Every major app route should be represented by at least one spec:

- `/login`
- `/`
- `/onboarding`
- `/dashboard`
- `/dashboard/workouts`
- `/dashboard/body`
- `/dashboard/chat`
- `/dashboard/settings/profile`
- `/dashboard/settings/subscription`
- `/dashboard/settings/trainer`
- `/dashboard/settings/integrations`
- `/dashboard/settings/memories`

If a route is not covered by any spec after the config edit, add it to a spec rather than leaving it implicit.

## Task 2: Make the Bootstrap Helpers the Single Way to Create a User

**Files:**
- Modify: `frontend/e2e/helpers/bootstrap.ts`
- Modify: `frontend/e2e/fixtures.ts`

- [ ] **Step 1: Keep registration through the real app form as the default path**

The existing `registerViaUi` and `bootstrapRegisteredUser` flow should remain the canonical path for new-user specs.

- [ ] **Step 2: Extend the helper surface only where a new spec truly needs more setup**

Add narrowly scoped helpers only if a spec cannot reasonably express its scenario with the current bootstrap plus page interactions.

Examples:

- a helper to navigate to a settings subtab
- a helper to open the weight drawer
- a helper to open the trainer settings card

- [ ] **Step 3: Keep the demo account helper separate**

Do not let demo-only bootstrap leak into the normal-user suite.

## Task 3: Add the Missing Feature Specs for Normal Users

**Files:**
- Create: `frontend/e2e/23-workouts-crud.spec.ts`
- Create: `frontend/e2e/24-body-weight-macros.spec.ts`
- Create: `frontend/e2e/25-metabolism-dashboard.spec.ts`
- Create: `frontend/e2e/26-chat-roundtrip.spec.ts`

- [ ] **Step 1: Write `23-workouts-crud.spec.ts` for workout lifecycle coverage**

This spec should:

- create a fresh user via the real registration flow
- complete onboarding
- open workouts
- create a workout
- verify it appears in the history
- edit a workout field
- delete the workout
- confirm the empty or removed state afterward

That one file should prove the workout area is not just visible but usable.

- [ ] **Step 2: Write `24-body-weight-macros.spec.ts` for the Body area**

This spec should:

- create a fresh user
- complete onboarding
- open `Body`
- switch to `Weight`
- create a weight log
- open the weight drawer
- assert the drawer shows the saved data
- switch to `Dieta e Macros`
- create a nutrition entry or meal log
- confirm the UI reflects the saved nutrition data

The purpose is to prove both tabs are navigable and writable for a normal user.

- [ ] **Step 3: Write `25-metabolism-dashboard.spec.ts` for metabolism and dashboard reflection**

This spec should:

- create a fresh user
- complete onboarding
- create enough body data for the metabolism widgets to render
- verify the metabolism surface loads
- verify the dashboard reflects the seeded state and does not render as empty

The point is to exercise the route and the data flow, not to test a numerical formula in isolation.

- [ ] **Step 4: Write `26-chat-roundtrip.spec.ts` for normal chat interaction**

This spec should:

- create a fresh user
- complete onboarding
- open chat
- send a message
- wait for the assistant response
- assert that the history persists after reload

The chat spec must prove the app supports a normal conversation, not just viewing a static transcript.

## Task 4: Expand Settings, Profile, Integrations, and Locale Coverage

**Files:**
- Create: `frontend/e2e/27-memories-locale-crud.spec.ts`
- Create: `frontend/e2e/28-settings-profile-photo.spec.ts`
- Create: `frontend/e2e/29-settings-trainer-subscription-integrations.spec.ts`
- Modify: `frontend/e2e/20-landing-locale.spec.ts`
- Modify: `frontend/e2e/21-profile-photo.spec.ts`

- [ ] **Step 1: Make `20-landing-locale.spec.ts` cover the app's language switch properly**

The landing spec should assert that switching the visible language changes the UI copy for the current locale, and that the selector still works after reload.

- [ ] **Step 2: Write `27-memories-locale-crud.spec.ts` for normal-user memories**

This spec should:

- create a fresh user
- complete onboarding
- seed or create a memory through the app flow
- verify the memory appears
- switch locale and verify the displayed copy changes
- delete the memory

This spec replaces any memory coverage that was incorrectly tied to the demo account.

- [ ] **Step 3: Write `28-settings-profile-photo.spec.ts` for profile settings**

This spec should:

- create a fresh user
- complete onboarding
- navigate to profile settings
- upload a temporary profile image
- verify the image preview changes
- save the profile
- reload and confirm the profile state persists

The photo upload is the easiest concrete proof that profile settings are exercised end-to-end.

- [ ] **Step 4: Write `29-settings-trainer-subscription-integrations.spec.ts` for the remaining settings surfaces**

This spec should:

- create a fresh user
- complete onboarding
- visit trainer settings
- visit subscription
- visit integrations
- assert the pages load for a normal user
- exercise one mutable action where the app supports it without external credentials

The goal is to cover the route set and the visible controls, not to fake third-party services.

## Task 5: Consolidate Regression Coverage

**Files:**
- Create: `frontend/e2e/30-dashboard-regressions.spec.ts`
- Modify: `frontend/e2e/04-navigation.spec.ts` only if a regression belongs there better than in a dedicated file

- [ ] **Step 1: Add a dedicated regression spec for the things that already broke**

This file should cover:

- dashboard scroll behavior
- logout visibility
- tabs in `Body` remaining clickable
- layout not creating a second scroll container for the page
- no hidden input or drawer behavior that blocks viewing data

- [ ] **Step 2: Keep the regression assertions tied to user-visible behavior**

Do not test implementation details unless there is no stable user-facing alternative.

## Task 6: Decide What to Do With the Current Demo/Memory Locale Spec

**Files:**
- Modify: `frontend/e2e/22-demo-memory-locale.spec.ts`
- Or create: `frontend/e2e/27-memories-locale-crud.spec.ts` and delete the demo-focused memory locale spec if it cannot be made normal-user based

- [ ] **Step 1: Remove any dependency on the demo account for normal coverage**

If the current memory locale spec still relies on the demo dataset, move that behavior into the demo-only suite or replace it with a fresh-user memory test.

- [ ] **Step 2: Keep locale assertions, but apply them to a user created in the test**

Locale-sensitive rendering belongs in the normal-user coverage because the requirement is to exercise the app, not the demo.

## Task 7: Validate the Expanded Coverage End-to-End

**Files:**
- None; this is verification only

- [ ] **Step 1: Run frontend lint and typecheck**

Run:

```bash
cd frontend
npm run lint
npm run typecheck
```

- [ ] **Step 2: Run the smoke tier**

Run:

```bash
cd frontend
npx playwright test --project smoke-chromium --reporter=line
```

Expected:
- all smoke specs pass
- the locale spec remains stable in the browser

- [ ] **Step 3: Run the expanded core tier**

Run:

```bash
cd frontend
npx playwright test --project core-chromium --reporter=line
```

Expected:
- every normal-user feature spec passes
- the new coverage now exercises the full main app at least once

- [ ] **Step 4: Run the demo suite separately**

Run:

```bash
cd frontend
npx playwright test --project demo-readonly --reporter=line
```

Expected:
- demo remains read-only
- normal-user coverage does not depend on demo behavior

## Acceptance Criteria

- Every major main-app route has at least one independent e2e spec.
- Every spec creates its own normal user through the app's registration flow unless it is explicitly demo-only.
- Onboarding is reused through helpers, not copied into every spec.
- The current demo read-only suite remains isolated and does not stand in for normal functionality.
- `frontend` lint, typecheck, smoke, core, and demo Playwright projects all pass after the expansion.

## Notes on Scope

- Admin app coverage is explicitly deferred to a later plan.
- External service flows are not being faked in this round.
- If a feature cannot be driven reliably through the UI, use a narrow helper or API assertion only to verify the UI action's effect, not to bypass the flow itself.
