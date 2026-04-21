# Plan Snapshot Coaching Context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enriquecer o `PlanSnapshot` entregue ao prompt da IA com `last_load` por exercicio do treino de hoje, aderencia 7d de treino e nutricao, e tendencia semanal de peso reaproveitando a fonte oficial do metabolismo.

**Architecture:** A implementacao adiciona campos estruturados ao modelo `PlanSnapshot`, cria um agregador dedicado de contexto de coaching para derivar sinais de treino e nutricao e reaproveita `AdaptiveTDEEService` para tendencia semanal de peso. O fluxo de injeção do prompt continua centrado em `PlanSnapshot`, mas `trainer.py` e `plan_tools.py` passam a construir um snapshot enriquecido em vez de apenas resumir o plano ativo.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, Pytest, Ruff, Pylint, LangChain tools

---

## File Structure

### Create

- `backend/src/services/plan_snapshot_context.py`
- `backend/tests/test_plan_snapshot_context.py`

### Modify

- `backend/src/api/models/plan.py`
- `backend/src/services/plan_service.py`
- `backend/src/services/plan_tools.py`
- `backend/src/services/trainer.py`
- `backend/tests/api/models/test_plan_models.py`
- `backend/tests/test_plan_service.py`
- `backend/tests/test_plan_tools.py`
- `backend/tests/test_trainer_plan_prompt.py`

### Keep As-Is Unless Blocked

- `backend/src/services/prompt_builder.py`
- `backend/tests/test_prompt_builder_plan_snapshot.py`
- `backend/src/services/database.py`

`prompt_builder.py` nao precisa conhecer as novas estruturas internas, porque ele ja consome o `PlanSnapshot` formatado em texto. `database.py` ja expoe os delegators necessarios para treinos, nutricao e peso.

---

### Task 1: Expandir o contrato do `PlanSnapshot`

**Files:**
- Modify: `backend/src/api/models/plan.py`
- Test: `backend/tests/api/models/test_plan_models.py`

- [ ] **Step 1: Escrever os testes que falham para os novos campos do snapshot**

Adicione cenarios cobrindo campos opcionais estruturados e o caso de snapshot compacto sem dados extras.

```python
from src.api.models.plan import (
    PlanSnapshot,
    PlanSnapshotAdherence7D,
    PlanSnapshotExerciseContext,
    PlanSnapshotWeightTrend,
)


def test_plan_snapshot_allows_structured_coaching_context():
    snapshot = PlanSnapshot(
        title="Plano Atual",
        objective_summary="Ganhar massa com minimo ganho de gordura",
        plan_period="2026-04-19 a 2026-06-07",
        status="active",
        active_focus="progressao de carga",
        today_training="Push com 6 exercicios",
        today_nutrition="3000 kcal / 180g proteina",
        upcoming_days=["Pull", "Legs"],
        today_training_context=[
            PlanSnapshotExerciseContext(
                exercise_name="Supino Reto",
                prescribed_sets="4",
                prescribed_reps="6-8",
                load_guidance="RPE 8",
                last_load_kg=80.0,
                last_performed_at="2026-04-18",
            )
        ],
        adherence_7d=PlanSnapshotAdherence7D(
            training_percent=100,
            nutrition_percent=86,
            window_start="2026-04-13",
            window_end="2026-04-19",
        ),
        weight_trend_weekly=PlanSnapshotWeightTrend(
            value_kg_per_week=-0.2,
            source="adaptive_tdee",
        ),
        last_checkpoint_summary="aderencia boa",
        critical_constraints=["viagem quinta"],
        pending_adjustment=None,
    )

    assert snapshot.today_training_context[0].exercise_name == "Supino Reto"
    assert snapshot.adherence_7d.training_percent == 100
    assert snapshot.weight_trend_weekly.value_kg_per_week == -0.2


def test_plan_snapshot_keeps_new_context_optional():
    snapshot = PlanSnapshot(
        title="Plano Atual",
        objective_summary="Ganhar massa",
        plan_period="2026-04-19 a 2026-06-19",
        status="active",
        active_focus="consistencia",
        today_training="Push",
        today_nutrition="3000 kcal / 180g",
        upcoming_days=["Pull"],
        last_checkpoint_summary="aderencia boa",
        critical_constraints=["viagem quinta"],
        pending_adjustment=None,
    )

    assert snapshot.today_training_context == []
    assert snapshot.adherence_7d is None
    assert snapshot.weight_trend_weekly is None
```

- [ ] **Step 2: Rodar apenas os testes do modelo para ver a falha**

Run: `cd backend && .venv/bin/pytest tests/api/models/test_plan_models.py -v`

Expected: FAIL com `ImportError`, `ValidationError` ou atributo ausente para os novos tipos/campos.

- [ ] **Step 3: Implementar os novos modelos estruturados em `plan.py`**

Adicione modelos dedicados e campos opcionais em `PlanSnapshot`.

```python
class PlanSnapshotExerciseContext(BaseModel):
    """Exercise-level coaching context injected into prompt snapshot."""

    exercise_name: str = Field(..., min_length=1)
    prescribed_sets: str | None = None
    prescribed_reps: str | None = None
    load_guidance: str | None = None
    last_load_kg: float | None = None
    last_load_text: str | None = None
    last_performed_at: str | None = None


class PlanSnapshotAdherence7D(BaseModel):
    """Simple 7-day adherence summary for prompt context."""

    training_percent: int | None = Field(default=None, ge=0, le=100)
    nutrition_percent: int | None = Field(default=None, ge=0, le=100)
    window_start: str = Field(..., min_length=1)
    window_end: str = Field(..., min_length=1)


class PlanSnapshotWeightTrend(BaseModel):
    """Weekly weight trend sourced from adaptive metabolism service."""

    value_kg_per_week: float
    source: str = Field(..., min_length=1)


class PlanSnapshot(BaseModel):
    """Compact and prompt-safe active plan context."""

    title: str = Field(..., min_length=1)
    objective_summary: str = Field(..., min_length=1)
    plan_period: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    active_focus: str = Field(..., min_length=1)
    today_training: str = Field(..., min_length=1)
    today_nutrition: str = Field(..., min_length=1)
    upcoming_days: list[str] = Field(default_factory=list)
    today_training_context: list[PlanSnapshotExerciseContext] = Field(default_factory=list)
    adherence_7d: PlanSnapshotAdherence7D | None = None
    weight_trend_weekly: PlanSnapshotWeightTrend | None = None
    last_checkpoint_summary: str | None = None
    critical_constraints: list[str] = Field(default_factory=list)
    pending_adjustment: str | None = None
```

- [ ] **Step 4: Rodar os testes do modelo novamente**

Run: `cd backend && .venv/bin/pytest tests/api/models/test_plan_models.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/api/models/plan.py backend/tests/api/models/test_plan_models.py
git commit -m "feat: expand plan snapshot contract"
```

---

### Task 2: Criar o agregador de contexto de coaching

**Files:**
- Create: `backend/src/services/plan_snapshot_context.py`
- Test: `backend/tests/test_plan_snapshot_context.py`

- [ ] **Step 1: Escrever os testes unitarios do agregador antes da implementacao**

Cubra matching de exercicios, usuarios sem dados, aderencia 7d e reutilizacao da tendencia oficial de peso.

```python
from datetime import datetime
from unittest.mock import MagicMock

from src.api.models.plan import ActivePlan, PlanStatus
from src.api.models.workout_log import WorkoutLog, ExerciseLog
from src.api.models.nutrition_log import NutritionLog
from src.api.models.weight_log import WeightLog
from src.services.plan_snapshot_context import build_plan_snapshot_context


def make_plan() -> ActivePlan:
    return ActivePlan(
        user_email="user@test.com",
        status=PlanStatus.ACTIVE,
        title="Plano Atual",
        objective_summary="Ganhar massa",
        start_date=datetime(2026, 4, 19),
        end_date=datetime(2026, 6, 19),
        version=1,
        strategy={
            "primary_goal": "gain_muscle",
            "success_criteria": ["volume"],
            "constraints": [],
            "coaching_rationale": "superavit",
            "adaptation_policy": "approval_required",
        },
        execution={
            "today_training": {
                "title": "Push",
                "session": {
                    "exercises": [
                        {"name": "Supino Reto", "sets": 4, "reps": "6-8", "load_guidance": "RPE 8"},
                        {"name": "Remada Curvada", "sets": 4, "reps": "8-10", "load_guidance": "RPE 8"},
                    ]
                },
            },
            "today_nutrition": {"calories": 3000, "protein_target": 180},
            "upcoming_days": [
                {"date": "2026-04-17", "status": "planned", "training": {"title": "Push"}},
                {"date": "2026-04-18", "status": "rest"},
                {"date": "2026-04-19", "status": "planned", "training": {"title": "Pull"}},
            ],
            "active_focus": "consistencia",
            "current_risks": [],
            "pending_changes": [],
        },
        tracking={"checkpoints": [], "adherence_snapshot": {}, "progress_snapshot": {}},
        governance={"change_reason": None, "approval_request": None},
    )


def test_build_plan_snapshot_context_returns_safe_empty_values_for_user_without_history():
    db = MagicMock()
    db.get_workout_logs.return_value = []
    db.get_nutrition_logs_by_date_range.return_value = []

    context = build_plan_snapshot_context(
        database=db,
        user_email="user@test.com",
        plan=make_plan(),
        metabolism_data={"weight_change_per_week": 0.0},
        now=datetime(2026, 4, 19, 10, 0, 0),
    )

    assert len(context.today_training_context) == 2
    assert all(item.last_load_kg is None for item in context.today_training_context)
    assert context.adherence_7d.nutrition_percent == 0
    assert context.adherence_7d.training_percent == 0
    assert context.weight_trend_weekly.value_kg_per_week == 0.0


def test_build_plan_snapshot_context_uses_latest_session_not_historic_pr():
    db = MagicMock()
    db.get_workout_logs.return_value = [
        {
            "date": datetime(2026, 4, 18, 8, 0, 0),
            "exercises": [{"name": "Supino reto", "reps_per_set": [8, 8], "weights_per_set": [80.0, 80.0]}],
        },
        {
            "date": datetime(2026, 3, 10, 8, 0, 0),
            "exercises": [{"name": "Supino Reto", "reps_per_set": [5], "weights_per_set": [100.0]}],
        },
    ]
    db.get_nutrition_logs_by_date_range.return_value = []

    context = build_plan_snapshot_context(
        database=db,
        user_email="user@test.com",
        plan=make_plan(),
        metabolism_data={"weight_change_per_week": -0.2},
        now=datetime(2026, 4, 19, 10, 0, 0),
    )

    supino = next(item for item in context.today_training_context if item.exercise_name == "Supino Reto")
    assert supino.last_load_kg == 80.0
    assert supino.last_performed_at == "2026-04-18"


def test_build_plan_snapshot_context_does_not_cross_match_similar_exercises():
    db = MagicMock()
    db.get_workout_logs.return_value = [
        {
            "date": datetime(2026, 4, 18, 8, 0, 0),
            "exercises": [{"name": "Supino Inclinado", "reps_per_set": [8], "weights_per_set": [34.0]}],
        }
    ]
    db.get_nutrition_logs_by_date_range.return_value = []

    context = build_plan_snapshot_context(
        database=db,
        user_email="user@test.com",
        plan=make_plan(),
        metabolism_data={"weight_change_per_week": -0.2},
        now=datetime(2026, 4, 19, 10, 0, 0),
    )

    supino = next(item for item in context.today_training_context if item.exercise_name == "Supino Reto")
    assert supino.last_load_kg is None
```

Adicione tambem, no mesmo arquivo de teste, casos explicitos para:

- pesos zerados na ultima sessao nao geram `last_load`
- listas `weights_per_set` e `reps_per_set` com tamanhos diferentes nao quebram o matching
- ausencia de treino planejado na janela retorna `training_percent is None`
- logs nutricionais duplicados no mesmo dia contam apenas uma vez
- `weight_change_per_week = 0.0` gera `PlanSnapshotWeightTrend` valido, nao `None`
- exercicios com diferenca apenas de caixa e espacos extras ainda casam corretamente
- exercicios parecidos como `Supino Reto` e `Supino Inclinado` nao compartilham carga
- sessoes fora da janela de 90 dias sao ignoradas

- [ ] **Step 2: Rodar a nova suite de contexto para confirmar a falha**

Run: `cd backend && .venv/bin/pytest tests/test_plan_snapshot_context.py -v`

Expected: FAIL com modulo ausente ou funcoes/classes ainda nao implementadas.

- [ ] **Step 3: Implementar o agregador em um servico dedicado**

Crie um modulo autocontido com normalizacao minima de nomes, janela movel de 7 dias e extracao da ultima carga valida da ultima sessao relevante.

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
import re

from src.api.models.plan import (
    PlanSnapshotAdherence7D,
    PlanSnapshotExerciseContext,
    PlanSnapshotWeightTrend,
)


def _normalize_exercise_name(name: str) -> str:
    collapsed = re.sub(r"\s+", " ", name.strip().lower())
    return collapsed


def _extract_today_exercises(plan) -> list[dict]:
    training = plan.execution.today_training
    session = training.get("session", {}) if isinstance(training, dict) else {}
    exercises = session.get("exercises")
    if isinstance(exercises, list):
        return [item for item in exercises if isinstance(item, dict) and item.get("name")]
    direct = training.get("exercises", []) if isinstance(training, dict) else []
    return [item for item in direct if isinstance(item, dict) and item.get("name")]


def _build_exercise_context(today_exercises: list[dict], workout_logs: list[dict], now: datetime) -> list[PlanSnapshotExerciseContext]:
    earliest = now - timedelta(days=90)
    recent_logs = [
        log for log in workout_logs
        if log.get("date") and log["date"] >= earliest
    ]
    result: list[PlanSnapshotExerciseContext] = []

    for exercise in today_exercises:
        target_name = str(exercise["name"])
        normalized_target = _normalize_exercise_name(target_name)
        last_load = None
        last_date = None

        for workout in recent_logs:
            matches = []
            for logged_exercise in workout.get("exercises", []):
                logged_name = logged_exercise.get("name")
                if not isinstance(logged_name, str):
                    continue
                if _normalize_exercise_name(logged_name) != normalized_target:
                    continue
                weights = [value for value in logged_exercise.get("weights_per_set", []) if isinstance(value, (int, float)) and value > 0]
                if weights:
                    matches.append(max(weights))
            if matches:
                last_load = max(matches)
                last_date = workout["date"]
                break

        result.append(
            PlanSnapshotExerciseContext(
                exercise_name=target_name,
                prescribed_sets=str(exercise.get("sets")) if exercise.get("sets") is not None else None,
                prescribed_reps=str(exercise.get("reps")) if exercise.get("reps") is not None else None,
                load_guidance=exercise.get("load_guidance"),
                last_load_kg=float(last_load) if last_load is not None else None,
                last_performed_at=last_date.date().isoformat() if last_date is not None else None,
            )
        )

    return result


@dataclass
class PlanSnapshotContext:
    today_training_context: list[PlanSnapshotExerciseContext]
    adherence_7d: PlanSnapshotAdherence7D | None
    weight_trend_weekly: PlanSnapshotWeightTrend | None
```

Implemente tambem:

- `_calculate_nutrition_adherence(...)`
- `_calculate_training_adherence(...)`
- `build_plan_snapshot_context(...)`

`build_plan_snapshot_context(...)` deve:

- receber `database`, `user_email`, `plan`, `metabolism_data`, `now`
- buscar `database.get_workout_logs(user_email, limit=50)`
- buscar `database.get_nutrition_logs_by_date_range(user_email, window_start, window_end)`
- popular `PlanSnapshotWeightTrend(value_kg_per_week=..., source="adaptive_tdee")` quando `weight_change_per_week` existir, inclusive `0.0`

- [ ] **Step 4: Rodar a suite do agregador ate passar**

Run: `cd backend && .venv/bin/pytest tests/test_plan_snapshot_context.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/services/plan_snapshot_context.py backend/tests/test_plan_snapshot_context.py
git commit -m "feat: add plan snapshot coaching context service"
```

---

### Task 3: Conectar o agregador ao builder e ao formatter do snapshot

**Files:**
- Modify: `backend/src/services/plan_service.py`
- Test: `backend/tests/test_plan_service.py`

- [ ] **Step 1: Escrever os testes que falham para snapshot enriquecido e formatter resiliente**

Expanda os testes existentes para aceitar contexto enriquecido sem quebrar compatibilidade.

```python
from src.api.models.plan import (
    PlanSnapshotAdherence7D,
    PlanSnapshotExerciseContext,
    PlanSnapshotWeightTrend,
)
from src.services.plan_service import build_plan_prompt_snapshot, format_plan_snapshot


def test_build_plan_prompt_snapshot_accepts_prebuilt_context():
    snapshot = build_plan_prompt_snapshot(
        make_plan(),
        today_training_context=[
            PlanSnapshotExerciseContext(
                exercise_name="Supino Reto",
                prescribed_sets="4",
                prescribed_reps="6-8",
                load_guidance="RPE 8",
                last_load_kg=80.0,
                last_performed_at="2026-04-18",
            )
        ],
        adherence_7d=PlanSnapshotAdherence7D(
            training_percent=100,
            nutrition_percent=86,
            window_start="2026-04-13",
            window_end="2026-04-19",
        ),
        weight_trend_weekly=PlanSnapshotWeightTrend(
            value_kg_per_week=-0.2,
            source="adaptive_tdee",
        ),
    )

    assert snapshot.today_training_context[0].last_load_kg == 80.0
    assert snapshot.adherence_7d.nutrition_percent == 86
    assert snapshot.weight_trend_weekly.value_kg_per_week == -0.2


def test_format_plan_snapshot_includes_enriched_sections_when_available():
    snapshot = build_plan_prompt_snapshot(
        make_plan(),
        today_training_context=[
            PlanSnapshotExerciseContext(
                exercise_name="Supino Reto",
                prescribed_sets="4",
                prescribed_reps="6-8",
                load_guidance="RPE 8",
                last_load_kg=80.0,
                last_performed_at="2026-04-18",
            )
        ],
        adherence_7d=PlanSnapshotAdherence7D(
            training_percent=100,
            nutrition_percent=86,
            window_start="2026-04-13",
            window_end="2026-04-19",
        ),
        weight_trend_weekly=PlanSnapshotWeightTrend(
            value_kg_per_week=-0.2,
            source="adaptive_tdee",
        ),
    )

    content = format_plan_snapshot(snapshot)

    assert "Contexto do treino de hoje:" in content
    assert "Supino Reto: 4x6-8" in content
    assert "Aderencia 7d: treino 100% | nutricao 86%" in content
    assert "Tendencia de peso: -0.20 kg/semana" in content
```

- [ ] **Step 2: Rodar os testes de plan service e confirmar a falha**

Run: `cd backend && .venv/bin/pytest tests/test_plan_service.py -v`

Expected: FAIL por assinatura antiga ou ausencia das novas secoes no formatter.

- [ ] **Step 3: Implementar a composicao do snapshot enriquecido**

Mantenha compatibilidade do builder aceitando contexto opcional por parametro nomeado.

```python
def build_plan_prompt_snapshot(
    plan: ActivePlan | None,
    *,
    today_training_context: list[PlanSnapshotExerciseContext] | None = None,
    adherence_7d: PlanSnapshotAdherence7D | None = None,
    weight_trend_weekly: PlanSnapshotWeightTrend | None = None,
) -> PlanSnapshot | None:
    """Builds a compact snapshot from active plan payload."""
    if plan is None:
        return None

    checkpoints = plan.tracking.checkpoints
    last_checkpoint = checkpoints[-1].summary if checkpoints else None
    pending_adjustment = None
    if plan.governance.approval_request is not None:
        pending_adjustment = plan.governance.approval_request.summary

    return PlanSnapshot(
        title=plan.title,
        objective_summary=plan.objective_summary,
        plan_period=(
            f"{plan.start_date.strftime('%Y-%m-%d')} a "
            f"{plan.end_date.strftime('%Y-%m-%d')}"
        ),
        status=plan.status.value,
        active_focus=plan.execution.active_focus,
        today_training=_extract_today_training(plan.execution.model_dump()),
        today_nutrition=_extract_today_nutrition(plan.execution.model_dump()),
        upcoming_days=[str(item) for item in plan.execution.upcoming_days],
        today_training_context=today_training_context or [],
        adherence_7d=adherence_7d,
        weight_trend_weekly=weight_trend_weekly,
        last_checkpoint_summary=last_checkpoint,
        critical_constraints=plan.strategy.constraints,
        pending_adjustment=pending_adjustment,
    )
```

Atualize `format_plan_snapshot(...)` para montar linhas opcionais somente quando houver dados:

```python
    training_context_lines = []
    if snapshot.today_training_context:
        training_context_lines.append("Contexto do treino de hoje:")
        for item in snapshot.today_training_context:
            prescription = f"{item.prescribed_sets or '-'}x{item.prescribed_reps or '-'}"
            if item.last_load_kg is not None and item.last_performed_at:
                training_context_lines.append(
                    f"- {item.exercise_name}: {prescription} | ultima carga registrada "
                    f"{item.last_load_kg:.0f} kg em {item.last_performed_at}"
                )
            else:
                training_context_lines.append(f"- {item.exercise_name}: {prescription}")

    adherence_line = ""
    if snapshot.adherence_7d is not None:
        training_pct = (
            "indisponivel"
            if snapshot.adherence_7d.training_percent is None
            else f"{snapshot.adherence_7d.training_percent}%"
        )
        nutrition_pct = (
            "indisponivel"
            if snapshot.adherence_7d.nutrition_percent is None
            else f"{snapshot.adherence_7d.nutrition_percent}%"
        )
        adherence_line = f"Aderencia 7d: treino {training_pct} | nutricao {nutrition_pct}"

    trend_line = ""
    if snapshot.weight_trend_weekly is not None:
        trend_line = (
            "Tendencia de peso: "
            f"{snapshot.weight_trend_weekly.value_kg_per_week:+.2f} kg/semana"
        )
```

- [ ] **Step 4: Rodar os testes do plan service novamente**

Run: `cd backend && .venv/bin/pytest tests/test_plan_service.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/services/plan_service.py backend/tests/test_plan_service.py
git commit -m "feat: format enriched plan snapshot"
```

---

### Task 4: Injetar o snapshot enriquecido nos fluxos reais da IA

**Files:**
- Modify: `backend/src/services/plan_tools.py`
- Modify: `backend/src/services/trainer.py`
- Modify: `backend/tests/test_plan_tools.py`
- Modify: `backend/tests/test_trainer_plan_prompt.py`

- [ ] **Step 1: Escrever os testes de integracao de tool e trainer antes da mudanca**

Garanta que tool e trainer constroem o snapshot usando o contexto enriquecido.

```python
from unittest.mock import MagicMock

from src.services.plan_tools import create_get_plan_prompt_snapshot_tool


def test_get_plan_prompt_snapshot_tool_returns_enriched_snapshot(monkeypatch):
    db = MagicMock()
    db.get_active_plan.return_value = make_active_plan()

    monkeypatch.setattr(
        "src.services.plan_tools.build_plan_snapshot_context",
        MagicMock(
            return_value=MagicMock(
                today_training_context=[],
                adherence_7d=MagicMock(training_percent=100, nutrition_percent=86),
                weight_trend_weekly=MagicMock(value_kg_per_week=-0.2, source="adaptive_tdee"),
            )
        ),
    )
    monkeypatch.setattr(
        "src.services.plan_tools.AdaptiveTDEEService",
        MagicMock(return_value=MagicMock(calculate_tdee=MagicMock(return_value={"weight_change_per_week": -0.2}))),
    )

    tool = create_get_plan_prompt_snapshot_tool(db, "user@test.com")
    result = tool.invoke({})

    assert "Aderencia 7d:" in result
    assert "Tendencia de peso:" in result
```

No teste do trainer, passe a verificar que o snapshot entregue ao `PromptBuilder` ja vem preenchido:

```python
    plan_snapshot = build_input_data_spy.call_args.kwargs.get("plan_snapshot")
    assert isinstance(plan_snapshot, PlanSnapshot)
    assert plan_snapshot.weight_trend_weekly.value_kg_per_week == -0.2
```

- [ ] **Step 2: Rodar os testes das duas integracoes para confirmar a falha**

Run: `cd backend && .venv/bin/pytest tests/test_plan_tools.py tests/test_trainer_plan_prompt.py -v`

Expected: FAIL porque `plan_tools.py` e `trainer.py` ainda nao chamam o agregador.

- [ ] **Step 3: Implementar a injecao do contexto enriquecido**

Em `plan_tools.py`, importe o agregador e o servico oficial de metabolismo:

```python
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.services.plan_snapshot_context import build_plan_snapshot_context
```

Atualize `get_plan_prompt_snapshot()`:

```python
    def get_plan_prompt_snapshot() -> str:
        """Retorna o snapshot compacto de plano usado no contexto do prompt."""
        plan = database.get_active_plan(user_email)
        if plan is None:
            return "Nenhum plano ativo encontrado."

        metabolism_data = AdaptiveTDEEService(database).calculate_tdee(user_email)
        context = build_plan_snapshot_context(
            database=database,
            user_email=user_email,
            plan=plan,
            metabolism_data=metabolism_data,
        )
        snapshot = build_plan_prompt_snapshot(
            plan,
            today_training_context=context.today_training_context,
            adherence_7d=context.adherence_7d,
            weight_trend_weekly=context.weight_trend_weekly,
        )
        return format_plan_snapshot(snapshot)
```

Em `trainer.py`, no ponto em que o plano ativo e lido antes de chamar `prompt_builder.build_input_data(...)`, injete o mesmo fluxo:

```python
        active_plan = self._database.get_active_plan(user_email)
        plan_snapshot = None
        if active_plan is not None:
            metabolism_data = AdaptiveTDEEService(self._database).calculate_tdee(user_email)
            context = build_plan_snapshot_context(
                database=self._database,
                user_email=user_email,
                plan=active_plan,
                metabolism_data=metabolism_data,
            )
            plan_snapshot = build_plan_prompt_snapshot(
                active_plan,
                today_training_context=context.today_training_context,
                adherence_7d=context.adherence_7d,
                weight_trend_weekly=context.weight_trend_weekly,
            )
```

`get_today_plan_brief()` pode permanecer sem os campos ricos se o texto continuar curto; nao aumente o escopo aqui.

- [ ] **Step 4: Rodar os testes das integracoes novamente**

Run: `cd backend && .venv/bin/pytest tests/test_plan_tools.py tests/test_trainer_plan_prompt.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/services/plan_tools.py backend/src/services/trainer.py backend/tests/test_plan_tools.py backend/tests/test_trainer_plan_prompt.py
git commit -m "feat: inject enriched plan snapshot into ai flows"
```

---

### Task 5: Executar a validacao final do backend

**Files:**
- Verify only: `backend/src/api/models/plan.py`
- Verify only: `backend/src/services/plan_snapshot_context.py`
- Verify only: `backend/src/services/plan_service.py`
- Verify only: `backend/src/services/plan_tools.py`
- Verify only: `backend/src/services/trainer.py`
- Verify only: `backend/tests/api/models/test_plan_models.py`
- Verify only: `backend/tests/test_plan_snapshot_context.py`
- Verify only: `backend/tests/test_plan_service.py`
- Verify only: `backend/tests/test_plan_tools.py`
- Verify only: `backend/tests/test_trainer_plan_prompt.py`

- [ ] **Step 1: Rodar a suite focada das alteracoes**

Run:

```bash
cd backend && .venv/bin/pytest \
  tests/api/models/test_plan_models.py \
  tests/test_plan_snapshot_context.py \
  tests/test_plan_service.py \
  tests/test_plan_tools.py \
  tests/test_trainer_plan_prompt.py -v
```

Expected: PASS

- [ ] **Step 2: Rodar o gate estatico exigido pelo projeto**

Run: `cd backend && .venv/bin/ruff check src tests && .venv/bin/pylint src`

Expected: PASS sem warnings nos arquivos tocados.

- [ ] **Step 3: Revisar o diff final para garantir que o escopo ficou restrito a IA**

Run: `git diff --stat HEAD~4..HEAD`

Expected: somente arquivos de backend ligados a snapshot, contexto e testes.

- [ ] **Step 4: Commit final de ajuste, se necessario**

```bash
git add backend/src/api/models/plan.py \
  backend/src/services/plan_snapshot_context.py \
  backend/src/services/plan_service.py \
  backend/src/services/plan_tools.py \
  backend/src/services/trainer.py \
  backend/tests/api/models/test_plan_models.py \
  backend/tests/test_plan_snapshot_context.py \
  backend/tests/test_plan_service.py \
  backend/tests/test_plan_tools.py \
  backend/tests/test_trainer_plan_prompt.py
git commit -m "test: finalize plan snapshot coaching context coverage"
```

- [ ] **Step 5: Registrar os casos manuais residuais**

Documente apenas os casos que realmente nao puderam ser automatizados. Se toda a cobertura desta entrega estiver automatizada em nivel unitario/integracao, o resultado esperado desta etapa e deixar a tabela manual vazia no fechamento da execucao.
