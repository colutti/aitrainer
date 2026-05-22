from datetime import date
from unittest.mock import MagicMock

import pytest

from src.api.models.plan import (
    ConflictRule,
    IntensityPrescription,
    NutritionDailyTargets,
    PlanAlignment,
    PlanCreateInput,
    PlanGoal,
    PlanPromptContext,
    PlanNutrition,
    PlanTimeline,
    PlanTracking,
    PlanUserContext,
    ProgressMarker,
    ProgressionRule,
    RepRange,
    SuccessMetric,
    TrainingExercise,
    PlanTraining,
    TrainingRoutine,
    WeeklyScheduleItem,
)
from src.api.models.trainer_profile import TrainerProfile
from src.api.models.user_profile import UserProfile
from src.services.plan_service import build_plan_from_create_input
from src.services.trainer import AITrainerBrain


def make_plan():
    payload = PlanCreateInput(
        title="Plano Atual",
        goal=PlanGoal(
            primary_goal="muscle_gain",
            outcome_summary="Ganhar massa",
            success_metrics=[
                SuccessMetric(
                    metric_name="peso",
                    target_value=75,
                    unit="kg",
                    direction="increase",
                    deadline=date(2026, 8, 1),
                )
            ],
        ),
        timeline=PlanTimeline(
            start_date=date(2026, 4, 19),
            target_date=date(2026, 6, 19),
            review_cadence_days=7,
            current_phase="acumulacao",
        ),
        user_context=PlanUserContext(
            training_days_available=["monday"],
            session_duration_min=60,
            constraints=["nenhuma"],
            preferences=["academia"],
            available_equipment=["barra"],
        ),
        training=PlanTraining(
            split_name="push_pull_legs",
            frequency_per_week=1,
            session_duration_min=60,
            routines=[
                TrainingRoutine(
                    id="push_a",
                    name="Push A",
                    exercises=[
                        TrainingExercise(
                            name="Supino Reto",
                            sets=4,
                            rep_range=RepRange(min_reps=6, max_reps=8),
                            intensity=IntensityPrescription(prescription_type="rpe", target="8"),
                            progression_rule=ProgressionRule(
                                method="double_progression",
                                increase_when="bater topo da faixa",
                                hold_when="ficar no meio da faixa",
                                deload_when="regredir por 2 semanas",
                            ),
                        )
                    ],
                )
            ],
            weekly_schedule=[
                WeeklyScheduleItem(day="monday", routine_id="push_a", focus="push", type="training"),
            ],
        ),
        nutrition=PlanNutrition(
            daily_targets=NutritionDailyTargets(
                calories_kcal=3000,
                protein_g=180,
                carbs_g=300,
                fat_g=90,
            ),
            strategy="superavit leve",
            adherence_target_pct=85,
        ),
        alignment=PlanAlignment(
            training_nutrition_rationale="Superavit leve",
            energy_strategy="surplus",
            recovery_assumptions=["dormir 7h"],
            conflict_rules=[ConflictRule(trigger="queda de performance", action="revisar recuperacao")],
        ),
        tracking=PlanTracking(
            workout_adherence_target_pct=85,
            nutrition_adherence_target_pct=80,
            progress_markers=[ProgressMarker(name="carga no supino", source="workouts", target_summary="subir")],
            review_questions=["Tudo coerente?"],
        ),
    )
    return build_plan_from_create_input("test@test.com", payload)


@pytest.mark.asyncio
async def test_send_message_ai_injects_plan_snapshot_into_prompt_builder(monkeypatch):
    mock_db = MagicMock()
    mock_llm = MagicMock()

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
    mock_db.get_window_memory.return_value.load_memory_variables.return_value = {"chat_history": []}
    mock_db.get_plan.return_value = make_plan()
    mock_db.get_plan_discovery.return_value = None
    mock_db.get_workout_logs.return_value = []
    mock_db.get_nutrition_stats.return_value = MagicMock(total_logs=0)
    mock_db.get_weight_logs.return_value = []

    async def mock_stream_with_tools(**_kwargs):
        yield "ok"

    mock_llm.stream_with_tools = mock_stream_with_tools

    brain = AITrainerBrain(database=mock_db, llm_client=mock_llm, qdrant_client=None)

    build_input_data_spy = MagicMock(
        return_value={
            "chat_history": [],
            "user_message": "<msg>oi</msg>",
            "agenda_section": "",
            "plan_section": "PLAN_CONTEXT",
            "current_date": "2026-04-19",
            "runtime_context": {},
            "runtime_context_json": "{}",
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
        MagicMock(return_value=MagicMock(calculate_tdee=MagicMock(return_value={"weight_change_per_week": -0.2}))),
    )

    chunks = []
    async for chunk in brain.send_message_ai("test@test.com", "oi"):
        chunks.append(chunk)

    assert "ok" in "".join(chunks)
    plan_snapshot = build_input_data_spy.call_args.kwargs.get("plan_snapshot")
    assert isinstance(plan_snapshot, PlanPromptContext)
    assert plan_snapshot.status == "ACTIVE_PLAN"
    assert plan_snapshot.active_plan["title"] == "Plano Atual"
