from unittest.mock import MagicMock

import pytest

from src.api.models.plan import (
    ActivePlan,
    PlanSnapshot,
    PlanSnapshotWeightTrend,
    PlanStatus,
)
from src.api.models.trainer_profile import TrainerProfile
from src.api.models.user_profile import UserProfile
from src.services.trainer import AITrainerBrain


@pytest.mark.asyncio
async def test_send_message_ai_injects_plan_snapshot_into_prompt_builder(monkeypatch):
    mock_db = MagicMock()
    mock_llm = MagicMock()
    mock_qdrant = None

    profile = UserProfile(
        email="test@test.com",
        gender="Masculino",
        age=30,
        weight=80,
        height=175,
        goal="ganhar massa",
        goal_type="gain",
        weekly_rate=0.5,
    )
    trainer_profile = TrainerProfile(user_email="test@test.com", trainer_type="atlas")

    mock_db.get_user_profile.return_value = profile
    mock_db.get_trainer_profile.return_value = trainer_profile
    mock_db.get_window_memory.return_value.load_memory_variables.return_value = {
        "chat_history": []
    }
    mock_db.get_active_plan.return_value = ActivePlan(
        user_email="test@test.com",
        status=PlanStatus.ACTIVE,
        title="Plano Atual",
        objective_summary="ganhar massa",
        start_date="2026-04-19T00:00:00",
        end_date="2026-06-19T00:00:00",
        version=1,
        strategy={
            "primary_goal": "gain_muscle",
            "success_criteria": ["volume"],
            "constraints": [],
            "coaching_rationale": "superavit leve",
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
            "checkpoints": [],
            "adherence_snapshot": {"training": "ok", "nutrition": "ok"},
            "progress_snapshot": {"status": "on_track"},
            "last_ai_assessment": None,
            "last_user_acknowledgement": None,
        },
        governance={"change_reason": None, "approval_request": None},
    )

    async def mock_stream_with_tools(**_kwargs):
        yield "ok"

    mock_llm.stream_with_tools = mock_stream_with_tools

    brain = AITrainerBrain(database=mock_db, llm_client=mock_llm, qdrant_client=mock_qdrant)

    build_input_data_spy = MagicMock(
        return_value={
            "chat_history": [],
            "user_message": "<msg>oi</msg>",
            "agenda_section": "",
            "plan_section": "Plano ativo: Plano Atual",
            "current_date": "2026-04-19",
        }
    )
    monkeypatch.setattr(brain.prompt_builder, "build_input_data", build_input_data_spy)
    monkeypatch.setattr(brain.prompt_builder, "get_prompt_template", MagicMock(return_value=MagicMock()))
    monkeypatch.setattr(brain, "get_tools", MagicMock(return_value=[]))
    monkeypatch.setattr(
        "src.services.trainer.EventRepository",
        MagicMock(return_value=MagicMock(get_active_events=MagicMock(return_value=[]))),
    )
    monkeypatch.setattr(
        "src.services.trainer.AdaptiveTDEEService",
        MagicMock(
            return_value=MagicMock(
                calculate_tdee=MagicMock(return_value={"weight_change_per_week": -0.2})
            )
        ),
    )
    monkeypatch.setattr(
        "src.services.trainer.build_plan_snapshot_context",
        MagicMock(
            return_value=MagicMock(
                today_training_context=[],
                adherence_7d=None,
                weight_trend_weekly=PlanSnapshotWeightTrend(
                    value_kg_per_week=-0.2,
                    source="adaptive_tdee",
                ),
            )
        ),
    )

    chunks = []
    async for chunk in brain.send_message_ai("test@test.com", "oi"):
        chunks.append(chunk)

    assert "ok" in "".join(chunks)
    assert build_input_data_spy.call_count == 1
    plan_snapshot = build_input_data_spy.call_args.kwargs.get("plan_snapshot")
    assert isinstance(plan_snapshot, PlanSnapshot)
    assert plan_snapshot.title == "Plano Atual"
    assert plan_snapshot.weight_trend_weekly is not None
    assert plan_snapshot.weight_trend_weekly.value_kg_per_week == -0.2
