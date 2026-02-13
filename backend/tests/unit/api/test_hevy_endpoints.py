"""Tests for Hevy integration endpoints."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_hevy_service, get_ai_trainer_brain


@pytest.fixture
def mock_brain():
    """Mock AITrainerBrain dependency."""
    brain = MagicMock()
    brain.get_user_profile = MagicMock()
    brain.save_user_profile = MagicMock()
    brain._database = MagicMock()
    brain._database.users = MagicMock()
    return brain


@pytest.fixture
def mock_hevy_service():
    """Mock HevyService dependency."""
    service = MagicMock()
    service.validate_api_key = AsyncMock()
    service.get_workout_count = AsyncMock()
    service.import_workouts = AsyncMock()
    service.fetch_workout_by_id = AsyncMock()
    service.transform_to_workout_log = MagicMock()
    service.workout_repository = MagicMock()
    return service


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestHevyValidation:
    """Test Hevy API key validation endpoint."""

    def test_validate_key_success(self, client, mock_hevy_service):
        """Test successful validation of Hevy API key."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_hevy_service.validate_api_key.return_value = True
        mock_hevy_service.get_workout_count.return_value = 42
        app.dependency_overrides[get_hevy_service] = lambda: mock_hevy_service

        response = client.post(
            "/integrations/hevy/validate",
            json={"api_key": "valid_key_123"},
            headers={"Authorization": "Bearer token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["count"] == 42
        mock_hevy_service.validate_api_key.assert_called_with("valid_key_123")
        app.dependency_overrides = {}

    def test_validate_key_invalid(self, client, mock_hevy_service):
        """Test validation of invalid Hevy API key."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_hevy_service.validate_api_key.return_value = False
        app.dependency_overrides[get_hevy_service] = lambda: mock_hevy_service

        response = client.post(
            "/integrations/hevy/validate",
            json={"api_key": "invalid_key"},
            headers={"Authorization": "Bearer token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "count" not in data
        app.dependency_overrides = {}


class TestHevyConfig:
    """Test Hevy configuration endpoints."""

    def test_save_config_set_key(self, client, mock_brain):
        """Test saving new Hevy API key."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"

        profile = MagicMock()
        profile.hevy_api_key = None
        profile.hevy_enabled = False
        profile.hevy_last_sync = None
        mock_brain.get_user_profile.return_value = profile

        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        response = client.post(
            "/integrations/hevy/config",
            json={"api_key": "new_key_123", "enabled": True},
            headers={"Authorization": "Bearer token"},
        )

        assert response.status_code == 200
        assert profile.hevy_api_key == "new_key_123"
        assert profile.hevy_enabled is True
        mock_brain.save_user_profile.assert_called_once()
        data = response.json()
        assert data["enabled"] is True
        assert data["hasKey"] is True
        assert data["apiKeyMasked"] == "****_123"
        assert data["lastSync"] is None
        app.dependency_overrides = {}

    def test_save_config_clear_key(self, client, mock_brain):
        """Test clearing Hevy API key with empty string."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"

        profile = MagicMock()
        profile.hevy_api_key = "old_key"
        profile.hevy_enabled = True
        profile.hevy_last_sync = None
        mock_brain.get_user_profile.return_value = profile

        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        response = client.post(
            "/integrations/hevy/config",
            json={"api_key": "", "enabled": False},
            headers={"Authorization": "Bearer token"},
        )

        assert response.status_code == 200
        assert profile.hevy_api_key is None
        data = response.json()
        assert data["hasKey"] is False
        assert data["apiKeyMasked"] is None
        assert data["enabled"] is False
        app.dependency_overrides = {}

    def test_save_config_without_enabled(self, client, mock_brain):
        """Test that saving with just api_key works (enabled defaults to True)."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"

        profile = MagicMock()
        profile.hevy_api_key = None
        profile.hevy_enabled = False
        profile.hevy_last_sync = None
        mock_brain.get_user_profile.return_value = profile

        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        response = client.post(
            "/integrations/hevy/config",
            json={"api_key": "test_key"},
            headers={"Authorization": "Bearer token"},
        )

        assert response.status_code == 200
        assert profile.hevy_enabled is True  # default enabled=True
        data = response.json()
        assert data["enabled"] is True
        app.dependency_overrides = {}


class TestHevyStatus:
    """Test Hevy status endpoint."""

    def test_get_status_with_key(self, client, mock_brain):
        """Test status when API key is configured."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"

        profile = MagicMock()
        profile.hevy_api_key = "secret_key_12345"
        profile.hevy_enabled = True
        profile.hevy_last_sync = "2024-01-15T10:30:00"
        mock_brain.get_user_profile.return_value = profile

        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        response = client.get(
            "/integrations/hevy/status",
            headers={"Authorization": "Bearer token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True
        assert data["hasKey"] is True
        assert data["apiKeyMasked"] == "****2345"
        assert data["lastSync"] == "2024-01-15T10:30:00"
        app.dependency_overrides = {}

    def test_get_status_without_key(self, client, mock_brain):
        """Test status when no API key configured."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"

        profile = MagicMock()
        profile.hevy_api_key = None
        profile.hevy_enabled = False
        mock_brain.get_user_profile.return_value = profile

        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        response = client.get(
            "/integrations/hevy/status",
            headers={"Authorization": "Bearer token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["hasKey"] is False
        assert data["apiKeyMasked"] is None
        app.dependency_overrides = {}


class TestHevyCount:
    """Test Hevy workout count endpoint."""

    def test_get_count_success(self, client, mock_hevy_service, mock_brain):
        """Test retrieving workout count."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"

        profile = MagicMock()
        profile.hevy_api_key = "valid_key_123"
        mock_brain.get_user_profile.return_value = profile

        mock_hevy_service.get_workout_count = AsyncMock(return_value=15)

        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
        app.dependency_overrides[get_hevy_service] = lambda: mock_hevy_service

        response = client.get(
            "/integrations/hevy/count",
            headers={"Authorization": "Bearer token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 15
        app.dependency_overrides = {}

    def test_get_count_no_key(self, client, mock_brain):
        """Test getting count when no API key configured."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"

        profile = MagicMock()
        profile.hevy_api_key = None
        mock_brain.get_user_profile.return_value = profile

        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
        app.dependency_overrides[get_hevy_service] = lambda: MagicMock()

        response = client.get(
            "/integrations/hevy/count",
            headers={"Authorization": "Bearer token"},
        )

        assert response.status_code == 400
        assert "Hevy API key not configured" in response.json()["detail"]
        app.dependency_overrides = {}


class TestHevyImport:
    """Test Hevy import endpoint."""

    def test_import_workouts_success(self, client, mock_hevy_service, mock_brain):
        """Test successful import of workouts."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"

        profile = MagicMock()
        profile.hevy_api_key = "valid_key_123"
        mock_brain.get_user_profile.return_value = profile

        import_result = {"imported": 3, "skipped": 1}
        mock_hevy_service.import_workouts = AsyncMock(return_value=import_result)

        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
        app.dependency_overrides[get_hevy_service] = lambda: mock_hevy_service

        response = client.post(
            "/integrations/hevy/import",
            json={"mode": "skip_duplicates", "from_date": "2024-01-01"},
            headers={"Authorization": "Bearer token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 3
        assert data["skipped"] == 1
        mock_brain.save_user_profile.assert_called_once()
        app.dependency_overrides = {}

    def test_import_workouts_no_key(self, client, mock_brain):
        """Test import when no API key configured."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"

        profile = MagicMock()
        profile.hevy_api_key = None
        mock_brain.get_user_profile.return_value = profile

        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
        app.dependency_overrides[get_hevy_service] = lambda: MagicMock()

        response = client.post(
            "/integrations/hevy/import",
            json={"mode": "skip_duplicates"},
            headers={"Authorization": "Bearer token"},
        )

        assert response.status_code == 400
        assert "Hevy API key not configured" in response.json()["detail"]
        app.dependency_overrides = {}


class TestHevyWebhook:
    """Test Hevy webhook endpoints."""

    def test_get_webhook_config_with_token(self, client, mock_brain):
        """Test getting webhook config when token exists."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"

        profile = MagicMock()
        profile.hevy_webhook_token = "webhook_token_xyz"
        profile.hevy_webhook_secret = "secret_very_long_token_abcd"
        mock_brain.get_user_profile.return_value = profile

        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        response = client.get(
            "/integrations/hevy/webhook/config",
            headers={"Authorization": "Bearer token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["hasWebhook"] is True
        assert "webhook_token_xyz" in data["webhookUrl"]
        assert data["authHeader"] == "Bearer ****abcd"
        app.dependency_overrides = {}

    def test_get_webhook_config_no_token(self, client, mock_brain):
        """Test getting webhook config when no token exists."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"

        profile = MagicMock()
        profile.hevy_webhook_token = None
        mock_brain.get_user_profile.return_value = profile

        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        response = client.get(
            "/integrations/hevy/webhook/config",
            headers={"Authorization": "Bearer token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["hasWebhook"] is False
        assert data["webhookUrl"] is None
        app.dependency_overrides = {}

    def test_generate_webhook_credentials(self, client, mock_brain):
        """Test generating webhook credentials."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"

        profile = MagicMock()
        profile.hevy_webhook_token = None
        profile.hevy_webhook_secret = None
        mock_brain.get_user_profile.return_value = profile

        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        response = client.post(
            "/integrations/hevy/webhook/generate",
            headers={"Authorization": "Bearer token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "webhookUrl" in data
        assert "authHeader" in data
        assert data["authHeader"].startswith("Bearer ")
        # Verify save was called with new token/secret
        mock_brain.save_user_profile.assert_called_once()
        app.dependency_overrides = {}

    def test_generate_webhook_preserves_existing_token(self, client, mock_brain):
        """Test that regenerating webhook preserves existing token but rotates secret."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"

        existing_token = "existing_token_12345"
        existing_secret = "existing_secret_67890"
        profile = MagicMock()
        profile.hevy_webhook_token = existing_token
        profile.hevy_webhook_secret = existing_secret
        mock_brain.get_user_profile.return_value = profile

        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        response = client.post(
            "/integrations/hevy/webhook/generate",
            headers={"Authorization": "Bearer token"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify token is preserved (in the URL) - works with both localhost and production URLs
        assert f"/integrations/hevy/webhook/{existing_token}" in data["webhookUrl"]
        assert existing_token in data["webhookUrl"]

        # Verify secret has been rotated (new Bearer token)
        assert data["authHeader"].startswith("Bearer ")
        assert data["authHeader"] != f"Bearer {existing_secret}"

        # Verify profile.hevy_webhook_token was set to the existing token
        assert profile.hevy_webhook_token == existing_token
        mock_brain.save_user_profile.assert_called_once()
        app.dependency_overrides = {}

    def test_revoke_webhook(self, client, mock_brain):
        """Test revoking webhook credentials."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"

        profile = MagicMock()
        profile.hevy_webhook_token = "token_to_revoke"
        profile.hevy_webhook_secret = "secret_to_revoke"
        mock_brain.get_user_profile.return_value = profile

        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        response = client.delete(
            "/integrations/hevy/webhook",
            headers={"Authorization": "Bearer token"},
        )

        assert response.status_code == 200
        assert profile.hevy_webhook_token is None
        assert profile.hevy_webhook_secret is None
        mock_brain.save_user_profile.assert_called_once()
        app.dependency_overrides = {}

    def test_receive_webhook_success(self, client, mock_brain, mock_hevy_service):
        """Test receiving webhook with valid token and secret."""
        # Setup user profile
        profile = MagicMock()
        profile.email = "user@test.com"
        profile.hevy_api_key = "user_key_123"
        profile.hevy_webhook_secret = "webhook_secret_xyz"

        # Setup database mock
        mock_db = MagicMock()
        mock_db.users.find_by_webhook_token.return_value = profile

        mock_brain.database = mock_db
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
        app.dependency_overrides[get_hevy_service] = lambda: mock_hevy_service

        response = client.post(
            "/integrations/hevy/webhook/token123",
            json={
                "id": "webhook_event_123",
                "payload": {"workoutId": "workout_abc"}
            },
            headers={"Authorization": "Bearer webhook_secret_xyz"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        app.dependency_overrides = {}

    def test_receive_webhook_invalid_token(self, client, mock_brain):
        """Test webhook with invalid token."""
        # Setup database mock - token not found
        mock_db = MagicMock()
        mock_db.users.find_by_webhook_token.return_value = None

        mock_brain.database = mock_db
        mock_brain.database = mock_db
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
        app.dependency_overrides[get_hevy_service] = lambda: MagicMock()

        response = client.post(
            "/integrations/hevy/webhook/invalid_token",
            json={
                "id": "webhook_event_123",
                "payload": {"workoutId": "workout_abc"}
            },
        )

        assert response.status_code == 404
        assert "Invalid token" in response.json()["detail"]
        app.dependency_overrides = {}

    def test_receive_webhook_invalid_auth(self, client, mock_brain):
        """Test webhook with invalid authorization header."""
        # Setup profile
        profile = MagicMock()
        profile.email = "user@test.com"
        profile.hevy_webhook_secret = "correct_secret_xyz"

        # Setup database mock
        mock_db = MagicMock()
        mock_db.users.find_by_webhook_token.return_value = profile

        mock_brain.database = mock_db
        mock_brain.database = mock_db
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
        app.dependency_overrides[get_hevy_service] = lambda: MagicMock()

        response = client.post(
            "/integrations/hevy/webhook/token123",
            json={
                "id": "webhook_event_123",
                "payload": {"workoutId": "workout_abc"}
            },
            headers={"Authorization": "Bearer wrong_secret"},
        )

        assert response.status_code == 401
        assert "Invalid authorization" in response.json()["detail"]
        app.dependency_overrides = {}

    def test_receive_webhook_missing_workout_id(self, client, mock_brain):
        """Test webhook with missing workoutId."""
        # Setup profile without secret (no auth check)
        profile = MagicMock()
        profile.email = "user@test.com"
        profile.hevy_webhook_secret = None

        # Setup database mock
        mock_db = MagicMock()
        mock_db.users.find_by_webhook_token.return_value = profile

        mock_brain.database = mock_db
        mock_brain.database = mock_db
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
        app.dependency_overrides[get_hevy_service] = lambda: MagicMock()

        response = client.post(
            "/integrations/hevy/webhook/token123",
            json={
                "id": "webhook_event_123",
                "payload": {}  # Missing workoutId
            },
        )

        assert response.status_code == 400
        assert "Missing workoutId" in response.json()["detail"]
        app.dependency_overrides = {}
