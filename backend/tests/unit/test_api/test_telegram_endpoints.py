"""API tests for Telegram endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock
from src.api.main import app
from src.core.deps import get_telegram_repository, get_telegram_service, get_ai_trainer_brain
from src.services.auth import verify_token
from src.api.models.telegram_link import TelegramLink

client = TestClient(app)


@pytest.fixture
def mock_telegram_repo():
    repo = Mock()
    repo.create_linking_code.return_value = "ABC123"
    repo.get_link_by_email.return_value = None
    repo.delete_link.return_value = True
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
        telegram_notify_on_workout=True,
        telegram_notify_on_nutrition=False,
        telegram_notify_on_weight=False,
    ))
    return brain


def test_generate_code_authenticated(mock_telegram_repo):
    """Test generating linking code with authentication."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_telegram_repository] = lambda: mock_telegram_repo

    response = client.post("/telegram/generate-code")
    assert response.status_code == 200
    assert response.json()["code"] == "ABC123"
    assert response.json()["expires_in_seconds"] == 600

    app.dependency_overrides = {}


def test_generate_code_unauthenticated():
    """Test generating code without authentication."""
    response = client.post("/telegram/generate-code")
    assert response.status_code == 401


def test_status_not_linked(mock_telegram_repo, mock_brain):
    """Test status endpoint when not linked."""
    mock_telegram_repo.get_link_by_email.return_value = None

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_telegram_repository] = lambda: mock_telegram_repo
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.get("/telegram/status")
    assert response.status_code == 200
    assert response.json()["linked"] is False

    app.dependency_overrides = {}


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

    app.dependency_overrides = {}


def test_unlink_success(mock_telegram_repo):
    """Test unlinking successfully."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_telegram_repository] = lambda: mock_telegram_repo

    response = client.post("/telegram/unlink")
    assert response.status_code == 200
    assert "Unlinked successfully" in response.json()["message"]

    app.dependency_overrides = {}


def test_webhook_valid_request(mock_telegram_service):
    """Test webhook with valid request."""
    app.dependency_overrides[get_telegram_service] = lambda: mock_telegram_service

    response = client.post(
        "/telegram/webhook", json={"update_id": 1, "message": {"text": "test"}}
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True

    app.dependency_overrides = {}
