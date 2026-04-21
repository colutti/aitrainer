# Plano Central Implementation Plan

> Execution workflow: use `.agent/workflows/executing-plans.md` to implement this plan in batches.

**Goal:** Build `plan` as the main coaching entity, inject the active plan snapshot into every AI conversation, and ship a first premium plan hub with proposal/approval/adjustment states.

**Architecture:** Add a dedicated `plan` domain to the backend with versioned active-plan persistence, prompt snapshot generation, and AI-only write tools. Expose a focused `/plan` API for the frontend, then add a new `plan` feature in the React app that becomes the operational home for the user with `Mission First` hierarchy.

**Tech Stack:** FastAPI, Pydantic, MongoDB repositories, LangChain tools/prompt builder, React 19, TypeScript, Zustand, TailwindCSS v4, Vitest, Pytest.

---

## Implementation Notes

- Follow TDD for each backend and frontend slice.
- Keep `user_profile` unchanged as the identity/config object. Do not move unrelated profile fields into the new domain.
- Start with one active plan per user and version history; do not add admin editing or multi-plan support.
- Treat approval as a persisted state transition, not a chat convention.
- Any new user-facing copy must be translated in:
  - `frontend/src/locales/pt-BR.json`
  - `frontend/src/locales/en-US.json`
  - `frontend/src/locales/es-ES.json`

## Verification Environment

- Backend lint: `cd backend && .venv/bin/ruff check src tests`
- Backend pylint: `cd backend && .venv/bin/pylint src`
- Backend typing when needed: `cd backend && .venv/bin/pyright src`
- Backend tests: `cd backend && .venv/bin/pytest`
- Frontend lint: `cd frontend && npm run lint`
- Frontend typecheck: `cd frontend && npm run typecheck`
- Frontend tests: `cd frontend && npm test`
- Full repo verification after integration: `make verify`

## Task 1: Define Backend Plan Models

**Files:**
- Create: `backend/src/api/models/plan.py`
- Modify: `backend/src/api/models/__init__.py`
- Test: `backend/tests/api/models/test_plan_models.py`

**Step 1: Write the failing model tests**

Create `backend/tests/api/models/test_plan_models.py` covering:

```python
from datetime import datetime

from src.api.models.plan import (
    PlanStatus,
    PlanSnapshot,
    PlanProposalInput,
    ActivePlan,
)


def test_plan_status_allows_only_supported_values():
    assert PlanStatus.ACTIVE == "active"
    assert PlanStatus.AWAITING_APPROVAL == "awaiting_approval"


def test_active_plan_requires_identity_strategy_and_execution_blocks():
    plan = ActivePlan(
        id="plan_1",
        user_email="user@test.com",
        status=PlanStatus.ACTIVE,
        title="Plano Cutting",
        objective_summary="Perder gordura mantendo performance",
        start_date=datetime(2026, 4, 19),
        end_date=datetime(2026, 6, 7),
        version=2,
        strategy={
            "primary_goal": "lose_fat",
            "success_criteria": ["peso medio em queda"],
            "constraints": ["rotina corrida"],
            "coaching_rationale": "deficit moderado",
            "adaptation_policy": "pedir aprovacao para mudancas materiais",
        },
        execution={
            "today_training": {"title": "Upper A", "status": "planned"},
            "today_nutrition": {"calories": 2200, "protein_target": 180},
            "upcoming_days": [],
            "active_focus": "constancia",
            "current_risks": [],
            "pending_changes": [],
        },
        tracking={
            "checkpoints": [],
            "adherence_snapshot": {"training": "unknown", "nutrition": "unknown"},
            "progress_snapshot": {"status": "insufficient_data"},
            "last_ai_assessment": None,
            "last_user_acknowledgement": None,
        },
        governance={"change_reason": None, "approval_request": None},
    )
    assert plan.version == 2


def test_plan_snapshot_stays_prompt_safe_and_compact():
    snapshot = PlanSnapshot(
        title="Plano Atual",
        objective_summary="Ganhar massa com minimo ganho de gordura",
        status="active",
        active_focus="progressao de carga",
        today_training="Push com 6 exercicios",
        today_nutrition="3000 kcal / 180g proteina",
        upcoming_days=["Pull", "Legs"],
        last_checkpoint_summary="aderencia boa",
        critical_constraints=["viagem quinta"],
        pending_adjustment=None,
    )
    assert "Push" in snapshot.today_training


def test_plan_proposal_input_requires_material_change_reason():
    payload = PlanProposalInput(
        title="Novo Plano",
        objective_summary="Reorganizar por queda de aderencia",
        change_reason="baixa_aderencia",
        strategy={},
        execution={},
        tracking={},
    )
    assert payload.change_reason == "baixa_aderencia"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/api/models/test_plan_models.py -v`

Expected: FAIL because `src.api.models.plan` does not exist yet.

**Step 3: Write minimal implementation**

Create `backend/src/api/models/plan.py` with:

- `PlanStatus` as `str, Enum`
- nested Pydantic models for:
  - `PlanStrategy`
  - `PlanExecution`
  - `PlanTracking`
  - `PlanGovernance`
  - `CheckpointRecord`
  - `PlanApprovalRequest`
  - `PlanSnapshot`
  - `PlanProposalInput`
  - `ActivePlan`
  - `ActivePlanWithId` if repository responses need `_id` mapping
- validation rules:
  - explicit `start_date`, `end_date`
  - `version >= 1`
  - non-empty `title` and `objective_summary`
  - snapshot fields intentionally compact and string/list oriented

Update `backend/src/api/models/__init__.py` to export the new plan models if the module already acts as a shared import surface.

**Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/api/models/test_plan_models.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/api/models/plan.py backend/src/api/models/__init__.py backend/tests/api/models/test_plan_models.py
git commit -m "feat(plan): add plan domain models"
```

## Task 2: Add Plan Repository and Database Delegation

**Files:**
- Create: `backend/src/repositories/plan_repository.py`
- Modify: `backend/src/services/database.py`
- Test: `backend/tests/test_plan_repository.py`

**Step 1: Write the failing repository tests**

Create `backend/tests/test_plan_repository.py` with cases for:

```python
from datetime import datetime

from src.api.models.plan import ActivePlan, PlanStatus
from src.repositories.plan_repository import PlanRepository


def make_plan(version=1, status=PlanStatus.ACTIVE):
    return ActivePlan(
        id=f"plan_{version}",
        user_email="user@test.com",
        status=status,
        title="Plano Atual",
        objective_summary="Ganhar massa",
        start_date=datetime(2026, 4, 19),
        end_date=datetime(2026, 6, 19),
        version=version,
        strategy={
            "primary_goal": "gain_muscle",
            "success_criteria": ["mais volume"],
            "constraints": [],
            "coaching_rationale": "superavit leve",
            "adaptation_policy": "approval_required",
        },
        execution={
            "today_training": {"title": "Push"},
            "today_nutrition": {"calories": 3000},
            "upcoming_days": [],
            "active_focus": "consistencia",
            "current_risks": [],
            "pending_changes": [],
        },
        tracking={
            "checkpoints": [],
            "adherence_snapshot": {"training": "unknown", "nutrition": "unknown"},
            "progress_snapshot": {"status": "unknown"},
            "last_ai_assessment": None,
            "last_user_acknowledgement": None,
        },
        governance={"change_reason": None, "approval_request": None},
    )


def test_save_active_plan_upserts_current_version(mongo_database):
    repo = PlanRepository(mongo_database.database)
    plan = make_plan()
    plan_id = repo.save_plan(plan)
    assert plan_id
    loaded = repo.get_active_plan("user@test.com")
    assert loaded is not None
    assert loaded.version == 1


def test_approve_plan_replaces_previous_active_version(mongo_database):
    repo = PlanRepository(mongo_database.database)
    repo.save_plan(make_plan(version=1, status=PlanStatus.ACTIVE))
    repo.save_plan(make_plan(version=2, status=PlanStatus.AWAITING_APPROVAL))
    repo.approve_plan("user@test.com", version=2)
    active = repo.get_active_plan("user@test.com")
    assert active is not None
    assert active.version == 2


def test_list_plan_versions_returns_latest_first(mongo_database):
    repo = PlanRepository(mongo_database.database)
    repo.save_plan(make_plan(version=1))
    repo.save_plan(make_plan(version=2, status=PlanStatus.AWAITING_APPROVAL))
    versions = repo.list_plan_versions("user@test.com")
    assert versions[0].version == 2
```

**Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/test_plan_repository.py -v`

Expected: FAIL because `PlanRepository` is missing.

**Step 3: Write minimal implementation**

Create `backend/src/repositories/plan_repository.py`:

- inherit from `BaseRepository`
- use collection name `plans`
- implement:
  - `save_plan(plan: ActivePlan) -> str`
  - `get_active_plan(user_email: str) -> ActivePlan | None`
  - `get_latest_plan(user_email: str) -> ActivePlan | None`
  - `list_plan_versions(user_email: str) -> list[ActivePlan]`
  - `approve_plan(user_email: str, version: int) -> bool`
  - `archive_active_plan(user_email: str) -> bool`
- ensure indexes:
  - `user_email`
  - `(user_email, version)` unique
  - partial index for active/latest fetches if helpful
- keep repository rules explicit:
  - only one `active`
  - approval transitions `awaiting_approval -> active`
  - old active version becomes `archived`

Modify `backend/src/services/database.py` to:

- initialize `self.plans = PlanRepository(self.database)`
- add delegating methods:
  - `save_plan`
  - `get_active_plan`
  - `get_latest_plan`
  - `list_plan_versions`
  - `approve_plan`

**Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/test_plan_repository.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/repositories/plan_repository.py backend/src/services/database.py backend/tests/test_plan_repository.py
git commit -m "feat(plan): add repository and database delegation"
```

## Task 3: Build Prompt Snapshot Generation

**Files:**
- Create: `backend/src/services/plan_service.py`
- Modify: `backend/src/services/prompt_builder.py`
- Test: `backend/tests/test_plan_service.py`
- Test: `backend/tests/test_prompt_builder_plan_snapshot.py`

**Step 1: Write the failing service tests**

Create `backend/tests/test_plan_service.py`:

```python
from datetime import datetime

from src.api.models.plan import ActivePlan, PlanStatus
from src.services.plan_service import build_plan_prompt_snapshot


def test_build_plan_prompt_snapshot_extracts_only_prompt_relevant_fields():
    plan = ActivePlan(
        id="plan_1",
        user_email="user@test.com",
        status=PlanStatus.ACTIVE,
        title="Plano Atual",
        objective_summary="Cutting com foco em aderencia",
        start_date=datetime(2026, 4, 19),
        end_date=datetime(2026, 6, 7),
        version=3,
        strategy={
            "primary_goal": "lose_fat",
            "success_criteria": ["queda do peso medio"],
            "constraints": ["jantar social sexta"],
            "coaching_rationale": "deficit sustentavel",
            "adaptation_policy": "approval_required",
        },
        execution={
            "today_training": {"title": "Lower A"},
            "today_nutrition": {"summary": "2200 kcal / 180p"},
            "upcoming_days": ["Upper B", "Off"],
            "active_focus": "consistencia",
            "current_risks": ["baixa energia"],
            "pending_changes": [],
        },
        tracking={
            "checkpoints": [],
            "adherence_snapshot": {"training": "good", "nutrition": "mixed"},
            "progress_snapshot": {"status": "on_track"},
            "last_ai_assessment": "boa aderencia na semana",
            "last_user_acknowledgement": None,
        },
        governance={"change_reason": None, "approval_request": None},
    )
    snapshot = build_plan_prompt_snapshot(plan)
    assert snapshot.title == "Plano Atual"
    assert snapshot.active_focus == "consistencia"
    assert "2200 kcal" in snapshot.today_nutrition
```

Create `backend/tests/test_prompt_builder_plan_snapshot.py`:

```python
from src.services.prompt_builder import PromptBuilder


def test_build_input_data_includes_plan_snapshot_section():
    input_data = PromptBuilder.build_input_data(
        profile=type("P", (), {"display_name": "Rafa", "timezone": "Europe/Madrid"})(),
        trainer_profile_summary="**Nome:** Atlas",
        user_profile_summary="Resumo",
        formatted_history_msgs=[],
        user_input="Como ajustamos hoje?",
        current_date="2026-04-19",
        agenda_events=[],
        plan_snapshot_text="Plano ativo: foco em consistencia",
    )
    assert input_data["plan_snapshot"] == "Plano ativo: foco em consistencia"
```

**Step 2: Run tests to verify they fail**

Run:

```bash
cd backend && .venv/bin/pytest tests/test_plan_service.py tests/test_prompt_builder_plan_snapshot.py -v
```

Expected: FAIL because the service and prompt support do not exist.

**Step 3: Write minimal implementation**

Create `backend/src/services/plan_service.py` with pure functions:

- `build_plan_prompt_snapshot(plan: ActivePlan | None) -> PlanSnapshot | None`
- `render_plan_snapshot_text(snapshot: PlanSnapshot | None) -> str`
- `get_today_plan_brief(plan: ActivePlan | None) -> dict[str, str]`

Keep rendering compact, for example:

```text
Plano ativo:
- Objetivo: Cutting com foco em aderencia
- Janela: 19/04/2026 -> 07/06/2026
- Foco atual: consistencia
- Treino de hoje: Lower A
- Nutricao de hoje: 2200 kcal / 180p
- Proximos dias: Upper B; Off
- Ultimo checkpoint: boa aderencia na semana
- Restricoes criticas: jantar social sexta
```

Modify `backend/src/services/prompt_builder.py` to:

- accept `plan_snapshot_text: str | None = None` in `build_input_data`
- inject `"plan_snapshot": plan_snapshot_text or ""`
- remove the empty plan block from the prompt if the prompt template contains it and no plan exists

Do not hardcode prompt template text in this step if `settings.PROMPT_TEMPLATE` does not yet contain a plan section; that integration lands in Task 4.

**Step 4: Run tests to verify they pass**

Run:

```bash
cd backend && .venv/bin/pytest tests/test_plan_service.py tests/test_prompt_builder_plan_snapshot.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/services/plan_service.py backend/src/services/prompt_builder.py backend/tests/test_plan_service.py backend/tests/test_prompt_builder_plan_snapshot.py
git commit -m "feat(plan): add prompt snapshot generation"
```

## Task 4: Inject Active Plan Snapshot into AI Chat Flow

**Files:**
- Modify: `backend/src/services/trainer.py`
- Modify: `backend/src/core/config.py` or prompt source file if the template is defined there
- Test: `backend/tests/test_trainer_plan_prompt.py`

**Step 1: Write the failing integration-style tests**

Create `backend/tests/test_trainer_plan_prompt.py` with cases for:

```python
from unittest.mock import MagicMock

from src.services.trainer import AITrainerBrain


def test_trainer_builds_prompt_with_active_plan_snapshot():
    database = MagicMock()
    database.get_active_plan.return_value = MagicMock()
    brain = AITrainerBrain(database=database, llm_client=MagicMock(), qdrant_client=None)

    database.get_user_profile.return_value = MagicMock(
        display_name="Rafa",
        timezone="Europe/Madrid",
        subscription_plan="Pro",
    )
    database.get_trainer_profile.return_value = MagicMock(
        get_profile_summary=lambda: "**Nome:** Atlas"
    )

    # Call the internal method or the smallest public path that assembles prompt input.
    # Assert get_active_plan was requested and plan snapshot text reached prompt builder.
```

Also add a case for `no active plan` to verify the prompt builder receives an empty plan block instead of crashing.

**Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/test_trainer_plan_prompt.py -v`

Expected: FAIL because the trainer flow does not request or pass plan context.

**Step 3: Write minimal implementation**

In `backend/src/services/trainer.py`:

- fetch `active_plan = self._database.get_active_plan(user_email)` before building prompt input
- use `build_plan_prompt_snapshot(active_plan)` and `render_plan_snapshot_text(...)`
- pass `plan_snapshot_text=` into `PromptBuilder.build_input_data(...)`

In the prompt template source:

- add a stable section such as:

```text
## Plano atual do aluno
{plan_snapshot}

```

- ensure `PromptBuilder.get_prompt_template()` removes that block when `plan_snapshot` is empty, similar to the existing agenda handling pattern

Keep this block near the profile/agenda context, not inside chat history.

**Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/test_trainer_plan_prompt.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/services/trainer.py backend/src/core/config.py backend/tests/test_trainer_plan_prompt.py
git commit -m "feat(plan): inject active plan into chat prompt"
```

## Task 5: Add AI Plan Tools and Approval Semantics

**Files:**
- Create: `backend/src/services/plan_tools.py`
- Modify: `backend/src/services/trainer.py`
- Test: `backend/tests/test_plan_tools.py`

**Step 1: Write the failing tool tests**

Create `backend/tests/test_plan_tools.py` with tests for:

```python
from unittest.mock import MagicMock

from src.services.plan_tools import (
    create_get_active_plan_tool,
    create_create_plan_proposal_tool,
    create_propose_plan_adjustment_tool,
    create_approve_plan_change_tool,
)


def test_get_active_plan_tool_returns_human_readable_summary():
    db = MagicMock()
    db.get_active_plan.return_value = MagicMock(title="Plano Atual", version=2)
    tool = create_get_active_plan_tool(db, "user@test.com")
    response = tool.invoke({})
    assert "Plano Atual" in response


def test_create_plan_proposal_tool_saves_awaiting_approval_version():
    db = MagicMock()
    tool = create_create_plan_proposal_tool(db, "user@test.com")
    response = tool.invoke({
        "title": "Plano Inicial",
        "objective_summary": "Recomposicao corporal",
        "change_reason": "initial_plan",
        "strategy": {},
        "execution": {},
        "tracking": {},
    })
    assert "aguarda aprovacao" in response.lower()
    db.save_plan.assert_called_once()


def test_approve_plan_change_tool_promotes_requested_version():
    db = MagicMock()
    db.approve_plan.return_value = True
    tool = create_approve_plan_change_tool(db, "user@test.com")
    response = tool.invoke({"version": 2})
    assert "aprovado" in response.lower()
```

**Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/test_plan_tools.py -v`

Expected: FAIL because `plan_tools.py` does not exist.

**Step 3: Write minimal implementation**

Create `backend/src/services/plan_tools.py` with tools:

- `create_get_active_plan_tool`
- `create_get_plan_prompt_snapshot_tool` if useful for debugging
- `create_create_plan_proposal_tool`
- `create_propose_plan_adjustment_tool`
- `create_approve_plan_change_tool`
- `create_get_today_plan_brief_tool`

Rules:

- proposal writes `awaiting_approval` or `adjustment_pending_approval`
- approval calls repository/database `approve_plan`
- tool responses are human-readable and explicit about persistence
- no tool should silently mutate the active version without an approval state transition

Modify `backend/src/services/trainer.py` to register the new tools in the tool list near profile/goal tools.

Do not remove existing workout/nutrition tools.

**Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/test_plan_tools.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/services/plan_tools.py backend/src/services/trainer.py backend/tests/test_plan_tools.py
git commit -m "feat(plan): add plan tools and approval flow"
```

## Task 6: Expose Plan API Endpoints

**Files:**
- Create: `backend/src/api/endpoints/plan.py`
- Modify: `backend/src/api/main.py`
- Test: `backend/tests/integration/test_plan_endpoints.py`

**Step 1: Write the failing endpoint tests**

Create `backend/tests/integration/test_plan_endpoints.py` with API tests for:

- `GET /plan/active`
- `GET /plan/versions`
- `POST /plan/approve`
- `GET /plan/today`

Example:

```python
def test_get_active_plan_returns_current_active_plan(client, auth_headers, mongo_database):
    # seed active plan
    response = client.get("/plan/active", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "active"


def test_get_active_plan_returns_404_when_user_has_no_plan(client, auth_headers):
    response = client.get("/plan/active", headers=auth_headers)
    assert response.status_code == 404
```

**Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/integration/test_plan_endpoints.py -v`

Expected: FAIL because the endpoint module and routes do not exist.

**Step 3: Write minimal implementation**

Create `backend/src/api/endpoints/plan.py`:

- follow the dependency pattern used in existing endpoint modules
- include:
  - `GET /active`
  - `GET /versions`
  - `GET /today`
  - `POST /approve`
- return Pydantic response models from `plan.py`
- `POST /approve` accepts a small payload such as:

```python
class ApprovePlanRequest(BaseModel):
    version: int
```

Modify `backend/src/api/main.py` to include:

```python
from src.api.endpoints import plan
app.include_router(plan.router, prefix="/plan", tags=["plan"])
```

**Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/integration/test_plan_endpoints.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/api/endpoints/plan.py backend/src/api/main.py backend/tests/integration/test_plan_endpoints.py
git commit -m "feat(plan): add plan api endpoints"
```

## Task 7: Extend Chat Metadata for Plan Approvals

**Files:**
- Modify: `backend/src/api/models/message.py`
- Modify: `backend/src/api/endpoints/message.py`
- Modify: `frontend/src/shared/types/chat.ts`
- Modify: `frontend/src/shared/hooks/useChat.ts`
- Test: `backend/tests/integration/test_plan_chat_signals.py`
- Test: `frontend/src/features/chat/ChatPage.test.tsx`

**Step 1: Write the failing tests**

Add a backend test asserting the message response can include plan action metadata, for example:

```python
assert response.json()["plan_action"]["type"] == "approval_required"
```

Add a frontend test asserting chat state preserves plan action metadata when a message arrives.

**Step 2: Run tests to verify they fail**

Run:

```bash
cd backend && .venv/bin/pytest tests/integration/test_plan_chat_signals.py -v
cd frontend && npm test -- ChatPage.test.tsx
```

Expected: FAIL because chat models do not yet support plan actions.

**Step 3: Write minimal implementation**

Use this task only if the current message streaming shape can safely carry extra metadata. If it cannot, use the existing text-only response and move approval CTA entirely to the plan page.

Preferred implementation:

- add optional `plan_action` metadata to backend message response model
- include fields such as:
  - `type`
  - `version`
  - `title`
  - `status`
- update frontend chat types/store to preserve it

If this slice becomes too invasive, explicitly defer chat CTA rendering and keep the approval action on the plan page for V1. In that case, document the deferral in the final change summary and remove this task from execution.

**Step 4: Run tests to verify they pass**

Run the same commands as Step 2.

Expected: PASS or task intentionally deferred with updated plan note.

**Step 5: Commit**

```bash
git add backend/src/api/models/message.py backend/src/api/endpoints/message.py frontend/src/shared/types/chat.ts frontend/src/shared/hooks/useChat.ts backend/tests/integration/test_plan_chat_signals.py frontend/src/features/chat/ChatPage.test.tsx
git commit -m "feat(plan): surface plan approval metadata in chat"
```

## Task 8: Add Frontend Plan Types and Store

**Files:**
- Create: `frontend/src/shared/types/plan.ts`
- Create: `frontend/src/shared/hooks/usePlan.ts`
- Test: `frontend/src/shared/hooks/usePlan.test.ts`

**Step 1: Write the failing store tests**

Create `frontend/src/shared/hooks/usePlan.test.ts` covering:

```ts
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { usePlanStore } from './usePlan';

vi.mock('../api/http-client', () => ({
  httpClient: vi.fn(),
}));

describe('usePlanStore', () => {
  beforeEach(() => {
    usePlanStore.getState().reset();
  });

  it('fetches active plan into state', async () => {
    // mock GET /plan/active
  });

  it('stores empty state when no active plan exists', async () => {
    // mock 404 handling
  });

  it('approves a pending version and refreshes active plan', async () => {
    // mock POST /plan/approve followed by GET /plan/active
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- src/shared/hooks/usePlan.test.ts`

Expected: FAIL because the plan store does not exist.

**Step 3: Write minimal implementation**

Create `frontend/src/shared/types/plan.ts`:

- `PlanStatus`
- `PlanSummary`
- `PlanTodayBrief`
- `PlanVersion`
- `PlanApprovalAction`

Create `frontend/src/shared/hooks/usePlan.ts`:

- Zustand store with state:
  - `activePlan`
  - `versions`
  - `todayBrief`
  - `isLoading`
  - `error`
- actions:
  - `fetchActivePlan`
  - `fetchVersions`
  - `fetchTodayBrief`
  - `approvePlan`
  - `reset`

Use `httpClient` directly, following `useDashboard.ts`/`useWorkout.ts`.

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- src/shared/hooks/usePlan.test.ts`

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/shared/types/plan.ts frontend/src/shared/hooks/usePlan.ts frontend/src/shared/hooks/usePlan.test.ts
git commit -m "feat(plan): add frontend plan store"
```

## Task 9: Add Plan Route and Navigation Entry

**Files:**
- Create: `frontend/src/features/plan/PlanPage.tsx`
- Modify: `frontend/src/AppRoutes.tsx`
- Modify: `frontend/src/shared/components/layout/PremiumLayout.tsx`
- Test: `frontend/src/AppRoutes.test.tsx`
- Test: `frontend/src/shared/components/layout/PremiumLayout.test.tsx`

**Step 1: Write the failing route/navigation tests**

Add tests for:

- `/dashboard/plan` renders `PlanPage`
- desktop nav contains `Plano`
- mobile nav contains a plan icon/tab

Example:

```tsx
it('renders plan route inside premium layout', async () => {
  render(<AppRoutes />, { route: '/dashboard/plan' });
  expect(await screen.findByText(/plan page/i)).toBeInTheDocument();
});
```

**Step 2: Run tests to verify they fail**

Run:

```bash
cd frontend && npm test -- src/AppRoutes.test.tsx src/shared/components/layout/PremiumLayout.test.tsx
```

Expected: FAIL because the route and nav item do not exist.

**Step 3: Write minimal implementation**

- Create temporary `frontend/src/features/plan/PlanPage.tsx` that mounts and triggers `usePlanStore` fetches.
- Add route:

```tsx
<Route path="plan" element={<PlanPage />} />
```

- Add nav item labeled with translations, not hardcoded copy.
- Keep route placement near `/dashboard` root, because this is now the conceptual center.

**Step 4: Run tests to verify they pass**

Run the same frontend test command as Step 2.

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/features/plan/PlanPage.tsx frontend/src/AppRoutes.tsx frontend/src/shared/components/layout/PremiumLayout.tsx frontend/src/AppRoutes.test.tsx frontend/src/shared/components/layout/PremiumLayout.test.tsx
git commit -m "feat(plan): add plan route and navigation"
```

## Task 10: Build the Plan Hub UI

**Files:**
- Create: `frontend/src/features/plan/components/PlanView.tsx`
- Create: `frontend/src/features/plan/components/PlanHero.tsx`
- Create: `frontend/src/features/plan/components/PlanMissionToday.tsx`
- Create: `frontend/src/features/plan/components/PlanUpcomingDays.tsx`
- Create: `frontend/src/features/plan/components/PlanCheckpointCard.tsx`
- Create: `frontend/src/features/plan/components/PlanStatusCard.tsx`
- Modify: `frontend/src/features/plan/PlanPage.tsx`
- Test: `frontend/src/features/plan/PlanPage.test.tsx`
- Test: `frontend/src/features/plan/components/PlanView.test.tsx`

**Step 1: Write the failing UI tests**

Cover states:

- no active plan
- awaiting approval
- active
- adjustment pending approval
- expired / review needed

Example:

```tsx
it('shows onboarding empty state when there is no active plan', () => {
  // mock store with null activePlan
});

it('renders mission first layout for active plan', () => {
  // assert hero, missao de hoje, proximos dias, checkpoint, estado do plano
});

it('shows approval CTA when plan is awaiting approval', () => {
  // assert approve button
});
```

**Step 2: Run tests to verify they fail**

Run:

```bash
cd frontend && npm test -- src/features/plan/PlanPage.test.tsx src/features/plan/components/PlanView.test.tsx
```

Expected: FAIL because the UI components do not exist.

**Step 3: Write minimal implementation**

Implement `Mission First` hierarchy:

1. `PlanHero`
   - title
   - objective
   - date window
   - status chip
   - pending approval CTA if applicable

2. `PlanMissionToday`
   - three cards:
     - training
     - nutrition
     - AI guidance

3. `PlanUpcomingDays`
   - 3-7 day compact strip/list

4. `PlanCheckpointCard`
   - last checkpoint summary, analysis, decision, next step

5. `PlanStatusCard`
   - on track / atencao / revisao sugerida / aguardando aprovacao

6. `PlanView`
   - orchestrates empty, loading, pending, active states

Do not add editable forms for the plan in V1.

**Step 4: Run tests to verify they pass**

Run the same test command as Step 2.

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/features/plan frontend/src/features/plan/PlanPage.test.tsx
git commit -m "feat(plan): add mission first plan hub ui"
```

## Task 11: Wire Plan Approval Action in the UI

**Files:**
- Modify: `frontend/src/features/plan/PlanPage.tsx`
- Modify: `frontend/src/features/plan/components/PlanHero.tsx`
- Modify: `frontend/src/features/plan/components/PlanStatusCard.tsx`
- Test: `frontend/src/features/plan/PlanPage.test.tsx`

**Step 1: Write the failing approval interaction tests**

Add tests for:

- approve CTA calls `approvePlan(version)`
- successful approval refreshes the active plan
- failed approval shows notification

**Step 2: Run tests to verify they fail**

Run: `cd frontend && npm test -- src/features/plan/PlanPage.test.tsx`

Expected: FAIL because the approve CTA is static or missing.

**Step 3: Write minimal implementation**

- inject `useNotificationStore`
- call `approvePlan(version)` from CTA
- refresh `activePlan`, `versions`, and `todayBrief`
- show translated success/error copy

If chat approval metadata from Task 7 was deferred, keep the approval entrypoint entirely inside the plan hub for V1.

**Step 4: Run tests to verify they pass**

Run: `cd frontend && npm test -- src/features/plan/PlanPage.test.tsx`

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/features/plan/PlanPage.tsx frontend/src/features/plan/components/PlanHero.tsx frontend/src/features/plan/components/PlanStatusCard.tsx frontend/src/features/plan/PlanPage.test.tsx
git commit -m "feat(plan): add plan approval action in ui"
```

## Task 12: Add Localization for the Plan Feature

**Files:**
- Modify: `frontend/src/locales/pt-BR.json`
- Modify: `frontend/src/locales/en-US.json`
- Modify: `frontend/src/locales/es-ES.json`
- Test: `frontend/src/features/plan/PlanPage.test.tsx`

**Step 1: Write the failing localization assertions**

Extend `PlanPage.test.tsx` to verify translated keys are used instead of hardcoded strings for:

- nav label
- hero status
- mission today labels
- checkpoint labels
- approval CTA
- empty state copy

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- src/features/plan/PlanPage.test.tsx`

Expected: FAIL if copy is still hardcoded.

**Step 3: Write minimal implementation**

Add a `plan` namespace with keys for all new UI strings to all three locale files.

Keep translation keys flat enough to be maintainable, for example:

- `plan.nav`
- `plan.hero.status.active`
- `plan.mission.title`
- `plan.today.training`
- `plan.today.nutrition`
- `plan.today.ai_guidance`
- `plan.checkpoint.title`
- `plan.approval.cta`
- `plan.empty.title`

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- src/features/plan/PlanPage.test.tsx`

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/locales/pt-BR.json frontend/src/locales/en-US.json frontend/src/locales/es-ES.json frontend/src/features/plan/PlanPage.test.tsx
git commit -m "feat(plan): add plan feature translations"
```

## Task 13: Add Dashboard Entry Point to the Plan Hub

**Files:**
- Modify: `frontend/src/features/dashboard/DashboardPage.tsx`
- Modify: `frontend/src/features/dashboard/components/DashboardView.tsx`
- Test: `frontend/src/features/dashboard/DashboardPage.test.tsx`

**Step 1: Write the failing dashboard tests**

Add a test asserting dashboard shows a CTA or summary card that routes to `/dashboard/plan`.

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- src/features/dashboard/DashboardPage.test.tsx`

Expected: FAIL because dashboard does not expose the new hub.

**Step 3: Write minimal implementation**

Add a subtle but clear entrypoint in the dashboard:

- either a CTA card near the primary zone
- or a summary ribbon pointing users toward the active plan

Keep this small. The goal is discoverability, not duplicating the plan page.

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- src/features/dashboard/DashboardPage.test.tsx`

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/features/dashboard/DashboardPage.tsx frontend/src/features/dashboard/components/DashboardView.tsx frontend/src/features/dashboard/DashboardPage.test.tsx
git commit -m "feat(plan): add dashboard entrypoint to plan hub"
```

## Task 14: Run Backend Verification

**Files:**
- No code changes

**Step 1: Run targeted backend tests**

Run:

```bash
cd backend && .venv/bin/pytest \
  tests/api/models/test_plan_models.py \
  tests/test_plan_repository.py \
  tests/test_plan_service.py \
  tests/test_prompt_builder_plan_snapshot.py \
  tests/test_trainer_plan_prompt.py \
  tests/test_plan_tools.py \
  tests/integration/test_plan_endpoints.py -v
```

Expected: PASS

**Step 2: Run backend lint**

Run: `cd backend && .venv/bin/ruff check src tests`

Expected: PASS

**Step 3: Run backend pylint**

Run: `cd backend && .venv/bin/pylint src`

Expected: PASS

**Step 4: Commit verification fixes if needed**

```bash
git add backend
git commit -m "fix(plan): satisfy backend verification"
```

## Task 15: Run Frontend Verification

**Files:**
- No code changes

**Step 1: Run targeted frontend tests**

Run:

```bash
cd frontend && npm test -- \
  src/shared/hooks/usePlan.test.ts \
  src/AppRoutes.test.tsx \
  src/shared/components/layout/PremiumLayout.test.tsx \
  src/features/plan/PlanPage.test.tsx \
  src/features/plan/components/PlanView.test.tsx \
  src/features/dashboard/DashboardPage.test.tsx
```

Expected: PASS

**Step 2: Run frontend lint**

Run: `cd frontend && npm run lint`

Expected: PASS

**Step 3: Run frontend typecheck**

Run: `cd frontend && npm run typecheck`

Expected: PASS

**Step 4: Commit verification fixes if needed**

```bash
git add frontend
git commit -m "fix(plan): satisfy frontend verification"
```

## Task 16: Run Cross-Surface Verification

**Files:**
- No code changes

**Step 1: Run repo verification**

Run: `make verify`

Expected: PASS

**Step 2: Evaluate whether plan-specific E2E is already justified**

If the plan hub has enough stable UI behavior to warrant browser coverage, add:

- `frontend/e2e/xx-plan-hub.spec.ts`

and run the supported containerized path:

Run: `make verify-all`

If not, explicitly defer E2E to the first iteration where plan creation/approval is stable end-to-end.

**Step 3: Commit final verification or defer note**

```bash
git add .
git commit -m "test(plan): verify plan hub integration"
```

## Manual Validation Residuals to Expect

These should remain only if not fully automatable in this iteration:

- IA proposes a good first plan from a real conversation
- IA asks permission before material plan adjustment in nuanced conversational cases
- premium feel and hierarchy of the plan hub on real mobile/desktop devices
- quality of AI rationale in checkpoint text

If these remain manual-only, capture them in the final delivery table required by `AGENTS.md`.

