"""Tests for the get_plan_training_program tool."""

from datetime import date
from unittest.mock import MagicMock

from src.api.models.plan import (
    ConflictRule,
    IntensityPrescription,
    NutritionDailyTargets,
    PlanAlignment,
    PlanCreateInput,
    PlanGoal,
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
from src.services.plan_service import build_plan_from_create_input
from src.services.plan_training_tools import create_get_plan_training_program_tool


def make_plan_with_training():
    payload = PlanCreateInput(
        title="Plano Mestre",
        goal=PlanGoal(
            primary_goal="muscle_gain",
            outcome_summary="Ganhar massa",
            success_metrics=[
                SuccessMetric(
                    metric_name="peso",
                    target_value=75,
                    unit="kg",
                    direction="increase",
                    deadline=date(2026, 8, 10),
                )
            ],
        ),
        timeline=PlanTimeline(
            start_date=date(2026, 4, 19),
            target_date=date(2026, 8, 10),
            review_cadence_days=7,
            current_phase="acumulacao",
        ),
        user_context=PlanUserContext(
            training_days_available=["monday", "tuesday"],
            session_duration_min=60,
            constraints=["nenhuma"],
            preferences=["academia"],
            available_equipment=["barra"],
        ),
        training=PlanTraining(
            split_name="PPL-UL",
            frequency_per_week=2,
            session_duration_min=60,
            routines=[
                TrainingRoutine(
                    id="push",
                    name="Push",
                    exercises=[
                        TrainingExercise(
                            name="Supino reto com barra",
                            sets=4,
                            rep_range=RepRange(min_reps=8, max_reps=10),
                            intensity=IntensityPrescription(prescription_type="rpe", target="RPE 8"),
                            progression_rule=ProgressionRule(
                                method="double_progression",
                                increase_when="bater topo da faixa",
                                hold_when="ficar no meio da faixa",
                                deload_when="regredir por 2 semanas",
                            ),
                        ),
                        TrainingExercise(
                            name="Elevacao lateral",
                            sets=3,
                            rep_range=RepRange(min_reps=12, max_reps=15),
                            intensity=IntensityPrescription(prescription_type="rpe", target="RPE 7"),
                            progression_rule=ProgressionRule(
                                method="volume_progression",
                                increase_when="completar volume",
                                hold_when="fadiga moderada",
                                deload_when="fadiga alta",
                            ),
                        ),
                    ],
                ),
                TrainingRoutine(
                    id="pull",
                    name="Pull",
                    exercises=[
                        TrainingExercise(
                            name="Puxada alta",
                            sets=4,
                            rep_range=RepRange(min_reps=8, max_reps=10),
                            intensity=IntensityPrescription(prescription_type="rpe", target="RPE 8"),
                            progression_rule=ProgressionRule(
                                method="double_progression",
                                increase_when="bater topo da faixa",
                                hold_when="ficar no meio da faixa",
                                deload_when="regredir por 2 semanas",
                            ),
                        ),
                    ],
                ),
            ],
            weekly_schedule=[
                WeeklyScheduleItem(day="monday", routine_id="push", focus="push", type="training"),
                WeeklyScheduleItem(day="tuesday", routine_id="pull", focus="pull", type="training"),
            ],
        ),
        nutrition=PlanNutrition(
            daily_targets=NutritionDailyTargets(
                calories_kcal=2600,
                protein_g=160,
                carbs_g=315,
                fat_g=75,
            ),
            strategy="superavit leve",
            adherence_target_pct=85,
        ),
        alignment=PlanAlignment(
            training_nutrition_rationale="Superavit leve para hipertrofia.",
            energy_strategy="surplus",
            recovery_assumptions=["dormir 7h"],
            conflict_rules=[ConflictRule(trigger="queda de performance", action="revisar recuperacao")],
        ),
        tracking=PlanTracking(
            workout_adherence_target_pct=85,
            nutrition_adherence_target_pct=80,
            progress_markers=[ProgressMarker(name="carga", source="workouts", target_summary="subir")],
            review_questions=["Tudo coerente?"],
        ),
    )
    return build_plan_from_create_input("test@test.com", payload)


class TestGetPlanTrainingProgram:
    def test_returns_training_program_when_plan_exists(self):
        mock_db = MagicMock()
        mock_db.get_plan.return_value = make_plan_with_training()
        tool = create_get_plan_training_program_tool(mock_db, "test@test.com")

        result = tool.invoke({"format": "text"})

        assert "PPL-UL" in result
        assert "Push" in result
        assert "Pull" in result
        assert "Supino reto com barra" in result
        assert "4x8-10" in result
        assert "RPE 8" in result
        assert "Segunda" in result
        assert "Terca" in result

    def test_returns_fallback_when_no_plan(self):
        mock_db = MagicMock()
        mock_db.get_plan.return_value = None
        tool = create_get_plan_training_program_tool(mock_db, "test@test.com")

        result = tool.invoke({"format": "text"})

        assert "Nenhum programa de treino salvo no plano" in result

    def test_returns_json_when_format_json(self):
        mock_db = MagicMock()
        mock_db.get_plan.return_value = make_plan_with_training()
        tool = create_get_plan_training_program_tool(mock_db, "test@test.com")

        result = tool.invoke({"format": "json"})

        import json

        data = json.loads(result)
        assert data["split_name"] == "PPL-UL"
        assert len(data["routines"]) == 2
        assert data["routines"][0]["name"] == "Push"
        assert data["routines"][0]["exercises"][0]["name"] == "Supino reto com barra"
        assert "nutrition" not in data

    def test_does_not_expose_nutrition_or_goal_data(self):
        mock_db = MagicMock()
        mock_db.get_plan.return_value = make_plan_with_training()
        tool = create_get_plan_training_program_tool(mock_db, "test@test.com")

        result = tool.invoke({"format": "json"})

        import json

        data = json.loads(result)
        assert "goal" not in data
        assert "nutrition" not in data
        assert "alignment" not in data
        assert "timeline" not in data

    def test_invoke_uses_database(self):
        mock_db = MagicMock()
        mock_db.get_plan.return_value = None
        tool = create_get_plan_training_program_tool(mock_db, "user@test.com")

        tool.invoke({})

        mock_db.get_plan.assert_called_once_with("user@test.com")
