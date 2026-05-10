from datetime import datetime, timezone
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.api.main import app
from src.core.deps import get_mongo_database
from src.services.auth import verify_token
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


client = TestClient(app)

now = datetime.now(timezone.utc)


def make_plan() -> UserPlan:
    return UserPlan(
        user_email="test@example.com",
        title="Plano Atual",
        goal=PlanGoal(primary="gain_muscle", objective_summary="Ganhar massa"),
        timeline=PlanTimeline(
            start_date=now,
            target_date=now,
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
            next_review="2026-06-01",
        ),
    )


def test_get_plan_returns_plan_payload():
    mock_db = MagicMock()
    mock_db.get_plan.return_value = make_plan()

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    try:
        response = client.get("/plan")
        assert response.status_code == 200
        assert response.json()["title"] == "Plano Atual"
    finally:
        app.dependency_overrides.clear()


def test_get_plan_returns_404_when_missing():
    mock_db = MagicMock()
    mock_db.get_plan.return_value = None

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    try:
        response = client.get("/plan")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_upsert_plan_creates_new_plan():
    mock_db = MagicMock()
    mock_db.get_latest_plan.return_value = None
    mock_db.get_plan.return_value = None
    mock_db.save_plan.return_value = "plan_1"

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    payload = {
        "title": "Plano Mestre",
        "change_reason": "initial_plan",
        "goal": {
            "primary": "lose_fat",
            "objective_summary": "Chegar a 15% BF",
        },
        "timeline": {
            "target_date": "2026-09-01T00:00:00",
            "review_cadence": "quinzenal",
        },
        "strategy": {
            "rationale": "Deficit moderado",
            "adaptation_policy": "ajustar por evidencia",
        },
        "nutrition_strategy": {
            "daily_targets": {
                "calories": 2200,
                "protein_g": 180,
                "carbs_g": 200,
                "fat_g": 70,
            },
        },
        "training_program": {
            "split_name": "push_pull_legs",
            "frequency_per_week": 5,
            "session_duration_min": 60,
            "routines": [
                {
                    "id": "push_a",
                    "name": "Push A",
                    "exercises": [
                        {"name": "Supino", "sets": 4, "reps": "6-8", "load_guidance": "RPE 8"},
                    ],
                }
            ],
            "weekly_schedule": [
                {"day": "monday", "routine_id": "push_a", "focus": "push"},
            ],
        },
        "current_summary": {
            "active_focus": "consistencia",
            "rationale": "executar bloco base",
            "next_review": "2026-09-15",
        },
    }

    try:
        response = client.post("/plan/upsert", json=payload)
        assert response.status_code == 200
        assert response.json()["id"] == "plan_1"
    finally:
        app.dependency_overrides.clear()


def test_upsert_plan_rejects_missing_required_fields():
    mock_db = MagicMock()
    mock_db.get_latest_plan.return_value = None

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    payload = {
        "title": "Plano Incompleto",
        "goal": {"primary": "lose_fat"},
        "timeline": {},
        "strategy": {},
        "nutrition_strategy": {},
        "training_program": {},
        "current_summary": {},
    }

    try:
        response = client.post("/plan/upsert", json=payload)
        assert response.status_code == 422
        assert "Plano incompleto" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_upsert_plan_rejects_missing_nutrition_targets():
    mock_db = MagicMock()
    mock_db.get_latest_plan.return_value = None

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    payload = {
        "title": "Plano Sem Nutricao",
        "goal": {
            "primary": "lose_fat",
            "objective_summary": "Emagrecer",
        },
        "timeline": {
            "target_date": "2026-09-01T00:00:00",
            "review_cadence": "semanal",
        },
        "strategy": {
            "rationale": "Deficit",
            "adaptation_policy": "ajustar",
        },
        "nutrition_strategy": {
            "daily_targets": {},
        },
        "training_program": {
            "split_name": "full_body",
            "frequency_per_week": 3,
            "session_duration_min": 45,
            "routines": [
                {
                    "id": "fb_a",
                    "name": "Full Body A",
                    "exercises": [
                        {"name": "Agachamento", "sets": 3, "reps": "8-10", "load_guidance": "RPE 7"},
                    ],
                }
            ],
            "weekly_schedule": [
                {"day": "monday", "routine_id": "fb_a", "focus": "full_body"},
            ],
        },
        "current_summary": {
            "active_focus": "base",
            "rationale": "inicio",
            "next_review": "2026-05-01",
        },
    }

    try:
        response = client.post("/plan/upsert", json=payload)
        assert response.status_code == 422
        assert "Plano incompleto" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_upsert_plan_updates_existing_plan():
    mock_db = MagicMock()
    mock_db.get_latest_plan.return_value = make_plan()
    mock_db.get_plan.return_value = make_plan()
    mock_db.save_plan.return_value = "plan_2"

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    payload = {
        "title": "Plano Atualizado",
        "change_reason": "review",
        "goal": {"primary": "lose_fat", "objective_summary": "Definir"},
        "timeline": {
            "target_date": "2026-12-01T00:00:00",
            "review_cadence": "mensal",
        },
        "strategy": {
            "rationale": "Deficit mais agressivo",
            "adaptation_policy": "ajustar quinzenalmente",
        },
        "nutrition_strategy": {
            "daily_targets": {
                "calories": 2000,
                "protein_g": 160,
                "carbs_g": 180,
                "fat_g": 60,
            },
        },
        "training_program": {
            "split_name": "upper_lower",
            "frequency_per_week": 4,
            "session_duration_min": 50,
            "routines": [
                {
                    "id": "push_a",
                    "name": "Push A",
                    "exercises": [
                        {"name": "Supino Inclinado", "sets": 4, "reps": "8-10", "load_guidance": "RPE 8"},
                    ],
                }
            ],
            "weekly_schedule": [
                {"day": "monday", "routine_id": "push_a", "focus": "push"},
            ],
        },
        "current_summary": {
            "active_focus": "intensidade",
            "rationale": "aumentar volume progressivo",
            "next_review": "2026-07-01",
        },
    }

    try:
        response = client.post("/plan/upsert", json=payload)
        assert response.status_code == 200
        assert response.json()["id"] == "plan_2"
    finally:
        app.dependency_overrides.clear()
