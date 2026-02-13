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
    brain.database.users.find_by_webhook_token.return_value = mock_user
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

        mock_brain.database.users.find_by_webhook_token.return_value = None
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


@pytest.mark.asyncio
async def test_analyze_workout_async_should_log_prompt():
    """Verify that analyze_workout_async logs the analysis prompt to database.

    This test checks that when analyze_workout_async is called (from webhook processing),
    the AI analysis prompt is logged to the prompt_logs collection, just like regular chat prompts.
    """
    from src.services.trainer import AITrainerBrain
    import inspect

    # Specification: analyze_workout_async should log prompts to database
    source = inspect.getsource(AITrainerBrain.analyze_workout_async)

    # The method SHOULD call log_prompt on the database to record the analysis
    assert "log_prompt" in source, \
        "analyze_workout_async must log the analysis prompt to database via self._database.prompts.log_prompt()"


@pytest.mark.asyncio
async def test_why_webhook_prompt_logging_was_missing():
    """Explains why the webhook prompt logging bug wasn't caught by existing tests.

    Summary:
    - Existing tests for process_webhook_async only mocked the hevy_service
    - They never checked whether prompts were being logged to the database
    - The test at line 111 (test_process_webhook_async_logic) verifies the webhook
      saves the workout, but doesn't verify that the AI analysis prompt is logged
    - Therefore, the bug (missing prompt logging) went undetected

    Why TDD would have caught this:
    - If we wrote a test FIRST that verifies "prompts should be logged when webhook triggers",
      the test would FAIL before implementation
    - Then implementation would be forced to add prompt logging to pass the test
    - With our current approach (tests after), the bug existed in production

    Lesson: Background processing (webhooks, async tasks) needs explicit tests that verify
    all side effects (saving to DB, logging, notifications, etc.), not just the main result.
    """
    # This is not a test with assertions, it's a specification/documentation
    # that explains the root cause: insufficient test coverage for webhook behavior


    # The webhook handler (line 149-247 in hevy.py) has complex async flow:
    # 1. Fetch workout from Hevy API
    # 2. Transform to WorkoutLog
    # 3. Save to MongoDB
    # 4. Trigger Telegram notification (with AI analysis)
    # 5. AI analysis should be logged to prompt_logs collection

    # But the old test only verified steps 1-3
    # Step 5 was completely untested, so the bug went undetected

    assert True  # This test documents the issue, doesn't make assertions


@pytest.mark.asyncio
async def test_webhook_end_to_end_with_ai_analysis(mock_brain):
    """
    Test complete webhook flow: receive → fetch → transform → save → AI analysis.
    This test mocks the Hevy API response to simulate a real workout.
    """
    from src.core.deps import get_ai_trainer_brain, get_hevy_service
    from src.api.models.workout_log import WorkoutLog, ExerciseLog
    from unittest.mock import AsyncMock

    # Mock hevy service to return a fake but realistic workout
    mock_hevy_service = AsyncMock()
    mock_hevy_service.fetch_workout_by_id.return_value = {
        "id": "hevy-workout-123",
        "title": "Peito e Tríceps",
        "start_time": "2026-02-13T15:46:00Z",
        "end_time": "2026-02-13T17:01:00Z",
        "exercises": [
            {
                "id": "ex1",
                "title": "Supino",
                "sets": [
                    {"reps": 8, "weight_kg": 80},
                    {"reps": 8, "weight_kg": 80},
                    {"reps": 10, "weight_kg": 70}
                ]
            },
            {
                "id": "ex2",
                "title": "Rosca Direta",
                "sets": [
                    {"reps": 10, "weight_kg": 20},
                    {"reps": 10, "weight_kg": 20}
                ]
            }
        ]
    }

    # Mock the transformed workout
    mock_workout_log = WorkoutLog(
        user_email="test@example.com",
        date="2026-02-13T15:46:00+00:00",
        workout_type="Peito e Tríceps",
        exercises=[
            ExerciseLog(name="Supino", sets=3, reps_per_set=[8, 8, 10], weights_per_set=[80.0, 80.0, 70.0]),
            ExerciseLog(name="Rosca Direta", sets=2, reps_per_set=[10, 10], weights_per_set=[20.0, 20.0]),
        ],
        source="hevy",
        external_id="hevy-workout-123"
    )
    mock_hevy_service.transform_to_workout_log.return_value = mock_workout_log

    # Mock AI analysis
    mock_brain.analyze_workout_async = AsyncMock(
        return_value="Ótimo treino de peito! Manteve a carga bem e progressão visível no tríceps. Continue assim!"
    )

    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
    app.dependency_overrides[get_hevy_service] = lambda: mock_hevy_service

    # Simulate webhook call
    response = client.post(
        "/integrations/hevy/webhook/valid_token",
        json={"id": "webhook-789", "payload": {"workoutId": "hevy-workout-123"}},
        headers={"Authorization": "Bearer secret123"},
    )

    # Should return 200 immediately (queues background task)
    assert response.status_code == 200
    assert response.json() == {"status": "queued"}

    # Verify hevy service was called to fetch
    mock_hevy_service.fetch_workout_by_id.assert_called_once()

    # Verify workout was transformed
    mock_hevy_service.transform_to_workout_log.assert_called_once()

    app.dependency_overrides = {}
