from datetime import datetime
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.api.main import app
from src.core.deps import get_mongo_database
from src.services.auth import verify_token
from src.api.models.plan import ActivePlan, PlanStatus


client = TestClient(app)


def make_plan(version=1, status=PlanStatus.ACTIVE):
    return ActivePlan(
        user_email="test@example.com",
        status=status,
        title="Plano Atual",
        objective_summary="Ganhar massa",
        start_date=datetime(2026, 4, 19),
        end_date=datetime(2026, 6, 19),
        version=version,
        strategy={
            "primary_goal": "gain_muscle",
            "success_criteria": ["volume"],
            "constraints": [],
            "coaching_rationale": "superavit",
            "adaptation_policy": "approval_required",
        },
        execution={
            "today_training": {"title": "Push"},
            "today_nutrition": {"calories": 3000, "protein_target": 180},
            "upcoming_days": ["Pull"],
            "active_focus": "consistencia",
            "current_risks": [],
            "pending_changes": [],
        },
        tracking={
            "checkpoints": [],
            "adherence_snapshot": {"training": "ok", "nutrition": "ok"},
            "progress_snapshot": {"status": "on_track"},
            "last_ai_assessment": None,
            "last_user_acknowledgement": None,
        },
        governance={"change_reason": None, "approval_request": None},
    )


def test_get_active_plan_returns_plan_payload():
    mock_db = MagicMock()
    mock_db.get_active_plan.return_value = make_plan()

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    try:
        response = client.get("/plan/active")
        assert response.status_code == 200
        assert response.json()["title"] == "Plano Atual"
    finally:
        app.dependency_overrides.clear()


def test_get_active_plan_returns_404_when_missing():
    mock_db = MagicMock()
    mock_db.get_active_plan.return_value = None

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    try:
        response = client.get("/plan/active")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_list_versions_returns_latest_first():
    mock_db = MagicMock()
    mock_db.list_plan_versions.return_value = [
        make_plan(version=2, status=PlanStatus.AWAITING_APPROVAL),
        make_plan(version=1),
    ]

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    try:
        response = client.get("/plan/versions")
        assert response.status_code == 200
        assert response.json()[0]["version"] == 2
    finally:
        app.dependency_overrides.clear()


def test_create_plan_proposal_persists_awaiting_approval():
    mock_db = MagicMock()
    mock_db.get_latest_plan.return_value = make_plan(version=1)
    mock_db.save_plan.return_value = "plan_2"

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    payload = {
        "title": "Plano V2",
        "objective_summary": "ajuste",
        "change_reason": "baixa_aderencia",
        "strategy": {},
        "execution": {},
        "tracking": {},
    }

    try:
        response = client.post("/plan/proposal", json=payload)
        assert response.status_code == 200
        assert response.json()["id"] == "plan_2"
    finally:
        app.dependency_overrides.clear()


def test_approve_plan_version():
    mock_db = MagicMock()
    mock_db.approve_plan.return_value = True

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    try:
        response = client.post("/plan/approve", json={"version": 2})
        assert response.status_code == 200
        assert response.json()["approved"] is True
    finally:
        app.dependency_overrides.clear()
