"""Tests for HevyService."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.hevy_service import HevyService
from src.api.models.workout_log import WorkoutLog, ExerciseLog
from src.api.models.routine import HevyRoutine, RoutineListResponse


@pytest.fixture
def mock_workout_repository():
    """Mock WorkoutRepository dependency."""
    repo = MagicMock()
    repo.collection = MagicMock()
    return repo


@pytest.fixture
def hevy_service(mock_workout_repository):
    """HevyService instance with mocked repository."""
    return HevyService(mock_workout_repository)


@pytest.fixture
def sample_hevy_workout():
    """Sample workout from Hevy API."""
    return {
        "id": "workout_123",
        "title": "Upper Body",
        "start_time": "2024-01-15T10:00:00Z",
        "end_time": "2024-01-15T11:30:00Z",
        "exercises": [
            {
                "id": "ex_1",
                "title": "Bench Press",
                "sets": [
                    {"reps": 10, "weight_kg": 100.0},
                    {"reps": 8, "weight_kg": 110.0},
                ],
            },
            {
                "id": "ex_2",
                "title": "Dumbbell Row",
                "sets": [
                    {"reps": 12, "weight_kg": 50.0},
                ],
            },
        ],
    }


class TestValidateApiKey:
    """Test API key validation."""

    @pytest.mark.asyncio
    async def test_validate_api_key_success(self, hevy_service):
        """Test successful API key validation."""
        with patch("src.services.hevy_service.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await hevy_service.validate_api_key("valid_key_123")

            assert result is True
            mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_api_key_invalid(self, hevy_service):
        """Test invalid API key validation."""
        with patch("src.services.hevy_service.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await hevy_service.validate_api_key("invalid_key")

            assert result is False

    @pytest.mark.asyncio
    async def test_validate_api_key_request_error(self, hevy_service):
        """Test API key validation with network error."""
        with patch("src.services.hevy_service.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            import httpx
            mock_client.get = AsyncMock(side_effect=httpx.RequestError("Connection failed"))
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await hevy_service.validate_api_key("any_key")

            assert result is False


class TestGetWorkoutCount:
    """Test getting workout count."""

    @pytest.mark.asyncio
    async def test_get_workout_count_success(self, hevy_service):
        """Test successful workout count retrieval."""
        with patch("src.services.hevy_service.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"workout_count": 42}
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            count = await hevy_service.get_workout_count("api_key")

            assert count == 42

    @pytest.mark.asyncio
    async def test_get_workout_count_error_response(self, hevy_service):
        """Test workout count with error response."""
        with patch("src.services.hevy_service.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            count = await hevy_service.get_workout_count("api_key")

            assert count == 0

    @pytest.mark.asyncio
    async def test_get_workout_count_exception(self, hevy_service):
        """Test workout count with exception."""
        with patch("src.services.hevy_service.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("Network error"))
            mock_client_class.return_value.__aenter__.return_value = mock_client

            count = await hevy_service.get_workout_count("api_key")

            assert count == 0


class TestFetchWorkouts:
    """Test fetching workouts."""

    @pytest.mark.asyncio
    async def test_fetch_workouts_success(self, hevy_service, sample_hevy_workout):
        """Test successful workout fetch."""
        with patch("src.services.hevy_service.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"workouts": [sample_hevy_workout]}
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            workouts = await hevy_service.fetch_workouts("api_key", page=1, page_size=10)

            assert len(workouts) == 1
            assert workouts[0]["id"] == "workout_123"

    @pytest.mark.asyncio
    async def test_fetch_workouts_empty(self, hevy_service):
        """Test fetch when no workouts returned."""
        with patch("src.services.hevy_service.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"workouts": []}
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            workouts = await hevy_service.fetch_workouts("api_key")

            assert len(workouts) == 0

    @pytest.mark.asyncio
    async def test_fetch_workouts_pagination(self, hevy_service, sample_hevy_workout):
        """Test workout fetch respects pagination parameters."""
        with patch("src.services.hevy_service.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"workouts": [sample_hevy_workout]}
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await hevy_service.fetch_workouts("api_key", page=3, page_size=20)

            # Verify parameters were passed correctly
            call_args = mock_client.get.call_args
            assert call_args[1]["params"]["page"] == 3
            assert call_args[1]["params"]["pageSize"] == 20


class TestFetchWorkoutById:
    """Test fetching workout by ID."""

    @pytest.mark.asyncio
    async def test_fetch_workout_by_id_success(self, hevy_service, sample_hevy_workout):
        """Test successful fetch of single workout."""
        with patch("src.services.hevy_service.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"workout": sample_hevy_workout}
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            workout = await hevy_service.fetch_workout_by_id("api_key", "workout_123")

            assert workout is not None
            assert workout["id"] == "workout_123"

    @pytest.mark.asyncio
    async def test_fetch_workout_by_id_not_found(self, hevy_service):
        """Test fetch when workout not found."""
        with patch("src.services.hevy_service.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            workout = await hevy_service.fetch_workout_by_id("api_key", "nonexistent")

            assert workout is None


class TestTransformWorkout:
    """Test workout transformation."""

    def test_transform_to_workout_log_success(self, hevy_service, sample_hevy_workout):
        """Test successful workout transformation."""
        log = hevy_service.transform_to_workout_log(
            sample_hevy_workout, "user@test.com"
        )

        assert log is not None
        assert log.user_email == "user@test.com"
        assert log.workout_type == "Upper Body"
        assert len(log.exercises) == 2
        assert log.exercises[0].name == "Bench Press"
        assert log.duration_minutes == 90  # 11:30 - 10:00
        assert log.source == "hevy"
        assert log.external_id == "workout_123"

    def test_transform_workout_no_exercises(self, hevy_service, sample_hevy_workout):
        """Test transformation with no exercises."""
        sample_hevy_workout["exercises"] = []

        log = hevy_service.transform_to_workout_log(
            sample_hevy_workout, "user@test.com"
        )

        assert log is None

    def test_transform_workout_no_end_time(self, hevy_service, sample_hevy_workout):
        """Test transformation without end time."""
        del sample_hevy_workout["end_time"]

        log = hevy_service.transform_to_workout_log(
            sample_hevy_workout, "user@test.com"
        )

        assert log is not None
        assert log.duration_minutes is None

    def test_transform_workout_duration_less_than_one_minute(
        self, hevy_service, sample_hevy_workout
    ):
        """Test transformation ensures minimum duration is 1 minute."""
        # Set end time to 30 seconds after start
        sample_hevy_workout["end_time"] = "2024-01-15T10:00:30Z"

        log = hevy_service.transform_to_workout_log(
            sample_hevy_workout, "user@test.com"
        )

        assert log is not None
        assert log.duration_minutes == 1  # Enforced minimum

    def test_transform_workout_missing_reps_weight(self, hevy_service):
        """Test transformation with missing reps/weight."""
        workout = {
            "id": "w_1",
            "title": "Partial",
            "start_time": "2024-01-15T10:00:00Z",
            "exercises": [
                {
                    "title": "Bench Press",
                    "sets": [
                        {"reps": None, "weight_kg": None},
                        {"reps": 10, "weight_kg": None},
                    ],
                }
            ],
        }

        log = hevy_service.transform_to_workout_log(workout, "user@test.com")

        assert log is not None
        assert log.exercises[0].reps_per_set == [0, 10]
        assert log.exercises[0].weights_per_set == [0.0, 0.0]

    def test_transform_workout_invalid_date_format(self, hevy_service):
        """Test transformation with invalid ISO date."""
        workout = {
            "id": "w_1",
            "title": "Test",
            "start_time": "invalid-date",
            "exercises": [{"title": "Ex", "sets": [{"reps": 10, "weight_kg": 50}]}],
        }

        log = hevy_service.transform_to_workout_log(workout, "user@test.com")

        assert log is None


class TestImportWorkouts:
    """Test workout import orchestration."""

    @pytest.mark.asyncio
    async def test_import_workouts_success(
        self, hevy_service, sample_hevy_workout, mock_workout_repository
    ):
        """Test successful import of new workouts."""
        # Mock fetch_workouts to return sample workout once, then empty
        with patch.object(
            hevy_service, "fetch_workouts", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.side_effect = [[sample_hevy_workout], []]
            mock_workout_repository.collection.find_one.return_value = None
            mock_workout_repository.collection.find.return_value = []
            mock_workout_repository.collection.insert_one = MagicMock()

            result = await hevy_service.import_workouts(
                user_email="user@test.com",
                api_key="api_key",
                mode="skip_duplicates",
            )

            assert result["imported"] >= 1
            assert result["skipped"] == 0

    @pytest.mark.asyncio
    async def test_import_workouts_skip_duplicates(
        self, hevy_service, sample_hevy_workout, mock_workout_repository
    ):
        """Test duplicate skipping during import."""
        with patch.object(
            hevy_service, "fetch_workouts", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.side_effect = [[sample_hevy_workout], []]
            # Simulate existing workout on same day
            mock_workout_repository.collection.find_one.return_value = None
            mock_workout_repository.collection.find.return_value = [{"_id": "existing"}]

            result = await hevy_service.import_workouts(
                user_email="user@test.com",
                api_key="api_key",
                mode="skip_duplicates",
            )

            assert result["skipped"] == 1

    @pytest.mark.asyncio
    async def test_import_workouts_overwrite(
        self, hevy_service, sample_hevy_workout, mock_workout_repository
    ):
        """Test overwrite mode during import."""
        with patch.object(
            hevy_service, "fetch_workouts", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.side_effect = [[sample_hevy_workout], []]
            mock_workout_repository.collection.find_one.return_value = None
            mock_workout_repository.collection.find.return_value = [
                {"_id": "old_doc"}
            ]
            mock_workout_repository.collection.delete_one = MagicMock()

            result = await hevy_service.import_workouts(
                user_email="user@test.com",
                api_key="api_key",
                mode="overwrite",
            )

            # Old workout should be deleted
            mock_workout_repository.collection.delete_one.assert_called()

    @pytest.mark.asyncio
    async def test_import_workouts_pagination(
        self, hevy_service, sample_hevy_workout, mock_workout_repository
    ):
        """Test import handles pagination correctly."""
        with patch.object(
            hevy_service, "fetch_workouts", new_callable=AsyncMock
        ) as mock_fetch:
            # Return full page, then partial page, then empty
            mock_fetch.side_effect = [
                [sample_hevy_workout] * 10,  # Full page
                [sample_hevy_workout] * 5,  # Partial page (triggers has_more=False)
                [],
            ]
            mock_workout_repository.collection.find_one.return_value = None
            mock_workout_repository.collection.find.return_value = []

            result = await hevy_service.import_workouts(
                user_email="user@test.com",
                api_key="api_key",
            )

            # Should fetch twice (pages 1 and 2)
            assert mock_fetch.call_count == 2


class TestGetRoutines:
    """Test getting routines."""

    @pytest.mark.asyncio
    async def test_get_routines_success(self, hevy_service):
        """Test successful retrieval of routines."""
        with patch("src.services.hevy_service.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "routines": [{"id": "r1", "title": "PPL"}],
                "total": 1,
                "page": 1,
                "page_count": 1,
            }
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await hevy_service.get_routines("api_key", page=1, page_size=5)

            assert result is not None
            assert len(result.routines) == 1

    @pytest.mark.asyncio
    async def test_get_routines_max_page_size(self, hevy_service):
        """Test that page_size is capped at 10."""
        with patch("src.services.hevy_service.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"routines": [], "total": 0}
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await hevy_service.get_routines("api_key", page=1, page_size=100)

            # Verify page_size was capped
            call_args = mock_client.get.call_args
            assert call_args[1]["params"]["pageSize"] == 10

    @pytest.mark.asyncio
    async def test_get_routines_error(self, hevy_service):
        """Test routine fetch with error."""
        with patch("src.services.hevy_service.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await hevy_service.get_routines("api_key")

            assert result is None
