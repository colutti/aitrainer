from datetime import date
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.api.main import app
from src.core.deps import get_mongo_database
from src.services.auth import verify_token
from src.api.models.plan import (
    ConflictRule,
    IntensityPrescription,
    NutritionDailyTargets,
    PlanAlignment,
    PlanCreateInput,
    PlanDiscoveryState,
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
    UserPlan,
    WeeklyScheduleItem,
)
from src.services.plan_service import build_plan_from_create_input


client = TestClient(app)


def make_create_input() -> PlanCreateInput:
    return PlanCreateInput(
        title="Plano Mestre",
        goal=PlanGoal(
            primary_goal="muscle_gain",
            outcome_summary="Ganhar massa com superavit controlado",
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
            start_date=date(2026, 5, 1),
            target_date=date(2026, 8, 1),
            review_cadence_days=7,
            current_phase="acumulacao",
        ),
        user_context=PlanUserContext(
            training_days_available=["monday", "thursday"],
            session_duration_min=60,
            constraints=["nenhuma"],
            preferences=["academia"],
            available_equipment=["barra"],
        ),
        training=PlanTraining(
            split_name="upper_lower",
            frequency_per_week=2,
            session_duration_min=60,
            routines=[
                TrainingRoutine(
                    id="upper_a",
                    name="Upper A",
                    exercises=[
                        TrainingExercise(
                            name="Supino Reto",
                            sets=4,
                            rep_range=RepRange(min_reps=6, max_reps=8),
                            intensity=IntensityPrescription(
                                prescription_type="rpe",
                                target="8",
                            ),
                            progression_rule=ProgressionRule(
                                method="double_progression",
                                increase_when="bater topo da faixa",
                                hold_when="ficar no meio da faixa",
                                deload_when="regredir por 2 semanas",
                            ),
                        )
                    ],
                ),
                TrainingRoutine(
                    id="lower_a",
                    name="Lower A",
                    exercises=[
                        TrainingExercise(
                            name="Agachamento",
                            sets=4,
                            rep_range=RepRange(min_reps=5, max_reps=8),
                            intensity=IntensityPrescription(
                                prescription_type="rpe",
                                target="8",
                            ),
                            progression_rule=ProgressionRule(
                                method="linear_load",
                                increase_when="completar volume com tecnica boa",
                                hold_when="tecnica instavel",
                                deload_when="fadiga acumulada por 2 semanas",
                            ),
                        )
                    ],
                ),
            ],
            weekly_schedule=[
                WeeklyScheduleItem(day="monday", routine_id="upper_a", focus="upper", type="training"),
                WeeklyScheduleItem(day="thursday", routine_id="lower_a", focus="lower", type="training"),
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
            progress_markers=[ProgressMarker(name="carga no supino", source="workouts", target_summary="subir carga ou reps")],
            review_questions=["A recuperacao esta coerente?"],
        ),
    )


def make_plan() -> UserPlan:
    return build_plan_from_create_input("test@example.com", make_create_input())


def override_db(mock_db: MagicMock) -> None:
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db


def test_get_plan_returns_plan_payload():
    mock_db = MagicMock()
    mock_db.get_plan.return_value = make_plan()
    override_db(mock_db)

    try:
        response = client.get("/plan")
        assert response.status_code == 200
        assert response.json()["title"] == "Plano Mestre"
    finally:
        app.dependency_overrides.clear()


def test_get_plan_status_returns_no_plan():
    mock_db = MagicMock()
    mock_db.get_plan.return_value = None
    mock_db.get_plan_discovery.return_value = None
    override_db(mock_db)

    try:
        response = client.get("/plan/status")
        assert response.status_code == 200
        assert response.json()["status"] == "NO_PLAN"
        assert "goal_primary" in response.json()["missing_fields"]
    finally:
        app.dependency_overrides.clear()


def test_create_plan_from_discovery_requires_complete_discovery():
    mock_db = MagicMock()
    mock_db.get_plan_discovery.return_value = None
    override_db(mock_db)

    try:
        response = client.post("/plan/create-from-discovery", json=make_create_input().model_dump(mode="json"))
        assert response.status_code == 422
        assert "Discovery incompleto" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_create_plan_from_discovery_saves_plan_and_clears_draft():
    mock_db = MagicMock()
    mock_db.get_plan_discovery.return_value = PlanDiscoveryState(
        user_email="test@example.com",
        goal_primary="muscle_gain",
        goal_summary="Ganhar massa",
        target_date=date(2026, 8, 1),
        training_days_available=["monday", "thursday"],
        session_duration_min=60,
        constraints=["nenhuma"],
        preferences=["academia"],
        available_equipment=["barra"],
        metabolism_confirmed=True,
        missing_fields=[],
    )
    mock_db.save_plan.return_value = "plan_1"
    override_db(mock_db)

    try:
        response = client.post("/plan/create-from-discovery", json=make_create_input().model_dump(mode="json"))
        assert response.status_code == 200
        assert response.json()["id"] == "plan_1"
        mock_db.clear_plan_discovery.assert_called_once_with("test@example.com")
    finally:
        app.dependency_overrides.clear()


def test_patch_plan_section_updates_active_plan():
    mock_db = MagicMock()
    mock_db.get_plan.return_value = make_plan()
    mock_db.save_plan.return_value = "plan_2"
    override_db(mock_db)

    payload = {
        "section": "nutrition",
        "nutrition": {
            "daily_targets": {
                "calories_kcal": 2800,
                "protein_g": 170,
                "carbs_g": 330,
                "fat_g": 80,
            },
            "strategy": "superavit moderado",
            "adherence_target_pct": 85,
        },
    }

    try:
        response = client.patch("/plan/section", json=payload)
        assert response.status_code == 200
        assert response.json()["id"] == "plan_2"
    finally:
        app.dependency_overrides.clear()


def test_patch_plan_section_rejects_missing_active_plan():
    mock_db = MagicMock()
    mock_db.get_plan.return_value = None
    override_db(mock_db)

    try:
        response = client.patch("/plan/section", json={"section": "tracking", "tracking": {
            "workout_adherence_target_pct": 85,
            "nutrition_adherence_target_pct": 80,
            "progress_markers": [{"name": "peso", "source": "body", "target_summary": "subir"}],
            "review_questions": ["Tudo coerente?"],
        }})
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_get_plan_view_returns_discovery_state_without_active_plan():
    mock_db = MagicMock()
    mock_db.get_plan.return_value = None
    mock_db.get_plan_discovery.return_value = PlanDiscoveryState(
        user_email="test@example.com",
        goal_primary="muscle_gain",
        missing_fields=["target_date"],
    )
    override_db(mock_db)

    try:
        response = client.get("/plan/view")
        assert response.status_code == 200
        assert response.json()["status"] == "DISCOVERY_IN_PROGRESS"
    finally:
        app.dependency_overrides.clear()
