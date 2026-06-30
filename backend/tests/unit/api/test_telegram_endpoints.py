"""API tests for Telegram endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock
from src.api.main import app
from src.core.deps import get_telegram_repository, get_telegram_service, get_ai_trainer_brain
from src.services.auth import verify_token
from src.api.models.telegram_link import TelegramLink

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides():
    app.dependency_overrides = {}
    yield
    app.dependency_overrides = {}


@pytest.fixture
def mock_telegram_repo():
    repo = Mock()
    repo.create_linking_code.return_value = "ABC123"
    repo.get_link_by_email.return_value = None
    repo.delete_link.return_value = True
    repo.create_or_replace_link.return_value = None
    return repo


@pytest.fixture
def mock_telegram_service():
    service = AsyncMock()
    service.handle_update = AsyncMock()
    return service


@pytest.fixture
def mock_brain():
    """Mock AI trainer brain to avoid Qdrant connection."""
    brain = Mock()
    brain.get_user_profile = Mock(return_value=Mock(
        subscription_plan="Pro",
        telegram_notify_on_workout=True,
        telegram_notify_on_nutrition=False,
        telegram_notify_on_weight=False,
    ))
    return brain


def test_generate_code_authenticated(mock_telegram_repo, mock_brain):
    """Test generating linking code with authentication."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_telegram_repository] = lambda: mock_telegram_repo
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.post("/telegram/generate-code")
    assert response.status_code == 200
    assert response.json()["code"] == "ABC123"
    assert response.json()["expires_in_seconds"] == 600

def test_generate_code_unauthenticated():
    """Test generating code without authentication."""
    response = client.post("/telegram/generate-code")
    assert response.status_code == 401


def test_generate_code_forbidden_for_basic_plan(mock_telegram_repo):
    """Basic plan cannot use Telegram endpoints."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_telegram_repository] = lambda: mock_telegram_repo

    mock_brain = Mock()
    mock_brain.get_user_profile = Mock(return_value=Mock(subscription_plan="Basic"))
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.post("/telegram/generate-code")
    assert response.status_code == 403
    assert response.json()["detail"] == "TELEGRAM_NOT_ALLOWED_FOR_PLAN"

def test_status_not_linked(mock_telegram_repo, mock_brain):
    """Test status endpoint when not linked."""
    mock_telegram_repo.get_link_by_email.return_value = None

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_telegram_repository] = lambda: mock_telegram_repo
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.get("/telegram/status")
    assert response.status_code == 200
    assert response.json()["linked"] is False

def test_status_linked(mock_telegram_repo, mock_brain):
    """Test status endpoint when linked."""
    from datetime import datetime, timezone

    mock_telegram_repo.get_link_by_email.return_value = TelegramLink(
        chat_id=123456,
        user_email="test@example.com",
        linked_at=datetime.now(timezone.utc),
        telegram_username="testuser",
    )

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_telegram_repository] = lambda: mock_telegram_repo
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.get("/telegram/status")
    assert response.status_code == 200
    data = response.json()
    assert data["linked"] is True
    assert data["telegram_username"] == "testuser"
    assert data["telegram_notify_on_workout"] is True
    assert data["telegram_notify_on_nutrition"] is False
    assert data["telegram_notify_on_weight"] is False


def test_status_linked_uses_persisted_notification_preferences(mock_telegram_repo):
    """Linked Telegram status must reflect persisted notification toggles."""
    from datetime import datetime, timezone

    mock_telegram_repo.get_link_by_email.return_value = TelegramLink(
        chat_id=123456,
        user_email="test@example.com",
        linked_at=datetime.now(timezone.utc),
        telegram_username="testuser",
    )

    mock_brain = Mock()
    mock_brain.get_user_profile = Mock(return_value=Mock(
        subscription_plan="Pro",
        telegram_notify_on_workout=False,
        telegram_notify_on_nutrition=True,
        telegram_notify_on_weight=True,
    ))

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_telegram_repository] = lambda: mock_telegram_repo
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.get("/telegram/status")

    assert response.status_code == 200
    data = response.json()
    assert data["linked"] is True
    assert data["telegram_notify_on_workout"] is False
    assert data["telegram_notify_on_nutrition"] is True
    assert data["telegram_notify_on_weight"] is True

def test_unlink_success(mock_telegram_repo, mock_brain):
    """Test unlinking successfully."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_telegram_repository] = lambda: mock_telegram_repo
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.post("/telegram/unlink")
    assert response.status_code == 200
    assert "Unlinked successfully" in response.json()["message"]


def test_e2e_link_success_when_test_auth_enabled(mock_telegram_repo, mock_brain, monkeypatch):
    """E2E link seed should be available only in test auth environments."""
    monkeypatch.setattr("src.api.endpoints.telegram.is_e2e_test_auth_enabled", lambda: True)
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_telegram_repository] = lambda: mock_telegram_repo
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.post(
        "/telegram/e2e-link",
        json={"chat_id": 987654321, "username": "e2e_telegram_user"},
    )

    assert response.status_code == 200
    assert response.json() == {"linked": True}
    mock_telegram_repo.create_or_replace_link.assert_called_once_with(
        "test@example.com", 987654321, "e2e_telegram_user"
    )


def test_e2e_link_hidden_when_test_auth_disabled(mock_telegram_repo, mock_brain, monkeypatch):
    """E2E seed endpoint must not be exposed outside E2E auth mode."""
    monkeypatch.setattr("src.api.endpoints.telegram.is_e2e_test_auth_enabled", lambda: False)
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_telegram_repository] = lambda: mock_telegram_repo
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.post(
        "/telegram/e2e-link",
        json={"chat_id": 987654321, "username": "e2e_telegram_user"},
    )

    assert response.status_code == 404
    mock_telegram_repo.create_or_replace_link.assert_not_called()

def test_webhook_valid_request(mock_telegram_service):
    """Test webhook with valid request."""
    app.dependency_overrides[get_telegram_service] = lambda: mock_telegram_service

    response = client.post(
        "/telegram/webhook", json={"update_id": 1, "message": {"text": "test"}}
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
