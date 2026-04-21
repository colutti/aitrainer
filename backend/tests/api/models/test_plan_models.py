from datetime import datetime

from src.api.models.plan import (
    PlanStatus,
    PlanSnapshot,
    PlanSnapshotAdherence7D,
    PlanSnapshotExerciseContext,
    PlanSnapshotWeightTrend,
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
        plan_period="2026-04-19 a 2026-06-07",
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
    assert snapshot.today_training_context == []
    assert snapshot.adherence_7d is None
    assert snapshot.weight_trend_weekly is None


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
