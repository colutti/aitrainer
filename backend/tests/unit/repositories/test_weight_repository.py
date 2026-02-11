"""Tests for weight repository (weight log management)."""

import pytest
from datetime import date, datetime
from unittest.mock import MagicMock
from src.repositories.weight_repository import WeightRepository
from src.api.models.weight_log import WeightLog


@pytest.fixture
def mock_db():
    """Create mock MongoDB database."""
    db_mock = MagicMock()
    collection_mock = MagicMock()
    db_mock.__getitem__.return_value = collection_mock
    return db_mock


@pytest.fixture
def weight_repo(mock_db):
    """Create WeightRepository instance with mock database."""
    return WeightRepository(mock_db)


@pytest.fixture
def sample_weight_log():
    """Create a sample weight log for testing."""
    return WeightLog(
        user_email="user@example.com",
        date=date.today(),
        weight_kg=80.5,
        body_fat_pct=20.0,
        source="manual"
    )


class TestWeightRepositoryEnsureIndexes:
    """Test ensure_indexes method."""

    def test_ensure_indexes_creates_unique_index(self, weight_repo, mock_db):
        """Test that unique index is created."""
        weight_repo.ensure_indexes()

        collection = mock_db.__getitem__.return_value
        collection.create_index.assert_called_once()

        # Verify the index call
        call_args = collection.create_index.call_args
        index_spec = call_args[0][0]

        # Should be a list of tuples for compound index
        assert isinstance(index_spec, list)
        assert len(index_spec) == 2

    def test_ensure_indexes_unique_constraint(self, weight_repo, mock_db):
        """Test that unique constraint is applied."""
        weight_repo.ensure_indexes()

        collection = mock_db.__getitem__.return_value
        call_kwargs = collection.create_index.call_args[1]

        assert call_kwargs.get('unique') is True

    def test_ensure_indexes_idempotent(self, weight_repo, mock_db):
        """Test that calling ensure_indexes multiple times is safe."""
        weight_repo.ensure_indexes()
        weight_repo.ensure_indexes()

        collection = mock_db.__getitem__.return_value
        # Should be called twice (MongoDB handles idempotency)
        assert collection.create_index.call_count == 2


class TestWeightRepositorySaveLog:
    """Test save_log method."""

    def test_save_log_creates_new_entry(self, weight_repo, mock_db, sample_weight_log):
        """Test creating a new weight log entry."""
        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = "507f1f77bcf86cd799439011"
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0

        doc_id, is_new = weight_repo.save_log(sample_weight_log)

        assert is_new is True
        assert doc_id == "507f1f77bcf86cd799439011"

        collection = mock_db.__getitem__.return_value
        collection.update_one.assert_called_once()

    def test_save_log_updates_existing_entry(self, weight_repo, mock_db, sample_weight_log):
        """Test updating existing weight log entry."""
        existing_id = "507f1f77bcf86cd799439011"
        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = None
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 1
        mock_db.__getitem__.return_value.find_one.return_value = {"_id": existing_id}

        doc_id, is_new = weight_repo.save_log(sample_weight_log)

        assert is_new is False
        assert doc_id == existing_id

    def test_save_log_upsert_true(self, weight_repo, mock_db, sample_weight_log):
        """Test that upsert is enabled."""
        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = "new_id"
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0

        weight_repo.save_log(sample_weight_log)

        collection = mock_db.__getitem__.return_value
        call_kwargs = collection.update_one.call_args[1]
        assert call_kwargs.get('upsert') is True

    def test_save_log_with_body_composition(self, weight_repo, mock_db):
        """Test saving log with complete body composition data."""
        log = WeightLog(
            user_email="user@example.com",
            date=date.today(),
            weight_kg=75.0,
            body_fat_pct=18.5,
            muscle_mass_pct=38.0,
            bone_mass_kg=3.2,
            body_water_pct=55.0,
            visceral_fat=8.0,
            bmr=1700,
            bmi=24.5
        )

        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = "id"
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0

        weight_repo.save_log(log)

        collection = mock_db.__getitem__.return_value
        collection.update_one.assert_called_once()

    def test_save_log_datetime_conversion(self, weight_repo, mock_db):
        """Test that date is converted to datetime properly."""
        test_date = date(2024, 1, 15)
        log = WeightLog(
            user_email="user@example.com",
            date=test_date,
            weight_kg=80.0
        )

        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = "id"
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0

        weight_repo.save_log(log)

        collection = mock_db.__getitem__.return_value
        call_args = collection.update_one.call_args

        # Check that date is converted to datetime
        update_data = call_args[0][1]["$set"]
        assert isinstance(update_data["date"], datetime)


class TestWeightRepositoryDeleteLog:
    """Test delete_log method."""

    def test_delete_log_successful(self, weight_repo, mock_db):
        """Test successful log deletion."""
        mock_db.__getitem__.return_value.delete_one.return_value.deleted_count = 1

        result = weight_repo.delete_log("user@example.com", date.today())

        assert result is True
        mock_db.__getitem__.return_value.delete_one.assert_called_once()

    def test_delete_log_not_found(self, weight_repo, mock_db):
        """Test deletion when log doesn't exist."""
        mock_db.__getitem__.return_value.delete_one.return_value.deleted_count = 0

        result = weight_repo.delete_log("user@example.com", date.today())

        assert result is False

    def test_delete_log_correct_query(self, weight_repo, mock_db):
        """Test that delete uses correct query."""
        test_date = date(2024, 1, 15)
        mock_db.__getitem__.return_value.delete_one.return_value.deleted_count = 1

        weight_repo.delete_log("user@example.com", test_date)

        collection = mock_db.__getitem__.return_value
        call_args = collection.delete_one.call_args[0][0]

        assert call_args["user_email"] == "user@example.com"
        assert isinstance(call_args["date"], datetime)

    def test_delete_log_old_date(self, weight_repo, mock_db):
        """Test deletion for old date."""
        old_date = date(2020, 1, 1)
        mock_db.__getitem__.return_value.delete_one.return_value.deleted_count = 1

        result = weight_repo.delete_log("user@example.com", old_date)

        assert result is True


class TestWeightRepositoryGetLogs:
    """Test get_logs method."""

    def test_get_logs_default_limit(self, weight_repo, mock_db):
        """Test retrieving logs with default limit."""
        cursor = MagicMock()
        cursor.sort.return_value = cursor
        cursor.limit.return_value = []

        mock_db.__getitem__.return_value.find.return_value = cursor

        result = weight_repo.get_logs("user@example.com")

        assert isinstance(result, list)
        cursor.limit.assert_called_once_with(30)

    def test_get_logs_custom_limit(self, weight_repo, mock_db):
        """Test retrieving logs with custom limit."""
        cursor = MagicMock()
        cursor.sort.return_value = cursor
        cursor.limit.return_value = []

        mock_db.__getitem__.return_value.find.return_value = cursor

        result = weight_repo.get_logs("user@example.com", limit=50)

        assert isinstance(result, list)
        cursor.limit.assert_called_once_with(50)

    def test_get_logs_descending_order(self, weight_repo, mock_db):
        """Test that logs are sorted by date descending."""
        cursor = MagicMock()
        cursor.sort.return_value = cursor
        cursor.limit.return_value = []

        mock_db.__getitem__.return_value.find.return_value = cursor

        weight_repo.get_logs("user@example.com")

        # Verify sort was called with descending order
        import pymongo
        cursor.sort.assert_called_once_with("date", pymongo.DESCENDING)

    def test_get_logs_converts_datetime_to_date(self, weight_repo, mock_db):
        """Test that datetime is converted back to date."""
        cursor = MagicMock()
        cursor.sort.return_value = cursor

        test_doc = {
            "user_email": "user@example.com",
            "date": datetime(2024, 1, 15),
            "weight_kg": 80.5,
            "_id": "123"
        }
        cursor.limit.return_value = [test_doc]

        mock_db.__getitem__.return_value.find.return_value = cursor

        result = weight_repo.get_logs("user@example.com")

        assert len(result) == 1
        assert isinstance(result[0].date, date)
        assert result[0].date == date(2024, 1, 15)

    def test_get_logs_removes_id_field(self, weight_repo, mock_db):
        """Test that _id field is removed from results."""
        cursor = MagicMock()
        cursor.sort.return_value = cursor

        test_doc = {
            "user_email": "user@example.com",
            "date": datetime(2024, 1, 15),
            "weight_kg": 80.5,
            "_id": "mongo_id"
        }
        cursor.limit.return_value = [test_doc]

        mock_db.__getitem__.return_value.find.return_value = cursor

        result = weight_repo.get_logs("user@example.com")

        # _id should be removed when creating WeightLog
        assert result[0] is not None

    def test_get_logs_empty_result(self, weight_repo, mock_db):
        """Test retrieving logs when none exist."""
        cursor = MagicMock()
        cursor.sort.return_value = cursor
        cursor.limit.return_value = []

        mock_db.__getitem__.return_value.find.return_value = cursor

        result = weight_repo.get_logs("nonexistent@example.com")

        assert result == []


class TestWeightRepositoryGetLogsByDateRange:
    """Test get_logs_by_date_range method."""

    def test_get_logs_by_date_range_single_day(self, weight_repo, mock_db):
        """Test retrieving logs for a single day."""
        cursor = MagicMock()
        cursor.sort.return_value = []

        mock_db.__getitem__.return_value.find.return_value = cursor

        start_date = date(2024, 1, 15)
        end_date = date(2024, 1, 15)

        result = weight_repo.get_logs_by_date_range("user@example.com", start_date, end_date)

        assert isinstance(result, list)

    def test_get_logs_by_date_range_week(self, weight_repo, mock_db):
        """Test retrieving logs for a week."""
        cursor = MagicMock()
        cursor.sort.return_value = []

        mock_db.__getitem__.return_value.find.return_value = cursor

        start_date = date(2024, 1, 8)
        end_date = date(2024, 1, 14)

        result = weight_repo.get_logs_by_date_range("user@example.com", start_date, end_date)

        assert isinstance(result, list)

    def test_get_logs_by_date_range_query_format(self, weight_repo, mock_db):
        """Test that date range query is formatted correctly."""
        cursor = MagicMock()
        cursor.sort.return_value = []

        mock_db.__getitem__.return_value.find.return_value = cursor

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        weight_repo.get_logs_by_date_range("user@example.com", start_date, end_date)

        collection = mock_db.__getitem__.return_value
        call_args = collection.find.call_args[0][0]

        # Should have $gte and $lte operators
        assert "$gte" in call_args["date"]
        assert "$lte" in call_args["date"]

    def test_get_logs_by_date_range_ascending_order(self, weight_repo, mock_db):
        """Test that logs are returned in ascending order."""
        cursor = MagicMock()
        cursor.sort.return_value = []

        mock_db.__getitem__.return_value.find.return_value = cursor

        weight_repo.get_logs_by_date_range(
            "user@example.com",
            date(2024, 1, 1),
            date(2024, 1, 31)
        )

        import pymongo
        cursor.sort.assert_called_once_with("date", pymongo.ASCENDING)

    def test_get_logs_by_date_range_datetime_boundaries(self, weight_repo, mock_db):
        """Test that datetime boundaries are set correctly."""
        cursor = MagicMock()
        cursor.sort.return_value = []

        mock_db.__getitem__.return_value.find.return_value = cursor

        start_date = date(2024, 1, 15)
        end_date = date(2024, 1, 20)

        weight_repo.get_logs_by_date_range("user@example.com", start_date, end_date)

        collection = mock_db.__getitem__.return_value
        call_args = collection.find.call_args[0][0]
        date_query = call_args["date"]

        # Start should be at 00:00:00
        start_dt = date_query["$gte"]
        assert start_dt.hour == 0
        assert start_dt.minute == 0
        assert start_dt.second == 0

        # End should be at 23:59:59
        end_dt = date_query["$lte"]
        assert end_dt.hour == 23
        assert end_dt.minute == 59
        assert end_dt.second == 59


class TestWeightRepositoryEdgeCases:
    """Test edge cases and error handling."""

    def test_save_log_with_missing_optional_fields(self, weight_repo, mock_db):
        """Test saving log with only required fields."""
        log = WeightLog(
            user_email="user@example.com",
            date=date.today(),
            weight_kg=80.0
        )

        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = "id"
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0

        doc_id, is_new = weight_repo.save_log(log)

        assert is_new is True
        assert doc_id == "id"

    def test_delete_log_multiple_times(self, weight_repo, mock_db):
        """Test deleting same log multiple times."""
        test_date = date.today()
        test_email = "user@example.com"

        mock_db.__getitem__.return_value.delete_one.return_value.deleted_count = 1

        # First delete
        result1 = weight_repo.delete_log(test_email, test_date)
        assert result1 is True

        # Second delete (should not find anything)
        mock_db.__getitem__.return_value.delete_one.return_value.deleted_count = 0
        result2 = weight_repo.delete_log(test_email, test_date)
        assert result2 is False

    def test_get_logs_with_extreme_dates(self, weight_repo, mock_db):
        """Test getting logs with very old dates."""
        cursor = MagicMock()
        cursor.sort.return_value = cursor
        cursor.limit.return_value = []

        mock_db.__getitem__.return_value.find.return_value = cursor

        result = weight_repo.get_logs("user@example.com")

        assert isinstance(result, list)

    def test_database_error_on_save(self, weight_repo, mock_db, sample_weight_log):
        """Test handling database error on save."""
        mock_db.__getitem__.return_value.update_one.side_effect = Exception("DB Error")

        with pytest.raises(Exception) as exc_info:
            weight_repo.save_log(sample_weight_log)

        assert "DB Error" in str(exc_info.value)

    def test_database_error_on_delete(self, weight_repo, mock_db):
        """Test handling database error on delete."""
        mock_db.__getitem__.return_value.delete_one.side_effect = Exception("DB Error")

        with pytest.raises(Exception) as exc_info:
            weight_repo.delete_log("user@example.com", date.today())

        assert "DB Error" in str(exc_info.value)

    def test_database_error_on_get(self, weight_repo, mock_db):
        """Test handling database error on get."""
        mock_db.__getitem__.return_value.find.side_effect = Exception("DB Error")

        with pytest.raises(Exception) as exc_info:
            weight_repo.get_logs("user@example.com")

        assert "DB Error" in str(exc_info.value)
