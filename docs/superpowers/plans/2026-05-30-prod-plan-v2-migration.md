# Prod Plan V2 Migration Plan

**Goal:** migrate existing production `plans` documents from the legacy singleton schema to the current `plan_v2` contract before deploying the current backend/frontend.

**Current state verified on 2026-05-30:**
- Production `plans` count: `2`
- Production `plan_v2` count: `0`
- Production discovery drafts: `0`
- Affected users found in prod: `rafacolucci@gmail.com`, `deacandia@gmail.com`
- Local sample plan for `rafacolucci@gmail.com` already validates as `plan_v2`
- Existing repo sync script found: `backend/scripts/sync_user_data.py`

## Why migration is mandatory

The current code no longer treats the legacy plan document as a valid active plan:

- `backend/src/api/models/plan.py` now requires `schema_version="plan_v2"` plus `user_context`, `training`, `nutrition`, `alignment`, and `tracking`.
- `backend/src/repositories/plan_repository.py` returns `None` when a stored plan fails `UserPlan(**doc)` validation.
- `backend/src/services/trainer.py` builds prompt context from `db.get_plan(...)`; invalid legacy docs are treated as if no plan exists.
- `frontend/src/shared/hooks/usePlan.ts` now reads `/plan/view`, which is built from the validated `UserPlan`. Legacy docs therefore surface as `NO_PLAN` / discovery state instead of a real plan.

Deploying the current app without migrating prod data will make existing plan users lose plan context in both chat and UI.

## Legacy to V2 mapping

Map each legacy document into one `UserPlan` V2 document:

- Top level:
  - `user_email` -> `user_email`
  - `title` -> `title`
  - `created_at` -> `created_at`
  - `updated_at` -> `updated_at`
  - `change_reason` -> `review_reason`
  - set `schema_version = "plan_v2"`
  - set `plan_status = "active"`
  - set `created_from = "migration"`
  - set `data_confidence = "medium"`
  - set `last_material_change_at = updated_at`
  - set `review_history = []` unless migrated from checkpoints

- `goal`:
  - `primary` -> `primary_goal`
  - `objective_summary` -> `outcome_summary`
  - `success_criteria[]` -> `success_metrics[]` using string-to-metric wrapping:
    - `metric_name = original string`
    - `target_value = "ver descrição"`
    - `unit = "qualitative"`
    - `direction = "complete"`
  - If `metric_targets.weekly_weight_change_kg` exists, append a structured metric:
    - `metric_name = "weekly_weight_change_kg"`
    - `target_value = abs(value)`
    - `unit = "kg/week"`
    - `direction = "increase"` when legacy `primary == "build_muscle"`, otherwise `direction = "decrease"` for `lose_fat`, else `maintain`
  - If `metric_targets.target_weight_kg` exists, append:
    - `metric_name = "target_weight"`
    - `target_value = value`
    - `unit = "kg"`
    - direction derived from legacy goal

- `timeline`:
  - `start_date` datetime -> `start_date` date
  - `target_date` datetime -> `target_date` date
  - `review_cadence` text -> `review_cadence_days`
  - `current_phase`:
    - use `current_summary.active_focus` when present
    - fallback to `"Plano migrado do schema legado"`
  - cadence conversion:
    - `semanal` / `weekly` -> `7`
    - `quinzenal` / `biweekly` -> `15`
    - `mensal` / `monthly` -> `30`
    - unknown text -> `14` and log a migration warning

- `user_context`:
  - `training_days_available` = distinct weekdays from migrated `weekly_schedule` where final type is `training`
  - `session_duration_min` = `training_program.session_duration_min`
  - `constraints` = `strategy.constraints`
  - `preferences` = `strategy.preferences`
  - `available_equipment` = `["unknown"]`
  - `training_level` = `"unknown"`
  - `nutrition_preferences` = `nutrition_strategy.adherence_notes`

- `training`:
  - `split_name` -> `split_name`
  - `frequency_per_week` -> recompute from final training rows, do not trust legacy value
  - `session_duration_min` -> `session_duration_min`
  - `routines`:
    - `id` -> `id`
    - `name` -> `name`
    - `objective` -> `objective`
    - legacy exercises -> V2 exercises:
      - `name` -> `name`
      - `sets` -> `sets`
      - `reps` string/number/list -> `rep_range`
      - `load_guidance` -> `intensity = {prescription_type: "guidance", target: load_guidance or "RPE 7-8"}`
      - `rest_seconds` -> `rest_seconds`
      - `notes` -> `notes`
      - `progression_rule = {method: "double_progression", increase_when: "Complete the top of the rep range with solid form", hold_when: "Still building consistency in the prescribed range", deload_when: "Form regresses or fatigue accumulates for multiple sessions"}`
      - `external_exercise_template_id = null`
    - `external_bindings = []`

- `nutrition`:
  - `daily_targets.calories` -> `daily_targets.calories_kcal`
  - `protein_g`, `carbs_g`, `fat_g`, `fiber_g` -> same names
  - `strategy` = join `nutrition_strategy.adherence_notes` into one sentence; fallback `"Plano nutricional migrado do schema legado."`
  - `adherence_target_pct = 85` by default

- `alignment`:
  - `training_nutrition_rationale` = `strategy.rationale`
  - `energy_strategy`:
    - `build_muscle` -> `surplus`
    - `lose_fat` -> `deficit`
    - `recomposition` -> `recomposition`
    - `performance` / unknown -> `maintenance`
  - `recovery_assumptions` = `strategy.current_risks`
  - `conflict_rules`:
    - if legacy risks exist, convert each risk string into `{trigger: risk, action: "Revisar o plano e ajustar volume, calorias ou recuperação."}`
    - if no risks exist, insert one default rule:
      - `trigger = "Dados de progresso ou adesão indicam desalinhamento com o objetivo"`
      - `action = "Revisar treino, nutrição e recuperação antes de manter o plano."`

- `tracking`:
  - `workout_adherence_target_pct = 80`
  - `nutrition_adherence_target_pct = 80`
  - `progress_markers`:
    - one marker from goal summary
    - one marker from training adherence
    - one marker from nutrition targets
  - `review_questions`:
    - migrate from checkpoint/current-summary language when possible
    - otherwise use:
      - `"Conseguiu seguir os treinos planejados?"`
      - `"Conseguiu seguir as metas nutricionais?"`
      - `"Os dados recentes mostram progresso na direção do objetivo?"`

- `latest_review` / `review_history`:
  - if legacy `checkpoints` exists:
    - newest checkpoint -> `latest_review`
    - all checkpoints -> `review_history`
    - `summary = checkpoint.summary`
    - `decision = checkpoint.decision`
    - `changes_made = []`
    - `next_review_at = date(current_summary.next_review)` when parseable
    - `evidence_summary = checkpoint.evidence`
  - if no checkpoints exist and `current_summary.last_review` exists:
    - create one synthetic `latest_review`
  - else keep `latest_review = null`, `review_history = []`

## Required normalization rules before save

These are mandatory because the current V2 schema is stricter than the legacy one:

- Convert all legacy datetimes to date-only for `timeline.start_date` and `timeline.target_date`.
- Deduplicate `weekly_schedule` to a single row per weekday.
- When the same weekday has both `off` and `training`, keep `training` and drop `off`.
- Keep weekday values canonical: `monday..sunday`.
- Recompute `frequency_per_week` from the final migrated schedule.
- Parse legacy reps into `RepRange`:
  - `"8-12"` -> `{min_reps: 8, max_reps: 12}`
  - `"12"` -> `{min_reps: 12, max_reps: 12}`
  - `"8/10/12"` -> `{min_reps: 8, max_reps: 12}`
  - unparseable values -> reject dry-run and require manual patch for that user
- Ensure every training schedule row points to an existing migrated routine id.
- Ensure every `off` row has `routine_id = null`.

## Prod-specific anomalies already observed

- `rafacolucci@gmail.com` has contradictory legacy schedule rows for `wednesday` and `thursday`:
  - one `off` row and one `training` row on the same day
  - migration rule must collapse these to a single `training` row
- `rafacolucci@gmail.com` has a mixed historical schedule that likely reflects partial plan rewrites; frequency must be recomputed from the deduplicated schedule, not copied verbatim.
- Both prod plans use the legacy top-level shape only; there is no mixed `legacy + v2` document in prod today.

## Local precondition

Before any local validation or migration rehearsal:

1. Start the local environment with `make debug-rebuild`.
2. Use the runtime that shares the same Mongo instance as the app.
3. Treat the host-side DB as non-authoritative if it diverges from the backend container runtime.

## Execution plan

1. Add a one-off migration script under `backend/scripts/`.
   - Read all `plans`.
   - Detect legacy vs already-migrated documents.
   - Transform legacy docs into `UserPlan` V2 objects.
   - Validate each transformed document with the current `UserPlan` model.
   - Produce a dry-run report per user with original keys, migrated keys, schedule normalization actions, and validation result.

2. Replace the local dev data for `rafacolucci@gmail.com` with the full production dataset.
   - Use the existing sync path in `backend/scripts/sync_user_data.py` instead of inventing a second importer.
   - Load production credentials from `backend/.env.prod`.
   - Run the sync in the backend runtime connected to the same local Mongo used by the app.
   - Replace the local test data for the user across all supported collections, not only `plans`.
   - This local overwrite is allowed because the local dataset is disposable.

3. Validate the imported prod data locally before any migration rehearsal.
   - Confirm the full local user import completed for the collections covered by the sync script.
   - Inspect the local app and API with the imported prod data.
   - If the imported local data is wrong or incomplete, fix the sync/import path first.

4. Run the plan migration script locally against the imported prod copy of `rafacolucci@gmail.com`.
   - Expected result for current prod: the local copy of `rafacolucci@gmail.com` migrates successfully into a valid `plan_v2`.
   - If validation fails, stop and patch the transformer before any prod write.

5. Human approval gate in local.
   - Start the local stack with the migrated local plan.
   - First validate that the imported prod data itself looks correct locally.
   - Then open the migrated plan UI and inspect the resulting plan as `rafacolucci@gmail.com`.
   - The user must explicitly confirm both:
     - the imported prod data looks correct locally
     - the migrated local plan looks correct
   - Prod migration is blocked until that explicit approval exists.

6. Run dry-run for the remaining prod documents in read-only mode.
   - Validate all legacy prod plans through the same transformer without writing.
   - If any user fails validation, stop and patch the transformer or define a user-specific correction rule before any prod write.

7. Add backup mode to the script.
   - Before writing, dump each original prod document into a timestamped JSON artifact outside the collection.
   - Include `_id`, `user_email`, and the full pre-migration payload.

8. Run write mode in prod only after the explicit local approval.
   - Replace only the `plans` documents for users that validated in dry-run.
   - Preserve `_id` when practical; if using repository upsert semantics, confirm post-write there is exactly one `plans` row per `user_email`.
   - Do not create `plan_discovery_states` for these users.

9. Post-write verification in prod.
   - Re-read each migrated plan and validate it through the current `UserPlan` model.
   - Confirm `db.get_plan(user_email)` would no longer return `None`.
   - Confirm `/plan/view` would return `status = "ACTIVE_PLAN"`.
   - Confirm prompt snapshot generation no longer falls back to `NO_PLAN` / `DISCOVERY_IN_PROGRESS`.

10. Only after migration verification, deploy the current backend/frontend.

## Verification checklist

- DB:
  - `plans_total` unchanged
  - `schema_version = "plan_v2"` for all migrated users
  - zero legacy-only plan documents remain

- Backend behavior:
  - current `UserPlan(**doc)` succeeds for each migrated plan
  - `PlanRepository.get_plan()` returns a model for each migrated user
  - prompt context status is `ACTIVE_PLAN`

- Frontend behavior:
  - `/plan/view` returns `active_plan`, not discovery
  - weekly schedule renders without duplicated weekdays

- Chat behavior:
  - the assistant sees the migrated plan in prompt context and does not restart discovery for existing users

## Rollback

- Rollback is data-only:
  - restore each user’s original backup document into `plans`
  - remove the migrated replacement
- Do not deploy current app code before either:
  - successful migration, or
  - temporary backward-compat read support for the legacy schema

## Recommendation

The lowest-risk path is:

1. implement the migration script,
2. start local with `make debug-rebuild`,
3. sync the full prod dataset for `rafacolucci@gmail.com` into local,
4. validate locally that the imported prod data itself looks correct,
5. migrate that local copy,
6. get explicit human approval from you in local,
7. dry-run all prod documents,
8. back up both prod documents,
9. write migrated plans in prod,
10. verify read path and `/plan/view`,
11. deploy the current app.

Do not publish the current code to prod before step 10 is complete.
