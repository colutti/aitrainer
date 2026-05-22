from datetime import date
from unittest.mock import MagicMock

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
    WeeklyScheduleItem,
)
from src.repositories.plan_repository import PlanRepository
from src.services.plan_service import build_plan_from_create_input


def make_plan():
    payload = PlanCreateInput(
        title="Plano Mestre",
        goal=PlanGoal(
            primary_goal="fat_loss",
            outcome_summary="Chegar a 15% de gordura",
            success_metrics=[
                SuccessMetric(
                    metric_name="body_fat_pct",
                    target_value=15,
                    unit="%",
                    direction="decrease",
                    deadline=date(2026, 9, 1),
                )
            ],
        ),
        timeline=PlanTimeline(
            start_date=date(2026, 4, 23),
            target_date=date(2026, 9, 1),
            review_cadence_days=14,
            current_phase="deficit",
        ),
        user_context=PlanUserContext(
            training_days_available=["monday"],
            session_duration_min=60,
            constraints=[],
            preferences=[],
            available_equipment=["barra"],
        ),
        training=PlanTraining(
            split_name="upper_lower",
            frequency_per_week=1,
            session_duration_min=60,
            routines=[
                TrainingRoutine(
                    id="upper_a",
                    name="Upper A",
                    exercises=[
                        TrainingExercise(
                            name="Supino",
                            sets=4,
                            rep_range=RepRange(min_reps=6, max_reps=8),
                            intensity=IntensityPrescription(prescription_type="rpe", target="8"),
                            progression_rule=ProgressionRule(
                                method="double_progression",
                                increase_when="bater topo da faixa",
                                hold_when="meio da faixa",
                                deload_when="regredir por 2 semanas",
                            ),
                        )
                    ],
                )
            ],
            weekly_schedule=[
                WeeklyScheduleItem(day="monday", routine_id="upper_a", focus="upper", type="training")
            ],
        ),
        nutrition=PlanNutrition(
            daily_targets=NutritionDailyTargets(
                calories_kcal=2200,
                protein_g=180,
                carbs_g=200,
                fat_g=70,
            ),
            strategy="deficit moderado",
            adherence_target_pct=80,
        ),
        alignment=PlanAlignment(
            training_nutrition_rationale="Deficit moderado",
            energy_strategy="deficit",
            recovery_assumptions=[],
            conflict_rules=[ConflictRule(trigger="fadiga", action="revisar volume")],
        ),
        tracking=PlanTracking(
            workout_adherence_target_pct=80,
            nutrition_adherence_target_pct=80,
            progress_markers=[ProgressMarker(name="aderencia", source="manual", target_summary="80%+")],
            review_questions=["Tudo coerente?"],
        ),
    )
    return build_plan_from_create_input("user@test.com", payload)


def _build_repo_with_collections() -> tuple[PlanRepository, MagicMock, MagicMock]:
    mock_db = MagicMock()
    mock_plans = MagicMock()
    mock_discovery = MagicMock()

    def get_collection(name: str):
        if name == "plans":
            return mock_plans
        if name == "plan_discovery_states":
            return mock_discovery
        raise KeyError(name)

    mock_db.__getitem__.side_effect = get_collection
    return PlanRepository(mock_db), mock_plans, mock_discovery


def test_save_plan_upserts_singleton_document():
    repo, collection, _ = _build_repo_with_collections()
    plan = make_plan()
    collection.find_one_and_update.return_value = {"_id": "mongo_plan_1", **plan.model_dump()}

    plan_id = repo.save_plan(plan)

    assert plan_id == "mongo_plan_1"
    collection.find_one_and_update.assert_called_once()
    collection.delete_many.assert_called_once()


def test_save_plan_serializes_date_fields_for_mongo():
    repo, collection, _ = _build_repo_with_collections()
    plan = make_plan()
    collection.find_one_and_update.return_value = {"_id": "mongo_plan_1"}

    repo.save_plan(plan)

    payload = collection.find_one_and_update.call_args.args[1]["$set"]
    assert payload["timeline"]["start_date"] == "2026-04-23"
    assert payload["timeline"]["target_date"] == "2026-09-01"
    assert payload["goal"]["success_metrics"][0]["deadline"] == "2026-09-01"


def test_get_plan_returns_latest_by_updated_at():
    repo, collection, _ = _build_repo_with_collections()
    plan = make_plan()
    collection.find_one.return_value = {"_id": "mongo_plan_1", **plan.model_dump()}

    loaded = repo.get_plan("user@test.com")

    assert loaded is not None
    assert loaded.title == "Plano Mestre"
    collection.find_one.assert_called_once()


def test_save_and_clear_discovery_roundtrip():
    repo, _, discovery_collection = _build_repo_with_collections()
    discovery = PlanDiscoveryState(
        user_email="user@test.com",
        goal_primary="fat_loss",
        missing_fields=["target_date"],
    )
    discovery_collection.find_one_and_update.return_value = {"_id": "discovery_1", **discovery.model_dump()}

    discovery_id = repo.save_discovery(discovery)
    repo.clear_discovery("user@test.com")

    assert discovery_id == "discovery_1"
    discovery_collection.find_one_and_update.assert_called_once()
    discovery_collection.delete_one.assert_called_once_with({"user_email": "user@test.com"})


def test_save_discovery_serializes_date_fields_for_mongo():
    repo, _, discovery_collection = _build_repo_with_collections()
    discovery = PlanDiscoveryState(
        user_email="user@test.com",
        goal_primary="fat_loss",
        goal_summary="Secar",
        target_date=date(2026, 9, 1),
        training_days_available=["monday"],
        session_duration_min=60,
        constraints=["nenhuma"],
        preferences=["academia"],
        available_equipment=["barra"],
        metabolism_confirmed=True,
        missing_fields=[],
    )
    discovery_collection.find_one_and_update.return_value = {"_id": "discovery_1"}

    repo.save_discovery(discovery)

    payload = discovery_collection.find_one_and_update.call_args.args[1]["$set"]
    assert payload["target_date"] == "2026-09-01"
