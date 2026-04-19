from datetime import datetime

from src.api.models.plan import ActivePlan, PlanStatus
from src.services.plan_service import build_plan_prompt_snapshot, format_plan_snapshot


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
    assert snapshot.status == "active"
    assert snapshot.today_training == "Push A"
    assert "3000" in snapshot.today_nutrition
    assert snapshot.critical_constraints == ["viagem quinta"]


def test_format_plan_snapshot_creates_prompt_ready_block():
    snapshot = build_plan_prompt_snapshot(make_plan())
    content = format_plan_snapshot(snapshot)

    assert "Plano ativo" in content
    assert "Push A" in content
    assert "Pull" in content
