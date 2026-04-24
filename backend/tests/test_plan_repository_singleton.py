from datetime import datetime
from unittest.mock import MagicMock

from src.api.models.plan import UserPlan
from src.repositories.plan_repository import PlanRepository


def make_plan() -> UserPlan:
    return UserPlan(
        user_email="user@test.com",
        title="Plano Mestre",
        goal={
            "primary": "lose_fat",
            "objective_summary": "Chegar a 15% de gordura",
            "success_criteria": ["aderencia >= 80%"],
        },
        timeline={
            "start_date": datetime(2026, 4, 23),
            "target_date": datetime(2026, 9, 1),
            "review_cadence": "quinzenal",
        },
        strategy={
            "rationale": "deficit moderado",
            "adaptation_policy": "ajustes por evidencia",
            "constraints": [],
            "preferences": [],
            "current_risks": [],
        },
        nutrition_strategy={
            "daily_targets": {"calories": 2200, "protein_g": 180},
            "adherence_notes": [],
        },
        training_program={
            "split_name": "upper_lower",
            "frequency_per_week": 4,
            "session_duration_min": 60,
            "routines": [
                {
                    "id": "upper_a",
                    "name": "Upper A",
                    "exercises": [
                        {
                            "name": "Supino",
                            "sets": 4,
                            "reps": "6-8",
                            "load_guidance": "RPE 8",
                        }
                    ],
                }
            ],
            "weekly_schedule": [
                {
                    "day": "monday",
                    "routine_id": "upper_a",
                    "focus": "upper",
                    "type": "training",
                }
            ],
        },
        current_summary={
            "active_focus": "consistencia",
            "rationale": "executar 2 semanas base",
            "key_risks": [],
            "next_review": "2026-05-01",
        },
        checkpoints=[],
        change_reason="initial_plan",
    )


def _build_repo_with_collection() -> tuple[PlanRepository, MagicMock]:
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    return PlanRepository(mock_db), mock_collection


def test_save_plan_upserts_singleton_document():
    repo, collection = _build_repo_with_collection()
    plan = make_plan()

    collection.find_one_and_update.return_value = {"_id": "mongo_plan_1", **plan.model_dump()}

    plan_id = repo.save_plan(plan)

    assert plan_id == "mongo_plan_1"
    collection.find_one_and_update.assert_called_once()
    collection.delete_many.assert_called_once()


def test_get_plan_returns_latest_by_updated_at():
    repo, collection = _build_repo_with_collection()
    plan = make_plan()
    collection.find_one.return_value = {"_id": "mongo_plan_1", **plan.model_dump()}

    loaded = repo.get_plan("user@test.com")

    assert loaded is not None
    assert loaded.title == "Plano Mestre"
    collection.find_one.assert_called_once()
