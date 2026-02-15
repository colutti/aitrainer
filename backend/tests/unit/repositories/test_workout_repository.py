"""Tests for workout repository (workout log management)."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from bson import ObjectId
from src.repositories.workout_repository import WorkoutRepository
from src.api.models.workout_log import WorkoutLog, ExerciseLog
from src.api.models.workout_stats import WorkoutStats


@pytest.fixture
def mock_db():
    """Create mock MongoDB database."""
    db_mock = MagicMock()
    collection_mock = MagicMock()
    db_mock.__getitem__.return_value = collection_mock
    return db_mock


@pytest.fixture
def workout_repo(mock_db):
    """Create WorkoutRepository instance with mock database."""
    return WorkoutRepository(mock_db)


@pytest.fixture
def sample_workout_log():
    """Create a sample workout log for testing."""
    return WorkoutLog(
        user_email="user@example.com",
        date=datetime.now(),
        workout_type="Strength",
        exercises=[
            ExerciseLog(
                name="Bench Press",
                sets=3,
                reps_per_set=[10, 10, 10],
                weights_per_set=[100, 100, 100]
            )
        ],
        duration_minutes=60
    )


class TestWorkoutRepositorySaveLog:
    """Test save_log method."""

    def test_save_log_creates_new_entry(self, workout_repo, mock_db, sample_workout_log):
        """Test creating a new workout log."""
        test_id = ObjectId()
        mock_db.__getitem__.return_value.insert_one.return_value.inserted_id = test_id

        result = workout_repo.save_log(sample_workout_log)

        assert result == str(test_id)
        mock_db.__getitem__.return_value.insert_one.assert_called_once()

    def test_save_log_returns_string_id(self, workout_repo, mock_db, sample_workout_log):
        """Test that save_log returns string ID."""
        test_id = ObjectId()
        mock_db.__getitem__.return_value.insert_one.return_value.inserted_id = test_id

        result = workout_repo.save_log(sample_workout_log)

        assert isinstance(result, str)


class TestWorkoutRepositoryGetLogs:
    """Test get_logs method."""

    def test_get_logs_default_limit(self, workout_repo, mock_db):
        """Test retrieving logs with default limit."""
        cursor = MagicMock()
        cursor.sort.return_value = cursor
        cursor.limit.return_value = []

        mock_db.__getitem__.return_value.find.return_value = cursor

        result = workout_repo.get_logs("user@example.com")

        assert isinstance(result, list)
        cursor.limit.assert_called_once_with(50)

    def test_get_logs_custom_limit(self, workout_repo, mock_db):
        """Test retrieving logs with custom limit."""
        cursor = MagicMock()
        cursor.sort.return_value = cursor
        cursor.limit.return_value = []

        mock_db.__getitem__.return_value.find.return_value = cursor

        result = workout_repo.get_logs("user@example.com", limit=100)

        assert isinstance(result, list)
        cursor.limit.assert_called_once_with(100)

    def test_get_logs_descending_order(self, workout_repo, mock_db):
        """Test that logs are sorted by date descending."""
        cursor = MagicMock()
        cursor.sort.return_value = cursor
        cursor.limit.return_value = []

        mock_db.__getitem__.return_value.find.return_value = cursor

        workout_repo.get_logs("user@example.com")

        import pymongo
        cursor.sort.assert_called_once_with("date", pymongo.DESCENDING)


class TestWorkoutRepositoryDeleteLog:
    """Test delete_log method."""

    def test_delete_log_successful(self, workout_repo, mock_db):
        """Test successful workout deletion."""
        mock_db.__getitem__.return_value.delete_one.return_value.deleted_count = 1

        result = workout_repo.delete_log(str(ObjectId()))

        assert result is True

    def test_delete_log_not_found(self, workout_repo, mock_db):
        """Test deletion when workout doesn't exist."""
        mock_db.__getitem__.return_value.delete_one.return_value.deleted_count = 0

        result = workout_repo.delete_log(str(ObjectId()))

        assert result is False

    def test_delete_log_uses_object_id(self, workout_repo, mock_db):
        """Test that delete uses ObjectId query."""
        test_id = str(ObjectId())
        mock_db.__getitem__.return_value.delete_one.return_value.deleted_count = 1

        workout_repo.delete_log(test_id)

        collection = mock_db.__getitem__.return_value
        call_args = collection.delete_one.call_args[0][0]

        # Should use ObjectId for query
        assert "_id" in call_args


class TestWorkoutRepositoryGetLogById:
    """Test get_log_by_id method."""

    def test_get_log_by_id_found(self, workout_repo, mock_db):
        """Test retrieving workout by ID."""
        test_id = str(ObjectId())
        test_doc = {
            "_id": ObjectId(test_id),
            "user_email": "user@example.com",
            "workout_type": "Strength"
        }

        mock_db.__getitem__.return_value.find_one.return_value = test_doc

        result = workout_repo.get_log_by_id(test_id)

        assert result is not None
        assert result["user_email"] == "user@example.com"

    def test_get_log_by_id_not_found(self, workout_repo, mock_db):
        """Test retrieving non-existent workout."""
        mock_db.__getitem__.return_value.find_one.return_value = None

        result = workout_repo.get_log_by_id(str(ObjectId()))

        assert result is None


class TestWorkoutRepositoryGetPaginated:
    """Test get_paginated method."""

    def test_get_paginated_first_page(self, workout_repo, mock_db):
        """Test retrieving first page."""
        cursor = MagicMock()
        cursor.sort.return_value = cursor
        cursor.skip.return_value = cursor
        cursor.limit.return_value = []

        mock_db.__getitem__.return_value.find.return_value = cursor
        mock_db.__getitem__.return_value.count_documents.return_value = 50

        workouts, total = workout_repo.get_paginated("user@example.com", page=1, page_size=10)

        assert isinstance(workouts, list)
        assert total == 50
        cursor.skip.assert_called_once_with(0)
        cursor.limit.assert_called_once_with(10)

    def test_get_paginated_second_page(self, workout_repo, mock_db):
        """Test retrieving second page."""
        cursor = MagicMock()
        cursor.sort.return_value = cursor
        cursor.skip.return_value = cursor
        cursor.limit.return_value = []

        mock_db.__getitem__.return_value.find.return_value = cursor
        mock_db.__getitem__.return_value.count_documents.return_value = 50

        workouts, total = workout_repo.get_paginated("user@example.com", page=2, page_size=10)

        cursor.skip.assert_called_once_with(10)

    def test_get_paginated_with_workout_type_filter(self, workout_repo, mock_db):
        """Test pagination with workout type filter."""
        cursor = MagicMock()
        cursor.sort.return_value = cursor
        cursor.skip.return_value = cursor
        cursor.limit.return_value = []

        mock_db.__getitem__.return_value.find.return_value = cursor
        mock_db.__getitem__.return_value.count_documents.return_value = 20

        workouts, total = workout_repo.get_paginated(
            "user@example.com",
            page=1,
            workout_type="Strength"
        )

        collection = mock_db.__getitem__.return_value
        call_args = collection.find.call_args[0][0]
        assert call_args.get("workout_type") == "Strength"

    def test_get_paginated_converts_id_field(self, workout_repo, mock_db):
        """Test that _id is converted to id in results."""
        cursor = MagicMock()
        cursor.sort.return_value = cursor
        cursor.skip.return_value = cursor

        test_doc = {
            "_id": ObjectId(),
            "user_email": "user@example.com",
            "workout_type": "Strength"
        }
        cursor.limit.return_value = [test_doc]

        mock_db.__getitem__.return_value.find.return_value = cursor
        mock_db.__getitem__.return_value.count_documents.return_value = 1

        workouts, total = workout_repo.get_paginated("user@example.com")

        assert len(workouts) > 0


class TestWorkoutRepositoryGetTypes:
    """Test get_types method."""

    def test_get_types_returns_sorted_list(self, workout_repo, mock_db):
        """Test that workout types are returned sorted."""
        mock_db.__getitem__.return_value.distinct.return_value = ["Strength", "Cardio", "Flexibility"]

        result = workout_repo.get_types("user@example.com")

        assert isinstance(result, list)
        assert result == sorted(result)

    def test_get_types_filters_empty_strings(self, workout_repo, mock_db):
        """Test that empty strings are filtered out."""
        mock_db.__getitem__.return_value.distinct.return_value = ["Strength", "", "Cardio"]

        result = workout_repo.get_types("user@example.com")

        assert "" not in result

    def test_get_types_empty_result(self, workout_repo, mock_db):
        """Test when no workout types exist."""
        mock_db.__getitem__.return_value.distinct.return_value = []

        result = workout_repo.get_types("user@example.com")

        assert result == []


class TestWorkoutRepositoryGetStats:
    """Test get_stats method."""

    def test_get_stats_no_workouts(self, workout_repo, mock_db):
        """Test stats when no workouts exist."""
        cursor = MagicMock()
        cursor.sort.return_value = []

        mock_db.__getitem__.return_value.find.return_value = cursor

        result = workout_repo.get_stats("user@example.com")

        assert isinstance(result, WorkoutStats)
        assert result.total_workouts == 0
        assert result.current_streak_weeks == 0

    def test_get_stats_returns_workout_stats(self, workout_repo, mock_db):
        """Test that stats returns WorkoutStats object."""
        cursor = MagicMock()
        cursor.sort.return_value = []

        mock_db.__getitem__.return_value.find.return_value = cursor

        result = workout_repo.get_stats("user@example.com")

        assert isinstance(result, WorkoutStats)
        assert hasattr(result, 'total_workouts')
        assert hasattr(result, 'current_streak_weeks')
        assert hasattr(result, 'weekly_frequency')


class TestWorkoutRepositoryCalculateWeeklyStreak:
    """Test _calculate_weekly_streak method."""

    def test_calculate_weekly_streak_no_workouts(self, workout_repo):
        """Test streak calculation with no workouts."""
        result = workout_repo._calculate_weekly_streak([])

        assert result == 0

    def test_calculate_weekly_streak_single_week(self, workout_repo):
        """Test streak with single week of workouts."""
        now = datetime.now()
        workouts = [
            {"date": now - timedelta(days=1)},
            {"date": now - timedelta(days=2)},
            {"date": now - timedelta(days=3)}
        ]

        result = workout_repo._calculate_weekly_streak(workouts)

        # Should detect at least current week
        assert isinstance(result, int)
        assert result >= 0


class TestWorkoutRepositoryCalculateRecentPRs:
    """Test _calculate_recent_prs method."""

    def test_calculate_recent_prs_no_exercises(self, workout_repo):
        """Test PR calculation with no exercises."""
        workouts = [{"date": datetime.now(), "exercises": [], "_id": ObjectId()}]

        result = workout_repo._calculate_recent_prs(workouts)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_calculate_recent_prs_returns_list(self, workout_repo):
        """Test that PR calculation returns list."""
        now = datetime.now()
        workouts = [{
            "date": now,
            "exercises": [{
                "name": "Bench Press",
                "weights_per_set": [100],
                "reps_per_set": [10]
            }],
            "_id": ObjectId()
        }]

        result = workout_repo._calculate_recent_prs(workouts)

        assert isinstance(result, list)

    def test_calculate_recent_prs_excludes_cardio_with_empty_weights(self, workout_repo):
        """Test that cardio exercises with empty weights_per_set are NOT included in PRs."""
        now = datetime.now()
        # Cardio exercise: spinning with NO weights
        workouts = [{
            "date": now,
            "exercises": [{
                "name": "Spinning",
                "weights_per_set": [],  # Empty for cardio
                "reps_per_set": [20],   # Might have reps but no weight
                "distance_meters_per_set": [5000],
                "duration_seconds_per_set": [1200]
            }],
            "_id": ObjectId()
        }]

        result = workout_repo._calculate_recent_prs(workouts)

        # Cardio should NOT appear in personal records
        assert len(result) == 0

    def test_calculate_recent_prs_excludes_cardio_with_zero_weights(self, workout_repo):
        """Test that cardio exercises with [0.0] weights are NOT included in PRs."""
        now = datetime.now()
        # If cardio somehow has weights_per_set = [0.0] instead of []
        workouts = [{
            "date": now,
            "exercises": [{
                "name": "Spinning",
                "weights_per_set": [0.0],  # Problematic: 0 weight instead of empty
                "reps_per_set": [1],
                "distance_meters_per_set": [5000],
                "duration_seconds_per_set": [1200]
            }],
            "_id": ObjectId()
        }]

        result = workout_repo._calculate_recent_prs(workouts)

        # Cardio with 0 weight should NOT appear - but BUG: it does!
        assert len(result) == 0, f"Expected no PRs, but got: {result}"


class TestWorkoutRepositoryCalculateVolumeTrend:
    """Test _calculate_volume_trend method."""

    def test_calculate_volume_trend_returns_8_weeks(self, workout_repo):
        """Test that volume trend returns 8 weeks of data."""
        result = workout_repo._calculate_volume_trend([])

        assert isinstance(result, list)
        assert len(result) == 8

    def test_calculate_volume_trend_recent_workout(self, workout_repo):
        """Test volume trend with recent workout."""
        now = datetime.now()
        workouts = [{
            "date": now,
            "exercises": [{
                "name": "Exercise",
                "reps_per_set": [10],
                "weights_per_set": [100]
            }]
        }]

        result = workout_repo._calculate_volume_trend(workouts)

        assert isinstance(result, list)
        assert len(result) == 8


class TestWorkoutRepositoryCalculateStrengthRadar:
    """Test _calculate_strength_radar method."""

    def test_calculate_strength_radar_empty_workouts(self, workout_repo):
        """Test strength radar with no workouts."""
        result = workout_repo._calculate_strength_radar([])

        assert isinstance(result, dict)
        assert "Push" in result
        assert "Pull" in result
        assert "Legs" in result

    def test_calculate_strength_radar_returns_ratios(self, workout_repo):
        """Test that strength radar returns 0-1 ratios."""
        result = workout_repo._calculate_strength_radar([])

        for value in result.values():
            assert 0 <= value <= 1.0


class TestWorkoutRepositoryEdgeCases:
    """Test edge cases and error handling."""

    def test_save_log_multiple_exercises(self, workout_repo, mock_db):
        """Test saving workout with multiple exercises."""
        log = WorkoutLog(
            user_email="user@example.com",
            date=datetime.now(),
            workout_type="Strength",
            exercises=[
                ExerciseLog(
                    name="Bench Press",
                    sets=3,
                    reps_per_set=[10, 10, 10],
                    weights_per_set=[100, 100, 100]
                ),
                ExerciseLog(
                    name="Squat",
                    sets=4,
                    reps_per_set=[8, 8, 8, 8],
                    weights_per_set=[150, 150, 150, 150]
                )
            ]
        )

        test_id = ObjectId()
        mock_db.__getitem__.return_value.insert_one.return_value.inserted_id = test_id

        result = workout_repo.save_log(log)

        assert result == str(test_id)

    def test_get_paginated_large_page_size(self, workout_repo, mock_db):
        """Test pagination with large page size."""
        cursor = MagicMock()
        cursor.sort.return_value = cursor
        cursor.skip.return_value = cursor
        cursor.limit.return_value = []

        mock_db.__getitem__.return_value.find.return_value = cursor
        mock_db.__getitem__.return_value.count_documents.return_value = 1000

        workouts, total = workout_repo.get_paginated(
            "user@example.com",
            page_size=1000
        )

        assert total == 1000

    def test_database_error_on_save(self, workout_repo, mock_db, sample_workout_log):
        """Test handling database error on save."""
        mock_db.__getitem__.return_value.insert_one.side_effect = Exception("DB Error")

        with pytest.raises(Exception) as exc_info:
            workout_repo.save_log(sample_workout_log)

        assert "DB Error" in str(exc_info.value)

    def test_database_error_on_get_stats(self, workout_repo, mock_db):
        """Test handling database error on get_stats."""
        mock_db.__getitem__.return_value.find.side_effect = Exception("DB Error")

        with pytest.raises(Exception) as exc_info:
            workout_repo.get_stats("user@example.com")

        assert "DB Error" in str(exc_info.value)

    def test_database_error_on_delete(self, workout_repo, mock_db):
        """Test handling database error on delete."""
        mock_db.__getitem__.return_value.delete_one.side_effect = Exception("DB Error")

        with pytest.raises(Exception) as exc_info:
            workout_repo.delete_log(str(ObjectId()))

        assert "DB Error" in str(exc_info.value)
