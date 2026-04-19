from datetime import datetime
from unittest.mock import MagicMock

from src.api.models.plan import ActivePlan, PlanStatus
from src.services.plan_tools import (
    create_get_active_plan_tool,
    create_get_plan_prompt_snapshot_tool,
    create_create_plan_proposal_tool,
    create_propose_plan_adjustment_tool,
    create_approve_plan_change_tool,
    create_get_today_plan_brief_tool,
)


def make_active_plan(version=1, status=PlanStatus.ACTIVE) -> ActivePlan:
    return ActivePlan(
        user_email="user@test.com",
        status=status,
        title="Plano Atual",
        objective_summary="Ganhar massa",
        start_date=datetime(2026, 4, 19),
        end_date=datetime(2026, 6, 19),
        version=version,
        strategy={
            "primary_goal": "gain_muscle",
            "success_criteria": ["volume"],
            "constraints": ["viagem"],
            "coaching_rationale": "superavit",
            "adaptation_policy": "approval_required",
        },
        execution={
            "today_training": {"title": "Push"},
            "today_nutrition": {"calories": 3000, "protein_target": 180},
            "upcoming_days": ["Pull"],
            "active_focus": "consistencia",
            "current_risks": [],
            "pending_changes": [],
        },
        tracking={
            "checkpoints": [{"summary": "ok"}],
            "adherence_snapshot": {"training": "ok", "nutrition": "ok"},
            "progress_snapshot": {"status": "on_track"},
            "last_ai_assessment": None,
            "last_user_acknowledgement": None,
        },
        governance={"change_reason": None, "approval_request": None},
    )


def test_get_active_plan_tool_returns_serialized_plan():
    db = MagicMock()
    db.get_active_plan.return_value = make_active_plan()

    tool = create_get_active_plan_tool(db, "user@test.com")
    result = tool.invoke({})

    assert "Plano Atual" in result
    db.get_active_plan.assert_called_once_with("user@test.com")


def test_get_plan_prompt_snapshot_tool_returns_compact_snapshot():
    db = MagicMock()
    db.get_active_plan.return_value = make_active_plan()

    tool = create_get_plan_prompt_snapshot_tool(db, "user@test.com")
    result = tool.invoke({})

    assert "Treino de hoje" in result
    assert "Push" in result


def test_create_plan_proposal_tool_persists_awaiting_approval_version():
    db = MagicMock()
    db.get_latest_plan.return_value = make_active_plan(version=1)
    db.save_plan.return_value = "plan_2"

    tool = create_create_plan_proposal_tool(db, "user@test.com")
    result = tool.invoke(
        {
            "title": "Plano V2",
            "objective_summary": "ajuste",
            "change_reason": "baixa_aderencia",
            "strategy": {},
            "execution": {},
            "tracking": {},
        }
    )

    assert "plan_2" in result
    saved_plan = db.save_plan.call_args.args[0]
    assert saved_plan.status == PlanStatus.AWAITING_APPROVAL
    assert saved_plan.version == 2


def test_propose_plan_adjustment_tool_creates_pending_adjustment_version():
    db = MagicMock()
    db.get_latest_plan.return_value = make_active_plan(version=3)
    db.save_plan.return_value = "plan_4"

    tool = create_propose_plan_adjustment_tool(db, "user@test.com")
    result = tool.invoke({"change_reason": "rotina_mudou", "proposal_summary": "ajuste de volume"})

    assert "plan_4" in result
    saved_plan = db.save_plan.call_args.args[0]
    assert saved_plan.version == 4
    assert saved_plan.status == PlanStatus.AWAITING_APPROVAL


def test_approve_plan_change_tool_delegates_approval():
    db = MagicMock()
    db.approve_plan.return_value = True

    tool = create_approve_plan_change_tool(db, "user@test.com")
    result = tool.invoke({"version": 5})

    assert "aprovado" in result.lower()
    db.approve_plan.assert_called_once_with("user@test.com", 5)


def test_get_today_plan_brief_tool_returns_training_and_nutrition():
    db = MagicMock()
    db.get_active_plan.return_value = make_active_plan()

    tool = create_get_today_plan_brief_tool(db, "user@test.com")
    result = tool.invoke({})

    assert "Push" in result
    assert "3000" in result
