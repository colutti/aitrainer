from datetime import datetime
from unittest.mock import MagicMock

from src.api.models.plan import ActivePlan, PlanStatus
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
                {"date": "2026-04-19", "status": "planned", "training": {"title": "Push"}},
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
    assert context.adherence_7d is not None
    assert context.adherence_7d.nutrition_percent == 0
    assert context.adherence_7d.training_percent == 0
    assert context.weight_trend_weekly is not None
    assert context.weight_trend_weekly.value_kg_per_week == 0.0


def test_build_plan_snapshot_context_uses_latest_session_not_historic_pr():
    db = MagicMock()
    db.get_workout_logs.return_value = [
        {
            "date": datetime(2026, 4, 18, 8, 0, 0),
            "exercises": [
                {"name": "Supino reto", "reps_per_set": [8, 8], "weights_per_set": [80.0, 80.0]}
            ],
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


def test_build_plan_snapshot_context_matches_name_variation_with_suffix():
    db = MagicMock()
    plan = make_plan()
    plan.execution.today_training = {
        "title": "Push",
        "session": {
            "exercises": [
                {"name": "Supino Reto Barra", "sets": 3, "reps": "8-10", "load_guidance": "RPE 8"},
            ]
        },
    }
    db.get_workout_logs.return_value = [
        {
            "date": datetime(2026, 4, 18, 8, 0, 0),
            "exercises": [{"name": "Supino Reto", "reps_per_set": [8], "weights_per_set": [90.0]}],
        }
    ]
    db.get_nutrition_logs_by_date_range.return_value = []

    context = build_plan_snapshot_context(
        database=db,
        user_email="user@test.com",
        plan=plan,
        metabolism_data={"weight_change_per_week": -0.2},
        now=datetime(2026, 4, 19, 10, 0, 0),
    )

    assert len(context.today_training_context) == 1
    assert context.today_training_context[0].exercise_name == "Supino Reto Barra"
    assert context.today_training_context[0].last_load_kg == 90.0


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


def test_build_plan_snapshot_context_ignores_zero_weights_and_outdated_sessions():
    db = MagicMock()
    db.get_workout_logs.return_value = [
        {
            "date": datetime(2026, 1, 1, 8, 0, 0),
            "exercises": [{"name": "Supino Reto", "reps_per_set": [5], "weights_per_set": [120.0]}],
        },
        {
            "date": datetime(2026, 4, 18, 8, 0, 0),
            "exercises": [{"name": "Supino Reto", "reps_per_set": [8], "weights_per_set": [0.0]}],
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
    assert supino.last_load_kg is None


def test_build_plan_snapshot_context_deduplicates_nutrition_days():
    db = MagicMock()
    db.get_workout_logs.return_value = []
    db.get_nutrition_logs_by_date_range.return_value = [
        {"date": datetime(2026, 4, 19, 12, 0, 0)},
        {"date": datetime(2026, 4, 19, 18, 0, 0)},
        {"date": datetime(2026, 4, 18, 12, 0, 0)},
    ]

    context = build_plan_snapshot_context(
        database=db,
        user_email="user@test.com",
        plan=make_plan(),
        metabolism_data={},
        now=datetime(2026, 4, 19, 10, 0, 0),
    )

    assert context.adherence_7d is not None
    assert context.adherence_7d.nutrition_percent == 29
    assert context.weight_trend_weekly is None


def test_build_plan_snapshot_context_supports_loose_name_normalization():
    db = MagicMock()
    db.get_workout_logs.return_value = [
        {
            "date": datetime(2026, 4, 18, 8, 0, 0),
            "exercises": [
                {"name": "  supino   reto ", "reps_per_set": [8], "weights_per_set": [82.0]},
            ],
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
    assert supino.last_load_kg == 82.0


def test_build_plan_snapshot_context_matches_accented_name_variation():
    db = MagicMock()
    plan = make_plan()
    plan.execution.today_training = {
        "title": "Pull",
        "session": {
            "exercises": [
                {"name": "Remada Curvada", "sets": 4, "reps": "8-10", "load_guidance": "RPE 8"},
            ]
        },
    }
    plan.execution.upcoming_days = []
    db.get_workout_logs.return_value = [
        {
            "date": datetime(2026, 4, 18, 8, 0, 0),
            "exercises": [{"name": "Remáda Curvada", "reps_per_set": [10], "weights_per_set": [70.0]}],
        }
    ]
    db.get_nutrition_logs_by_date_range.return_value = []

    context = build_plan_snapshot_context(
        database=db,
        user_email="user@test.com",
        plan=plan,
        metabolism_data={"weight_change_per_week": -0.2},
        now=datetime(2026, 4, 19, 10, 0, 0),
    )

    assert len(context.today_training_context) == 1
    assert context.today_training_context[0].last_load_kg == 70.0


def test_build_plan_snapshot_context_returns_none_when_training_window_has_no_planned_days():
    db = MagicMock()
    plan = make_plan()
    plan.execution.upcoming_days = []
    db.get_workout_logs.return_value = []
    db.get_nutrition_logs_by_date_range.return_value = []

    context = build_plan_snapshot_context(
        database=db,
        user_email="user@test.com",
        plan=plan,
        metabolism_data={"weight_change_per_week": 0.0},
        now=datetime(2026, 4, 19, 10, 0, 0),
    )
    assert context.adherence_7d is not None
    assert context.adherence_7d.training_percent is None


def test_build_plan_snapshot_context_uses_today_training_exercises_from_upcoming_days():
    db = MagicMock()
    plan = make_plan()
    plan.execution.today_training = {
        "title": "Push",
        "session": {
            "exercises": [
                {"name": "Supino Reto", "sets": 3, "reps": "8-10", "load_guidance": "RPE 8"},
            ]
        },
    }
    plan.execution.upcoming_days = [
        {
            "date": "2026-04-19",
            "label": "Hoje",
            "status": "planned",
            "training": {
                "title": "Pull",
                "session": {
                    "exercises": [
                        {"name": "Remada Curvada", "sets": 4, "reps": "8-10", "load_guidance": "RPE 8"},
                    ]
                },
            },
            "nutrition": "2400 kcal",
        }
    ]
    db.get_workout_logs.return_value = []
    db.get_nutrition_logs_by_date_range.return_value = []

    context = build_plan_snapshot_context(
        database=db,
        user_email="user@test.com",
        plan=plan,
        metabolism_data={"weight_change_per_week": -0.1},
        now=datetime(2026, 4, 19, 10, 0, 0),
    )

    assert len(context.today_training_context) == 1
    assert context.today_training_context[0].exercise_name == "Remada Curvada"
