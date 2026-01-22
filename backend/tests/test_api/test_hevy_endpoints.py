import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock
from src.api.main import app
from src.core.deps import get_hevy_service, get_ai_trainer_brain
from src.services.auth import verify_token
from src.api.models.user_profile import UserProfile

client = TestClient(app)


@pytest.fixture
def mock_hevy_service():
    service = AsyncMock()
    service.validate_api_key.return_value = True
    service.get_workout_count.return_value = 10
    service.import_workouts.return_value = {"imported": 1, "skipped": 0, "failed": 0}
    return service


@pytest.fixture
def mock_user_profile():
    return UserProfile(
        email="test@example.com",
        gender="Masculino",
        age=25,
        weight=70,
        height=175,
        goal="Gain Muscle",
        goal_type="gain",
        hevy_api_key="stored_key",
        hevy_enabled=True,
    )


@pytest.fixture
def mock_brain(mock_user_profile):
    brain = Mock()
    brain.get_user_profile.return_value = mock_user_profile
    return brain


def test_validate_endpoint(mock_hevy_service):
    app.dependency_overrides[get_hevy_service] = lambda: mock_hevy_service

    response = client.post("/integrations/hevy/validate", json={"api_key": "test"})
    assert response.status_code == 200
    assert response.json()["valid"] is True
    assert response.json()["count"] == 10

    app.dependency_overrides = {}


def test_import_endpoint(mock_hevy_service, mock_brain):
    app.dependency_overrides[get_hevy_service] = lambda: mock_hevy_service
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.post(
        "/integrations/hevy/import", json={"mode": "skip_duplicates"}
    )
    assert response.status_code == 200
    assert response.json()["imported"] == 1

    app.dependency_overrides = {}


def test_missing_key_import(mock_hevy_service, mock_brain):
    # Profile without key
    no_key_profile = UserProfile(
        email="test@example.com",
        gender="Masculino",
        age=25,
        weight=70,
        height=175,
        goal="Get Strong",
        goal_type="gain",
        hevy_api_key=None,
    )
    mock_brain.get_user_profile.return_value = no_key_profile

    app.dependency_overrides[get_hevy_service] = lambda: mock_hevy_service
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.post("/integrations/hevy/import", json={})
    assert response.status_code == 400

    app.dependency_overrides = {}
