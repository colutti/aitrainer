# Free Subscription Overhaul Implementation Plan

> Execution workflow: use `.agent/workflows/executing-plans.md` to implement this plan in batches.

**Goal:** Modify the Free subscription plan to allow 20 messages per day for 7 days, locked to the 'gymbro' trainer (Breno), with a clear paywall/upgrade CTA when limits are reached, supporting admin custom limits.

**Architecture:** We will update the `SubscriptionPlan` definitions in the backend to include `daily_limit`, `validity_days`, and `allowed_trainers`. The `AITrainerBrain` will enforce these limits during chat interactions, returning specific HTTP 403 errors (`TRIAL_EXPIRED`, `DAILY_LIMIT_REACHED`). The frontend will handle these errors by replacing the chat input with an upgrade CTA and will restrict trainer selection in the settings page. Admin custom limits will override plan defaults.

**Tech Stack:** FastAPI, Pydantic, React, Zustand, TailwindCSS

---

### Task 1: Update Subscription Core Models & Frontend Types

**Files:**
- Modify: `backend/src/core/subscription.py`
- Modify: `backend/src/api/models/user_profile.py`
- Modify: `frontend/src/shared/types/user-profile.ts`
- Test: `backend/tests/test_subscription_limits.py`
- Test: `backend/tests/api/models/test_user_profile.py`

**Step 1: Write the failing tests**

Update/Create tests in `backend/tests/test_subscription_limits.py` to check for the new fields (`daily_limit`, `validity_days`, `allowed_trainers`) in `SUBSCRIPTION_PLANS`. Test `UserProfile` initialization with new fields in `test_user_profile.py`.

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_subscription_limits.py backend/tests/api/models/test_user_profile.py -v`
Expected: FAIL due to missing fields/attributes.

**Step 3: Write minimal implementation**

Modify `backend/src/core/subscription.py`:
- In `PlanDetails`, add:
  - `daily_limit: int | None`
  - `validity_days: int | None`
  - `allowed_trainers: list[str] | None`
- Update `SUBSCRIPTION_PLANS`:
  - `FREE`: `daily_limit=20`, `validity_days=7`, `allowed_trainers=["gymbro"]`, change `total_limit` to `None`.
  - Others: add these fields as `None`.

Modify `backend/src/api/models/user_profile.py`:
- In `UserProfile` class, add:
  - `messages_sent_today: int = Field(default=0, description="Messages sent today")`
  - `last_message_date: str | None = Field(default=None, description="ISO Date of last message sent")`

Modify `frontend/src/shared/types/user-profile.ts`:
- Add `messages_sent_today?: number;` and `last_message_date?: string;` to the interface.

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_subscription_limits.py backend/tests/api/models/test_user_profile.py -v`
Expected: PASS

**Step 5: Run quality checks**
Run: `cd backend && ruff check .`
Expected: PASS with 0 errors.

**Step 6: Commit**
```bash
git add backend/src/core/subscription.py backend/src/api/models/user_profile.py frontend/src/shared/types/user-profile.ts
git commit -m "feat: add daily limits and validity to subscription models and frontend types"
```

---

### Task 2: Implement Limits Logic and Expose Limits to Frontend

**Files:**
- Modify: `backend/src/services/trainer.py`
- Modify: `backend/src/api/endpoints/user.py`
- Modify: `backend/src/api/models/user_profile.py`
- Test: `backend/tests/unit/services/test_trainer.py`

**Step 1: Write the failing tests**

Write tests checking that `AITrainerBrain._check_message_limits`:
1. Blocks if plan is Free and 7 days have passed since `current_billing_cycle_start` (returns 403 `TRIAL_EXPIRED`).
2. Resets `messages_sent_today` if `last_message_date` is less than today.
3. Blocks if `messages_sent_today` >= `daily_limit` (returns 403 `DAILY_LIMIT_REACHED`).
4. Allows overriding with `custom_message_limit`.
5. Check `_increment_counts` updates `messages_sent_today` and `last_message_date`.

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/unit/services/test_trainer.py -k "test_check_message_limits" -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Modify `backend/src/services/trainer.py`:
- Update `_check_message_limits` to incorporate `daily_limit` and `validity_days` logic.
- Update `_increment_counts` to increment daily counters and update `last_message_date`.

Modify `backend/src/api/endpoints/user.py`:
- Update `get_profile` to include current plan limits in the response (e.g., by adding a computed field or just returning them). 
- *Alternatively*, update `UserProfile` in `backend/src/api/models/user_profile.py` to add a `@property` or method that returns current limits based on the plan name.

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/unit/services/test_trainer.py -k "test_check_message_limits" -v`
Expected: PASS

**Step 5: Run quality checks**
Run: `cd backend && ruff check .`
Expected: PASS

**Step 6: Commit**
```bash
git add backend/src/services/trainer.py backend/src/api/endpoints/user.py backend/src/api/models/user_profile.py
git commit -m "feat: implement daily limits logic and expose usage to frontend"
```

---

### Task 3: Update Chat UI for Limits and Paywall

**Files:**
- Modify: `frontend/src/features/chat/ChatPage.tsx`
- Modify: `frontend/src/shared/hooks/useChat.ts`
- Modify: `frontend/src/locales/pt-BR.json`
- Test: `frontend/src/features/chat/ChatPage.test.tsx`

**Step 1: Write the failing tests**

Add tests in `ChatPage.test.tsx` to verify:
1. When `error` is `"TRIAL_EXPIRED"` or `"DAILY_LIMIT_REACHED"`, the text area is hidden.
2. A Call to Action (CTA) block is rendered instead, prompting upgrade.
3. A small counter (e.g. "X mensagens restantes hoje") is shown if limits are known (Optional, but good if we expose it. If not exposed easily, we just handle the error state).

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test ChatPage.test`
Expected: FAIL

**Step 3: Write minimal implementation**

Modify `frontend/src/locales/pt-BR.json`:
- Add keys under `chat`: `trial_expired_title`, `trial_expired_desc`, `daily_limit_title`, `daily_limit_desc`, `upgrade_button`.

Modify `frontend/src/shared/hooks/useChat.ts`:
- Ensure error handling catches 403 APIs and sets specific error states for these details to be read by the UI.

Modify `frontend/src/features/chat/ChatPage.tsx`:
- Detect these specific error strings.
- Render a fallback block in place of the `<form>` input area.
- Add `<Button>` linking to `/settings/plans` (or a paywall modal).

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test ChatPage.test`
Expected: PASS

**Step 5: Run quality checks**
Run: `cd frontend && npm run check`
Expected: PASS

**Step 6: Commit**
```bash
git add frontend/
git commit -m "feat(frontend): display paywall and hide chat input on limits reached"
```

---

### Task 4: Restrict Trainer Selection to "Gymbro" for Free Plan

**Files:**
- Modify: `frontend/src/features/settings/components/TrainerSettingsPage.tsx`
- Test: `frontend/src/features/settings/components/TrainerSettingsPage.test.tsx`

**Step 1: Write the failing tests**

Write tests to verify that if the user's plan is 'Free', non-'gymbro' trainers appear locked/disabled and clicking them shows an upgrade prompt or prevents selection.

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test TrainerSettingsPage.test`
Expected: FAIL

**Step 3: Write minimal implementation**

Modify `frontend/src/features/settings/components/TrainerSettingsPage.tsx`:
- Get `userInfo` from `useAuthStore()` to check `subscription_plan`.
- Check if `plan === 'Free' || plan === 'Gratuito'`.
- If true, for `t_data.trainer_id !== 'gymbro'`, apply a visual lock (opacity, Lock icon instead of check).
- Prevent `setSelectedTrainerId(t_data.trainer_id)` for locked trainers.
- Show a small tooltip/toast or banner "Upgrade to unlock".

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test TrainerSettingsPage.test`
Expected: PASS

**Step 5: Run quality checks**
Run: `cd frontend && npm run check`
Expected: PASS

**Step 6: Commit**
```bash
git add frontend/
git commit -m "feat(frontend): restrict free tier to gymbro trainer only"
```

---

### Task 5: Marketing and Landing Page Copy Updates

**Files:**
- Modify: `frontend/src/locales/pt-BR.json`
- Test: N/A (Copy updates)

**Step 1: Write minimal implementation**

Modify `frontend/src/locales/pt-BR.json`:
- Update `landing.hero.trial_desc` to `"Comece com 20 mensagens diárias por 7 dias. Sem compromisso."`
- Update `landing.cta.trial` and related strings to reflect the 7-day, 20-msg/day trial.
- Update `landing.plans.items.free.features` to denote `"20 mensagens/dia por 7 dias"` and `"Treinador Breno (Gymbro)"`.

**Step 2: Run quality checks**
Run: `cd frontend && npm run check`

**Step 3: Commit**
```bash
git add frontend/src/locales/pt-BR.json
git commit -m "chore(frontend): update marketing copy for new free tier logic"
```
