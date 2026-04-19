from datetime import datetime
from unittest.mock import MagicMock

from src.api.models.plan import ActivePlan, PlanStatus
from src.repositories.plan_repository import PlanRepository
from src.services.database import MongoDatabase


def make_plan(version=1, status=PlanStatus.ACTIVE):
    return ActivePlan(
        id=f"plan_{version}",
        user_email="user@test.com",
        status=status,
        title="Plano Atual",
        objective_summary="Ganhar massa",
        start_date=datetime(2026, 4, 19),
        end_date=datetime(2026, 6, 19),
        version=version,
        strategy={
            "primary_goal": "gain_muscle",
            "success_criteria": ["mais volume"],
            "constraints": [],
            "coaching_rationale": "superavit leve",
            "adaptation_policy": "approval_required",
        },
        execution={
            "today_training": {"title": "Push"},
            "today_nutrition": {"calories": 3000},
            "upcoming_days": [],
            "active_focus": "consistencia",
            "current_risks": [],
            "pending_changes": [],
        },
        tracking={
            "checkpoints": [],
            "adherence_snapshot": {"training": "unknown", "nutrition": "unknown"},
            "progress_snapshot": {"status": "unknown"},
            "last_ai_assessment": None,
            "last_user_acknowledgement": None,
        },
        governance={"change_reason": None, "approval_request": None},
    )


def _build_repo_with_collection() -> tuple[PlanRepository, MagicMock]:
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    return PlanRepository(mock_db), mock_collection


def test_save_active_plan_upserts_current_version():
    repo, collection = _build_repo_with_collection()
    plan = make_plan()

    collection.update_one.return_value.upserted_id = "mongo_plan_1"
    collection.find_one.return_value = {
        "_id": "mongo_plan_1",
        **plan.model_dump(),
    }

    plan_id = repo.save_plan(plan)

    assert plan_id == "mongo_plan_1"
    loaded = repo.get_active_plan("user@test.com")
    assert loaded is not None
    assert loaded.version == 1


def test_approve_plan_replaces_previous_active_version():
    repo, collection = _build_repo_with_collection()

    collection.update_many.return_value.modified_count = 1
    collection.update_one.return_value.matched_count = 1
    collection.find_one.return_value = {
        "_id": "mongo_plan_2",
        **make_plan(version=2, status=PlanStatus.ACTIVE).model_dump(),
    }

    approved = repo.approve_plan("user@test.com", version=2)

    assert approved is True
    active = repo.get_active_plan("user@test.com")
    assert active is not None
    assert active.version == 2


def test_list_plan_versions_returns_latest_first():
    repo, collection = _build_repo_with_collection()

    collection.find.return_value.sort.return_value = [
        {"_id": "p2", **make_plan(version=2, status=PlanStatus.AWAITING_APPROVAL).model_dump()},
        {"_id": "p1", **make_plan(version=1).model_dump()},
    ]

    versions = repo.list_plan_versions("user@test.com")

    assert versions[0].version == 2
    assert versions[1].version == 1


def test_database_delegates_plan_operations():
    db = MongoDatabase.__new__(MongoDatabase)
    db.plans = MagicMock()

    plan = make_plan(version=3)
    db.save_plan(plan)
    db.get_active_plan("user@test.com")
    db.get_latest_plan("user@test.com")
    db.list_plan_versions("user@test.com")
    db.approve_plan("user@test.com", 3)

    db.plans.save_plan.assert_called_once_with(plan)
    db.plans.get_active_plan.assert_called_once_with("user@test.com")
    db.plans.get_latest_plan.assert_called_once_with("user@test.com")
    db.plans.list_plan_versions.assert_called_once_with("user@test.com")
    db.plans.approve_plan.assert_called_once_with("user@test.com", 3)
