from datetime import datetime, timedelta

from src.api.models.plan import (
    ActivePlan,
    PlanProposalInput,
    PlanSnapshotAdherence7D,
    PlanSnapshotExerciseContext,
    PlanSnapshotWeightTrend,
    PlanStatus,
)
from src.services.plan_service import (
    build_next_plan_version,
    build_plan_prompt_snapshot,
    format_plan_snapshot,
)


def make_plan() -> ActivePlan:
    return ActivePlan(
        user_email="user@test.com",
        status=PlanStatus.ACTIVE,
        title="Plano Atual",
        objective_summary="Ganhar massa com controle de gordura",
        start_date=datetime(2026, 4, 19),
        end_date=datetime(2026, 6, 19),
        version=2,
        strategy={
            "primary_goal": "gain_muscle",
            "success_criteria": ["volume em alta"],
            "constraints": ["viagem quinta"],
            "coaching_rationale": "superavit leve",
            "adaptation_policy": "approval_required",
        },
        execution={
            "today_training": {"title": "Push A"},
            "today_nutrition": {"calories": 3000, "protein_target": 180},
            "upcoming_days": ["Pull", "Legs"],
            "active_focus": "consistencia",
            "current_risks": ["sono irregular"],
            "pending_changes": [],
        },
        tracking={
            "checkpoints": [{"summary": "aderencia boa"}],
            "adherence_snapshot": {"training": "ok", "nutrition": "ok"},
            "progress_snapshot": {"status": "on_track"},
            "last_ai_assessment": "manter estrategia",
            "last_user_acknowledgement": None,
        },
        governance={"change_reason": None, "approval_request": None},
    )


def test_build_plan_prompt_snapshot_returns_none_when_missing_plan():
    assert build_plan_prompt_snapshot(None) is None


def test_build_plan_prompt_snapshot_compacts_active_plan():
    snapshot = build_plan_prompt_snapshot(make_plan())

    assert snapshot is not None
    assert snapshot.plan_period == "2026-04-19 a 2026-06-19"
    assert snapshot.status == "active"
    assert snapshot.today_training == "Push A"
    assert "3000" in snapshot.today_nutrition
    assert snapshot.critical_constraints == ["viagem quinta"]


def test_build_plan_prompt_snapshot_prefers_today_training_from_upcoming_days():
    plan = make_plan()
    plan.execution.today_training = {"title": "Push A (ontem)"}
    plan.execution.upcoming_days = [
        {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "label": "Hoje",
            "status": "planned",
            "training": {
                "title": "Pull B (hoje)",
                "session": {"exercises": [{"name": "Remada", "sets": 3, "reps": "8-10"}]},
            },
            "nutrition": "2600 kcal",
        }
    ]

    snapshot = build_plan_prompt_snapshot(plan)

    assert snapshot is not None
    assert snapshot.today_training == "Pull B (hoje)"


def test_format_plan_snapshot_creates_prompt_ready_block():
    snapshot = build_plan_prompt_snapshot(make_plan())
    content = format_plan_snapshot(snapshot)

    assert "Plano ativo" in content
    assert "Periodo do plano: 2026-04-19 a 2026-06-19" in content
    assert "Push A" in content
    assert "Pull" in content


def test_build_plan_prompt_snapshot_filters_non_future_upcoming_days():
    plan = make_plan()
    today_iso = datetime.now().strftime("%Y-%m-%d")
    yesterday_iso = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow_iso = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    plan.execution.upcoming_days = [
        {"date": yesterday_iso, "label": "Ontem", "training": "Push", "status": "planned"},
        {"date": today_iso, "label": "Hoje", "training": "Pull", "status": "planned"},
        {"date": tomorrow_iso, "label": "Amanha", "training": "Legs", "status": "planned"},
    ]

    snapshot = build_plan_prompt_snapshot(plan)

    assert snapshot is not None
    assert len(snapshot.upcoming_days) == 1
    assert tomorrow_iso in snapshot.upcoming_days[0]


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

    assert snapshot is not None
    assert snapshot.today_training_context[0].last_load_kg == 80.0
    assert snapshot.adherence_7d is not None
    assert snapshot.adherence_7d.nutrition_percent == 86
    assert snapshot.weight_trend_weekly is not None
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


def test_format_plan_snapshot_keeps_last_load_field_when_history_missing():
    snapshot = build_plan_prompt_snapshot(
        make_plan(),
        today_training_context=[
            PlanSnapshotExerciseContext(
                exercise_name="Supino Reto",
                prescribed_sets="3",
                prescribed_reps="8-10",
                load_guidance="RPE 8",
                last_load_kg=None,
                last_performed_at=None,
            )
        ],
    )
    content = format_plan_snapshot(snapshot)

    assert "Supino Reto: 3x8-10 | ultima carga registrada: indisponivel" in content


def test_build_next_plan_version_creates_valid_default_date_window():
    payload = PlanProposalInput(
        title="Plano Inicial",
        objective_summary="Recomposicao corporal",
        change_reason="inicio",
        strategy={
            "dias_disponiveis_treino": ["seg", "ter", "qui", "sex"],
            "frequencia_treino_semana": 4,
            "nivel_treinamento": "intermediario",
            "restricoes_lesoes": [],
            "tempo_por_sessao_min": 60,
            "preferencia_ambiente": "academia",
        },
        execution={
            "today_training": {
                "title": "Full Body A",
                "session": {
                    "exercises": [
                        {
                            "name": "Agachamento",
                            "sets": 4,
                            "reps": "6-8",
                            "load_guidance": "RPE 8",
                        }
                    ]
                },
            },
            "today_nutrition": {"calories": 2400, "protein_target": 140},
            "upcoming_days": [
                {
                    "date": "2026-04-20",
                    "label": "Amanha",
                    "training": "Upper A",
                    "nutrition": "2400 kcal",
                    "status": "planned",
                }
            ],
            "active_focus": "consistencia",
        },
        tracking={},
    )

    plan = build_next_plan_version("user@test.com", None, payload)

    assert plan.end_date > plan.start_date
    assert (plan.end_date - plan.start_date).days >= 6
