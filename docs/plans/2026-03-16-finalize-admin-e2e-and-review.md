# Finalize Admin E2E Tests and Review Implementation Plan

> Execution workflow: use `.agent/workflows/executing-plans.md` to implement this plan in batches.

**Goal:** Ensure the admin dashboard is fully functional, all E2E tests pass, and Stripe integration is ready for production.

**Architecture:** We use Playwright for E2E testing with mocked API responses for isolation. The Stripe service integrates with external webhooks to manage user subscriptions.

**Tech Stack:** Playwright, React, FastAPI, Stripe API.

---

### Task 1: Verify Admin E2E Tests

**Files:**
- Modify: `frontend/e2e/admin.spec.ts`
- Verify: `frontend/admin/src/features/admin/components/AdminLayout.tsx`

**Step 1: Run the admin E2E tests**

Run: `cd frontend && npx playwright test e2e/admin.spec.ts --project=admin-chromium --workers=1`
Expected: 5 passed tests.

**Step 2: Fix any remaining assertion or element visibility issues**

Ensure the `confirmation-modal` and `confirm-accept` data-testids are correctly hit.

---

### Task 2: Stripe Integration Review

**Files:**
- Doc: `AGENTS.md`
- Env: `.env`

**Step 1: Verify current Stripe implementation**

Check `backend/src/api/endpoints/stripe.py` and ensure the plan mapping logic matches the user's expectations.

**Step 2: Document manual steps for the user**

Inform the user about configuring Price IDs and Webhook Secret.

---

### Task 3: Full Project Quality Check

**Files:**
- Workflow: `.agent/workflows/run-all-tests.md`

**Step 1: Execute all tests and quality checks**

Run: execute the commands documented in `.agent/workflows/run-all-tests.md`

**Step 2: Resolve any lint or type errors**

Ensure zero errors in Ruff, Pylint, and TypeScript.

---

### Task 4: Clean up and Walkthrough

**Files:**
- Workflow: `.agent/workflows/cleancode.md`

**Step 1: Run cleancode**

Run: execute the cleanup commands documented in `.agent/workflows/cleancode.md`

**Step 2: Create walkthrough**

Document completion in `walkthrough.md`.
