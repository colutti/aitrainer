# Stripe Hybrid Test Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir uma estratégia híbrida de testes Stripe que combine `stripe-mock`, Stripe real em `test mode` e Playwright para cobrir com alta confiança criação, mudança, cancelamento e falha de assinatura.

**Architecture:** A implementação separa testes rápidos de contrato e regras locais dos testes live contra Stripe real. Um test harness centraliza criação de dados, triggering de eventos, polling de convergência e cleanup. Playwright reutiliza esse harness para validar as jornadas críticas da UI sem duplicar lógica de billing.

**Tech Stack:** FastAPI, Pytest, Playwright, Stripe API, Stripe CLI, Podman Compose, GitHub Actions or equivalent CI runner.

---

## File Structure / Ownership

- Modify: `backend/src/core/config.py`
- Modify: `backend/src/api/endpoints/stripe.py`
- Modify: `docker-compose.test.yml`
- Modify: `compose/e2e.yml`
- Modify: `README.md`
- Create: `backend/tests/integration/stripe/conftest.py`
- Create: `backend/tests/integration/stripe/test_checkout_lifecycle.py`
- Create: `backend/tests/integration/stripe/test_subscription_state_transitions.py`
- Create: `backend/tests/integration/stripe/test_billing_cycle_resets.py`
- Create: `backend/tests/integration/stripe/test_webhook_idempotency_live.py`
- Create: `backend/tests/integration/stripe/stripe_harness.py`
- Create: `backend/tests/integration/stripe/profile_assertions.py`
- Create: `frontend/e2e/stripe/checkout-return.spec.ts`
- Create: `frontend/e2e/stripe/cancellation-and-locks.spec.ts`
- Create: `frontend/e2e/stripe/fixtures/stripeTestHarness.ts`
- Create: `scripts/test/run-stripe-live.sh`
- Create: `scripts/test/run-stripe-playwright.sh`
- Create: `scripts/test/stripe_cli_forward.sh`
- Create: `.github/workflows/stripe-live-tests.yml` or repository CI equivalent if present
- Modify: `frontend/e2e/15-subscription.spec.ts`

### Task 1: Formalize live Stripe test configuration

**Files:**
- Modify: `backend/src/core/config.py`
- Modify: `docker-compose.test.yml`
- Modify: `compose/e2e.yml`
- Create: `scripts/test/stripe_cli_forward.sh`
- Modify: `README.md`

- [ ] **Step 1: Write failing config tests for live Stripe env parsing**

Add tests asserting new live env vars are optional but validated when present:

- `STRIPE_LIVE_TEST_ENABLED`
- `STRIPE_TEST_SECRET_KEY`
- `STRIPE_TEST_WEBHOOK_SECRET`
- `STRIPE_CLI_WEBHOOK_FORWARD_URL`

- [ ] **Step 2: Run the config tests and confirm failure**

Run: `cd backend && .venv/bin/pytest tests/integration/test_settings.py -v`
Expected: FAIL because the live Stripe settings do not exist yet.

- [ ] **Step 3: Implement live Stripe config surface**

Update `backend/src/core/config.py` to add explicit settings for live test mode and CLI forwarding, keeping them isolated from default app execution.

- [ ] **Step 4: Add container wiring for live Stripe runs**

Update `docker-compose.test.yml` and `compose/e2e.yml` so backend/playwright services can receive live Stripe test envs without changing the default `stripe-mock` path.

- [ ] **Step 5: Add a small CLI forwarding helper**

Create `scripts/test/stripe_cli_forward.sh` to start `stripe listen` in a deterministic way and write the signing secret to a temporary env file or stdout contract consumed by the runner.

- [ ] **Step 6: Document local and CI prerequisites**

Document:
- what still uses `stripe-mock`
- what needs Stripe real secrets
- how to boot the live test flow locally

- [ ] **Step 7: Verify backend and docs gates**

Run:
- `cd backend && .venv/bin/ruff check src tests`
- `cd backend && .venv/bin/pylint src`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/src/core/config.py docker-compose.test.yml compose/e2e.yml scripts/test/stripe_cli_forward.sh README.md
git commit -m "test: add live stripe test configuration"
```

### Task 2: Build the Stripe live test harness

**Files:**
- Create: `backend/tests/integration/stripe/stripe_harness.py`
- Create: `backend/tests/integration/stripe/profile_assertions.py`
- Create: `backend/tests/integration/stripe/conftest.py`

- [ ] **Step 1: Write failing harness tests**

Create tests for:
- unique metadata correlation per test
- cleanup idempotency
- wait helpers timing out with clear error
- profile polling converging on expected state

- [ ] **Step 2: Run the harness tests and confirm failure**

Run: `cd backend && .venv/bin/pytest backend/tests/integration/stripe/conftest.py -v`
Expected: FAIL because the harness does not exist.

- [ ] **Step 3: Implement the Stripe client wrapper**

Create `stripe_harness.py` with helpers for:
- creating test customers
- creating checkout sessions and direct subscriptions
- updating prices
- canceling now / at period end
- reactivating
- looking up invoices and subscriptions by metadata

- [ ] **Step 4: Implement app convergence assertions**

Create `profile_assertions.py` with polling helpers that assert backend profile state:
- `subscription_plan`
- `stripe_subscription_status`
- `current_billing_cycle_start`
- counters reset state
- trainer fallback state

- [ ] **Step 5: Add pytest fixtures**

Create fixtures for:
- `stripe_live_client`
- `test_user_factory`
- `stripe_test_run_id`
- `cleanup_registry`
- `await_profile_state`

- [ ] **Step 6: Re-run the harness tests**

Run: `cd backend && .venv/bin/pytest backend/tests/integration/stripe -k harness -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/tests/integration/stripe/stripe_harness.py backend/tests/integration/stripe/profile_assertions.py backend/tests/integration/stripe/conftest.py
git commit -m "test: add stripe live integration harness"
```

### Task 3: Cover new subscription and checkout lifecycle against Stripe real

**Files:**
- Create: `backend/tests/integration/stripe/test_checkout_lifecycle.py`
- Modify: `backend/src/api/endpoints/stripe.py`

- [ ] **Step 1: Write failing integration tests for first subscription**

Cover:
- checkout session creation
- checkout completion reflected in local profile
- first active subscription moves user to `Pro`
- customer id persisted

- [ ] **Step 2: Run the checkout lifecycle tests and confirm failure**

Run: `cd backend && .venv/bin/pytest backend/tests/integration/stripe/test_checkout_lifecycle.py -v`
Expected: FAIL because the live orchestration path is not complete yet.

- [ ] **Step 3: Tighten webhook behavior for live convergence**

Update webhook handling as needed for:
- deterministic metadata correlation
- explicit logging of customer/subscription/event IDs
- robust handling of `created` + `updated` sequencing

- [ ] **Step 4: Re-run checkout lifecycle tests**

Run: `cd backend && .venv/bin/pytest backend/tests/integration/stripe/test_checkout_lifecycle.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/integration/stripe/test_checkout_lifecycle.py backend/src/api/endpoints/stripe.py
git commit -m "test: cover live stripe checkout lifecycle"
```

### Task 4: Cover state transitions for cancellation, reactivation and plan change

**Files:**
- Create: `backend/tests/integration/stripe/test_subscription_state_transitions.py`
- Modify: `backend/src/api/endpoints/stripe.py`

- [ ] **Step 1: Write failing live transition tests**

Cover:
- immediate cancellation
- cancel at period end
- reactivation before period end
- price swap inside paid subscription
- duplicate webhook delivery

- [ ] **Step 2: Run the transition suite and confirm failure**

Run: `cd backend && .venv/bin/pytest backend/tests/integration/stripe/test_subscription_state_transitions.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement missing backend behavior**

Adjust webhook logic only if tests reveal gaps in:
- `canceled`
- `trialing`
- `active`
- `past_due`
- `unpaid`
- duplicate events / out-of-order updates

- [ ] **Step 4: Re-run transition suite**

Run: `cd backend && .venv/bin/pytest backend/tests/integration/stripe/test_subscription_state_transitions.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/integration/stripe/test_subscription_state_transitions.py backend/src/api/endpoints/stripe.py
git commit -m "test: cover live stripe subscription transitions"
```

### Task 5: Cover billing cycle reset and entitlement loss

**Files:**
- Create: `backend/tests/integration/stripe/test_billing_cycle_resets.py`
- Create: `backend/tests/integration/stripe/test_webhook_idempotency_live.py`

- [ ] **Step 1: Write failing live billing tests**

Cover:
- cycle rollover resets `messages_sent_this_month`
- cycle rollover resets `photos_sent_this_month`
- `past_due` / `unpaid` removes entitlements
- trainer resets to `gymbro`
- blocked capabilities are enforced after downgrade

- [ ] **Step 2: Run the billing suite and confirm failure**

Run:
- `cd backend && .venv/bin/pytest backend/tests/integration/stripe/test_billing_cycle_resets.py -v`
- `cd backend && .venv/bin/pytest backend/tests/integration/stripe/test_webhook_idempotency_live.py -v`

Expected: FAIL.

- [ ] **Step 3: Implement missing observability and assertion hooks**

Add only the minimum support required for deterministic verification:
- better log correlation
- helper endpoints or repository reads if absolutely needed for test observation

- [ ] **Step 4: Re-run the billing suite**

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/integration/stripe/test_billing_cycle_resets.py backend/tests/integration/stripe/test_webhook_idempotency_live.py
git commit -m "test: cover live stripe billing resets and idempotency"
```

### Task 6: Add Playwright Stripe end-to-end coverage

**Files:**
- Create: `frontend/e2e/stripe/fixtures/stripeTestHarness.ts`
- Create: `frontend/e2e/stripe/checkout-return.spec.ts`
- Create: `frontend/e2e/stripe/cancellation-and-locks.spec.ts`
- Modify: `frontend/e2e/15-subscription.spec.ts`

- [ ] **Step 1: Write failing e2e scenarios**

Cover:
- user starts checkout from app and returns with active Pro
- user cancels subscription and UI reflects locked features
- subscription state in settings/chat/integrations updates without manual admin intervention

- [ ] **Step 2: Run e2e Stripe specs and confirm failure**

Run: `make e2e`
Expected: FAIL in the new Stripe flows before harness integration is complete.

- [ ] **Step 3: Implement shared Playwright harness**

Create a TS harness that:
- provisions or locates test users
- coordinates with backend fixtures
- waits for profile convergence after Stripe actions

- [ ] **Step 4: Keep e2e suite intentionally small**

Retain only the critical UI journeys here. Do not duplicate all backend integration matrix in Playwright.

- [ ] **Step 5: Re-run e2e**

Run: `make e2e`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/e2e/stripe/fixtures/stripeTestHarness.ts frontend/e2e/stripe/checkout-return.spec.ts frontend/e2e/stripe/cancellation-and-locks.spec.ts frontend/e2e/15-subscription.spec.ts
git commit -m "test: add stripe end-to-end subscription coverage"
```

### Task 7: Wire CI execution model for fast and full Stripe suites

**Files:**
- Create: `.github/workflows/stripe-live-tests.yml` or equivalent CI config
- Create: `scripts/test/run-stripe-live.sh`
- Create: `scripts/test/run-stripe-playwright.sh`
- Modify: `README.md`

- [ ] **Step 1: Write failing CI documentation/tests if repo supports them**

Document the intended split:
- fast PR smoke
- full nightly/release billing suite

- [ ] **Step 2: Implement runner scripts**

`run-stripe-live.sh` should:
- validate secrets
- boot forwarding
- run backend live Stripe suites
- clean up forwarding and temp files

`run-stripe-playwright.sh` should:
- validate secrets
- boot full stack
- run only Stripe Playwright specs

- [ ] **Step 3: Add CI workflow**

Configure:
- opt-in or scheduled full live Stripe suite
- artifact upload for logs/reports
- clear failure output for missing secrets

- [ ] **Step 4: Validate local gates**

Run:
- `cd backend && .venv/bin/ruff check src tests`
- `cd backend && .venv/bin/pylint src`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`

- [ ] **Step 5: Run official full path where possible**

Run:
- `make test-once`

If the repo’s current worktree cannot support it due to missing compose helper files or environment mismatch, document the exact blocker and run the closest supported containerized subset.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/stripe-live-tests.yml scripts/test/run-stripe-live.sh scripts/test/run-stripe-playwright.sh README.md
git commit -m "ci: add live stripe billing test pipeline"
```

## Coverage Map

By the end of this plan, the suite must automate:

- subscription creation
- checkout completion
- customer persistence
- active subscription entitlement
- price change
- cancel now
- cancel at period end
- reactivation
- payment failure
- `past_due`
- `unpaid` or nearest supported Stripe test-mode equivalent
- cycle reset for messages
- cycle reset for photos
- downgrade locks
- trainer fallback
- webhook duplication
- webhook ordering resilience

## Final Verification

- `cd backend && .venv/bin/ruff check src tests`
- `cd backend && .venv/bin/pylint src`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `make e2e`
- `make test-once`

Expected:

- lint and type gates pass
- backend integration Stripe suites pass
- Stripe-focused Playwright passes
- full system path remains green
