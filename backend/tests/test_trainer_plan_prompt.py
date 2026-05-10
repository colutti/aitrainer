from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.api.models.plan import (
    NutritionDailyTargets,
    NutritionStrategy,
    PlanCurrentSummary,
    PlanGoal,
    PlanPromptContext,
    PlanStrategy,
    PlanTimeline,
    TrainingExercise,
    TrainingProgram,
    TrainingRoutine,
    UserPlan,
    WeeklyScheduleItem,
)
from src.api.models.trainer_profile import TrainerProfile
from src.api.models.user_profile import UserProfile
from src.services.trainer import AITrainerBrain


now = datetime.now(timezone.utc)


def make_plan() -> UserPlan:
    return UserPlan(
        user_email="test@test.com",
        title="Plano Atual",
        goal=PlanGoal(
            primary="build_muscle",
            objective_summary="ganhar massa",
        ),
        timeline=PlanTimeline(
            start_date=datetime(2026, 4, 19, tzinfo=timezone.utc),
            target_date=datetime(2026, 6, 19, tzinfo=timezone.utc),
            review_cadence="semanal",
        ),
        strategy=PlanStrategy(
            rationale="superavit leve",
            adaptation_policy="approval_required",
        ),
        nutrition_strategy=NutritionStrategy(
            daily_targets=NutritionDailyTargets(
                calories=3000, protein_g=180, carbs_g=300, fat_g=90,
            ),
        ),
        training_program=TrainingProgram(
            split_name="push_pull_legs",
            frequency_per_week=5,
            session_duration_min=60,
            routines=[
                TrainingRoutine(
                    id="push_a",
                    name="Push A",
                    exercises=[
                        TrainingExercise(
                            name="Supino Reto", sets=4, reps="6-8", load_guidance="RPE 8",
                        ),
                    ],
                ),
            ],
            weekly_schedule=[
                WeeklyScheduleItem(day="monday", routine_id="push_a", focus="push"),
            ],
        ),
        current_summary=PlanCurrentSummary(
            active_focus="consistencia",
            rationale="executar bloco base",
            next_review="2026-05-15",
        ),
    )


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
    mock_db.get_plan.return_value = make_plan()

    async def mock_stream_with_tools(**_kwargs):
        yield "ok"

    mock_llm.stream_with_tools = mock_stream_with_tools

    brain = AITrainerBrain(database=mock_db, llm_client=mock_llm, qdrant_client=mock_qdrant)

    build_input_data_spy = MagicMock(
        return_value={
            "chat_history": [],
            "user_message": "<msg>oi</msg>",
            "agenda_section": "",
            "plan_section": "Plano mestre ativo: Plano Atual",
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

    chunks = []
    async for chunk in brain.send_message_ai("test@test.com", "oi"):
        chunks.append(chunk)

    assert "ok" in "".join(chunks)
    assert build_input_data_spy.call_count == 1
    plan_snapshot = build_input_data_spy.call_args.kwargs.get("plan_snapshot")
    assert isinstance(plan_snapshot, PlanPromptContext)
    assert plan_snapshot.title == "Plano Atual"
    assert plan_snapshot.goal_primary == "build_muscle"
