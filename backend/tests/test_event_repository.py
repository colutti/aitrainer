"""
Tests for EventRepository (TDD: failing first).

Tests CRUD operations and date filtering for scheduled events.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest
from src.api.models.scheduled_event import ScheduledEvent
from src.repositories.event_repository import EventRepository


@pytest.fixture
def sample_event():
    """Sample scheduled event for testing."""
    return ScheduledEvent(
        user_email="test@example.com",
        title="Emagrecer para o verão",
        description="Meta de -8kg até dezembro",
        date="2025-12-01",
        recurrence="none",
        active=True,
        created_at=datetime.now().isoformat(),
    )


class TestEventRepositoryDateFiltering:
    """Tests for date filtering in get_active_events."""

    @patch("src.repositories.event_repository.ObjectId")
    def test_get_active_events_builds_correct_query(self, mock_object_id):
        """Test that get_active_events builds the correct MongoDB query."""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection

        # Setup mock chain
        mock_cursor = MagicMock()
        mock_collection.find.return_value = mock_cursor
        mock_cursor.sort.return_value = []

        repo = EventRepository(mock_db)
        repo.get_active_events("test@example.com")

        # Verify find was called with correct query
        call_args = mock_collection.find.call_args
        assert call_args is not None

        query = call_args[0][0]
        assert query["user_email"] == "test@example.com"
        assert query["active"] is True
        assert "$or" in query

    @patch("src.repositories.event_repository.ObjectId")
    def test_get_active_events_filters_past_dates(self, mock_object_id):
        """Test that query filters out past dates correctly."""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection

        mock_cursor = MagicMock()
        mock_collection.find.return_value = mock_cursor
        mock_cursor.sort.return_value = []

        repo = EventRepository(mock_db)
        repo.get_active_events("test@example.com")

        call_args = mock_collection.find.call_args
        query = call_args[0][0]

        # $or should have two conditions: date=None or date >= today
        or_conditions = query.get("$or", [])
        assert len(or_conditions) == 2

        # First should be {date: None}
        assert or_conditions[0] == {"date": None}

        # Second should have $gte
        assert "$gte" in or_conditions[1].get("date", {})


class TestEventRepositorySave:
    """Tests for saving events."""

    def test_save_event_calls_insert_one(self, sample_event):
        """Test that save_event calls collection.insert_one."""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.insert_one.return_value.inserted_id = "event-123"

        repo = EventRepository(mock_db)
        event_id = repo.save_event(sample_event)

        assert event_id == "event-123"
        mock_collection.insert_one.assert_called_once()

    def test_save_event_stores_event_data(self, sample_event):
        """Test that save_event stores all event fields."""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.insert_one.return_value.inserted_id = "event-123"

        repo = EventRepository(mock_db)
        repo.save_event(sample_event)

        call_args = mock_collection.insert_one.call_args
        stored_data = call_args[0][0]

        assert stored_data["user_email"] == "test@example.com"
        assert stored_data["title"] == "Emagrecer para o verão"
        assert stored_data["date"] == "2025-12-01"


class TestEventRepositoryDelete:
    """Tests for deleting events."""

    @patch("src.repositories.event_repository.ObjectId")
    def test_delete_event_returns_true_on_success(self, mock_object_id):
        """Test that delete_event returns True when event is deleted."""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.delete_one.return_value.deleted_count = 1

        repo = EventRepository(mock_db)
        result = repo.delete_event("event-123", "test@example.com")

        assert result is True
        mock_collection.delete_one.assert_called_once()

    @patch("src.repositories.event_repository.ObjectId")
    def test_delete_event_returns_false_when_not_found(self, mock_object_id):
        """Test that delete_event returns False when event not found."""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.delete_one.return_value.deleted_count = 0

        repo = EventRepository(mock_db)
        result = repo.delete_event("nonexistent", "test@example.com")

        assert result is False

    @patch("src.repositories.event_repository.ObjectId")
    def test_delete_event_checks_user_ownership(self, mock_object_id):
        """Test that delete_event verifies user ownership."""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.delete_one.return_value.deleted_count = 1

        repo = EventRepository(mock_db)
        repo.delete_event("event-123", "test@example.com")

        call_args = mock_collection.delete_one.call_args
        query = call_args[0][0]

        # Query should include user_email for authorization
        assert query.get("user_email") == "test@example.com"


class TestEventRepositoryListAll:
    """Tests for listing all events."""

    @patch("src.repositories.event_repository.ObjectId")
    def test_list_all_events_queries_by_user(self, mock_object_id):
        """Test that list_all_events queries by user_email."""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection

        mock_cursor = MagicMock()
        mock_collection.find.return_value = mock_cursor
        mock_cursor.sort.return_value = []

        repo = EventRepository(mock_db)
        repo.list_all_events("test@example.com")

        call_args = mock_collection.find.call_args
        query = call_args[0][0]

        assert query.get("user_email") == "test@example.com"

    @patch("src.repositories.event_repository.ObjectId")
    def test_list_all_events_includes_all_states(self, mock_object_id):
        """Test that list_all_events includes past and inactive events."""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection

        mock_cursor = MagicMock()
        mock_collection.find.return_value = mock_cursor
        mock_cursor.sort.return_value = []

        repo = EventRepository(mock_db)
        repo.list_all_events("test@example.com")

        # list_all should NOT have active=True filter
        call_args = mock_collection.find.call_args
        query = call_args[0][0]

        assert "active" not in query or query.get("active") is not True
