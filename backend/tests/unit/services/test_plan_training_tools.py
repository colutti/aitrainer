"""Tests for the get_plan_training_program tool."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.api.models.plan import (
    NutritionDailyTargets,
    NutritionStrategy,
    PlanCurrentSummary,
    PlanGoal,
    PlanStrategy,
    PlanTimeline,
    TrainingExercise,
    TrainingProgram,
    TrainingRoutine,
    UserPlan,
    WeeklyScheduleItem,
)
from src.services.plan_training_tools import create_get_plan_training_program_tool


def make_plan_with_training() -> UserPlan:
    return UserPlan(
        user_email="test@test.com",
        title="Plano Mestre",
        goal=PlanGoal(
            primary="build_muscle",
            objective_summary="Ganhar massa",
        ),
        timeline=PlanTimeline(
            start_date=datetime(2026, 4, 19, tzinfo=timezone.utc),
            target_date=datetime(2026, 8, 10, tzinfo=timezone.utc),
            review_cadence="semanal",
        ),
        strategy=PlanStrategy(
            rationale="superavit leve",
            adaptation_policy="approval_required",
        ),
        nutrition_strategy=NutritionStrategy(
            daily_targets=NutritionDailyTargets(
                calories=2600, protein_g=160, carbs_g=315, fat_g=75,
            ),
        ),
        training_program=TrainingProgram(
            split_name="PPL-UL",
            frequency_per_week=2,
            session_duration_min=60,
            routines=[
                TrainingRoutine(
                    id="push",
                    name="Push",
                    exercises=[
                        TrainingExercise(
                            name="Supino reto com barra", sets=4, reps="8-10",
                            load_guidance="RPE 8",
                        ),
                        TrainingExercise(
                            name="Elevacao lateral", sets=3, reps="12-15",
                            load_guidance="RPE 7",
                        ),
                    ],
                ),
                TrainingRoutine(
                    id="pull",
                    name="Pull",
                    exercises=[
                        TrainingExercise(
                            name="Puxada alta", sets=4, reps="8-10",
                            load_guidance="RPE 8",
                        ),
                    ],
                ),
            ],
            weekly_schedule=[
                WeeklyScheduleItem(day="monday", routine_id="push", focus="push", type="training"),
                WeeklyScheduleItem(day="tuesday", routine_id="pull", focus="pull", type="training"),
            ],
        ),
        current_summary=PlanCurrentSummary(
            active_focus="consistencia",
            rationale="executar bloco base",
            next_review="2026-05-15",
        ),
    )


class TestGetPlanTrainingProgram:
    """Tests for the get_plan_training_program tool."""

    def test_returns_training_program_when_plan_exists(self):
        """Should return formatted training program when user has a plan."""
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
        """Should return fallback message when user has no plan."""
        mock_db = MagicMock()
        mock_db.get_plan.return_value = None
        tool = create_get_plan_training_program_tool(mock_db, "test@test.com")

        result = tool.invoke({"format": "text"})

        assert "Nenhum programa de treino salvo no plano" in result

    def test_returns_json_when_format_json(self):
        """Should return JSON when format='json'."""
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
        # Should NOT include nutrition or goal data
        assert "nutrition_strategy" not in data

    def test_does_not_expose_nutrition_or_goal_data(self):
        """Should not return nutrition, goal, strategy or other non-training fields."""
        mock_db = MagicMock()
        mock_db.get_plan.return_value = make_plan_with_training()
        tool = create_get_plan_training_program_tool(mock_db, "test@test.com")

        result = tool.invoke({"format": "json"})

        import json
        data = json.loads(result)
        assert "goal" not in data
        assert "nutrition_strategy" not in data
        assert "strategy" not in data
        assert "checkpoints" not in data
        assert "timeline" not in data
        assert "current_summary" not in data

    def test_invoke_uses_database(self):
        """Should call database.get_plan with correct user_email."""
        mock_db = MagicMock()
        mock_db.get_plan.return_value = None
        tool = create_get_plan_training_program_tool(mock_db, "user@test.com")

        tool.invoke({})

        mock_db.get_plan.assert_called_once_with("user@test.com")
