import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.models.user_profile import UserProfile

client = TestClient(app)


@pytest.fixture
def mock_user():
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
        hevy_webhook_token="valid_token",
        hevy_webhook_secret="secret123",
    )


@pytest.fixture
def mock_brain(mock_user):
    brain = MagicMock()
    brain.get_user_profile.return_value = mock_user
    brain._database.users.find_by_webhook_token.return_value = mock_user
    return brain


class TestHevyWebhook:
    """Tests for Hevy webhook endpoint."""

    def test_webhook_success_flow(self, mock_brain):
        """Webhook should return 200 OK immediately and queue a background task."""
        from src.core.deps import get_ai_trainer_brain, get_hevy_service

        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
        app.dependency_overrides[get_hevy_service] = lambda: MagicMock()

        with patch("fastapi.BackgroundTasks.add_task") as mock_add_task:
            response = client.post(
                "/integrations/hevy/webhook/valid_token",
                json={"id": "webhook-123", "payload": {"workoutId": "workout-456"}},
                headers={"Authorization": "Bearer secret123"},
            )

        assert response.status_code == 200
        assert response.json() == {"status": "queued"}
        mock_add_task.assert_called_once()

        app.dependency_overrides = {}

    def test_webhook_invalid_token_returns_404(self, mock_brain):
        """Webhook with invalid token should return 404."""
        from src.core.deps import get_ai_trainer_brain, get_hevy_service

        mock_brain._database.users.find_by_webhook_token.return_value = None
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
        app.dependency_overrides[get_hevy_service] = lambda: MagicMock()

        response = client.post(
            "/integrations/hevy/webhook/invalid_token",
            json={"id": "webhook-123", "payload": {"workoutId": "workout-456"}},
        )

        assert response.status_code == 404
        app.dependency_overrides = {}

    def test_webhook_invalid_auth_returns_401(self, mock_brain):
        """Webhook with wrong secret should return 401."""
        from src.core.deps import get_ai_trainer_brain, get_hevy_service

        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
        app.dependency_overrides[get_hevy_service] = lambda: MagicMock()

        response = client.post(
            "/integrations/hevy/webhook/valid_token",
            json={"id": "webhook-123", "payload": {"workoutId": "workout-456"}},
            headers={"Authorization": "Bearer WRONG_SECRET"},
        )

        assert response.status_code == 401
        app.dependency_overrides = {}

    def test_webhook_missing_workout_id_returns_400(self, mock_brain):
        """Webhook without workoutId should return 400."""
        from src.core.deps import get_ai_trainer_brain, get_hevy_service

        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
        app.dependency_overrides[get_hevy_service] = lambda: MagicMock()

        response = client.post(
            "/integrations/hevy/webhook/valid_token",
            json={
                "id": "webhook-123",
                "payload": {},  # Missing workoutId
            },
            headers={"Authorization": "Bearer secret123"},
        )

        assert response.status_code == 400
        app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_process_webhook_async_logic():
    """Verifies the background task processing logic."""
    from src.api.endpoints.hevy import process_webhook_async

    # Mocks
    mock_service = AsyncMock()
    mock_service.fetch_workout_by_id.return_value = {
        "id": "workout-456",
        "title": "Chest Day",
    }
    mock_service.transform_to_workout_log = MagicMock()
    mock_service.workout_repository.collection.find_one = MagicMock(return_value=None)
    mock_service.workout_repository.save_log = MagicMock()

    # Execute the background task directly
    await process_webhook_async(
        user_email="test@example.com",
        api_key="api_key_123",
        workout_id="workout-456",
        hevy_service=mock_service,
    )

    # Verify the flow
    mock_service.fetch_workout_by_id.assert_called_with("api_key_123", "workout-456")
    mock_service.transform_to_workout_log.assert_called_once()
    mock_service.workout_repository.save_log.assert_called_once()


@pytest.mark.asyncio
async def test_process_webhook_async_retry_logic():
    """Verifies that the background task retries on fetch failure."""
    from src.api.endpoints.hevy import process_webhook_async

    # Mocks
    mock_service = AsyncMock()
    # Mock to fail twice then succeed
    mock_service.fetch_workout_by_id.side_effect = [
        None,
        None,
        {"id": "workout-456", "title": "Chest Day"},
    ]
    mock_service.transform_to_workout_log = MagicMock()
    mock_service.workout_repository.save_log = MagicMock()

    # Patch asyncio.sleep to not wait in tests
    with patch("asyncio.sleep", AsyncMock()) as mock_sleep:
        await process_webhook_async(
            user_email="test@example.com",
            api_key="api_key_123",
            workout_id="workout-456",
            hevy_service=mock_service,
        )

        # Verify it was called 3 times
        assert mock_service.fetch_workout_by_id.call_count == 3
        # Verify sleep was called twice
        assert mock_sleep.call_count == 2
        # Verify eventual success
        mock_service.transform_to_workout_log.assert_called_once()
        mock_service.workout_repository.save_log.assert_called_once()
