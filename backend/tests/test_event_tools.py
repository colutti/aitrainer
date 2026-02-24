"""
Tests for event management tools.

Tests that tools return properly formatted strings for the AI agent.
"""

from unittest.mock import MagicMock, patch
import pytest
from src.services.event_tools import (
    create_create_event_tool,
    create_list_events_tool,
    create_delete_event_tool,
    create_update_event_tool,
)
from src.api.models.scheduled_event import ScheduledEventWithId


@pytest.fixture
def mock_db():
    """Mock database."""
    return MagicMock()


@pytest.fixture
def user_email():
    """Test user email."""
    return "test@example.com"


class TestCreateEventTool:
    """Tests for create_event_tool."""

    @patch("src.services.event_tools.EventRepository")
    def test_create_event_tool_returns_success_message(self, mock_repo_class, mock_db, user_email):
        """Test that create_event_tool returns success message with event ID."""
        mock_repo = MagicMock()
        mock_repo.save_event.return_value = "event-123"
        mock_repo_class.return_value = mock_repo

        tool = create_create_event_tool(mock_db, user_email)
        # LangChain tools need to be invoked with invoke() or use .func()
        result = tool.invoke({
            "title": "Test Event",
            "description": "Test",
            "date": "2025-12-01",
            "recurrence": "none"
        })

        assert isinstance(result, str)
        assert "event-123" in result or "sucesso" in result.lower() or "criado" in result.lower()

    @patch("src.services.event_tools.EventRepository")
    def test_create_event_tool_passes_title_to_repo(self, mock_repo_class, mock_db, user_email):
        """Test that create_event_tool passes all fields to repository."""
        mock_repo = MagicMock()
        mock_repo.save_event.return_value = "event-123"
        mock_repo_class.return_value = mock_repo

        tool = create_create_event_tool(mock_db, user_email)
        tool.invoke({
            "title": "Emagrecer",
            "description": "Meta",
            "date": "2025-12-01",
            "recurrence": "none"
        })

        mock_repo.save_event.assert_called_once()
        call_args = mock_repo.save_event.call_args[0][0]
        assert call_args.title == "Emagrecer"
        assert call_args.date == "2025-12-01"


class TestListEventsTool:
    """Tests for list_events_tool."""

    @patch("src.services.event_tools.EventRepository")
    def test_list_events_tool_returns_formatted_list(self, mock_repo_class, mock_db, user_email):
        """Test that list_events_tool returns formatted event list."""
        mock_repo = MagicMock()
        mock_events = [
            ScheduledEventWithId(
                id="1",
                user_email=user_email,
                title="Event 1",
                date="2025-12-01",
                recurrence="none",
                active=True,
                created_at="2025-02-24T10:00:00",
            ),
            ScheduledEventWithId(
                id="2",
                user_email=user_email,
                title="Event 2",
                date=None,
                recurrence="weekly",
                active=True,
                created_at="2025-02-24T10:00:00",
            ),
        ]
        mock_repo.get_active_events.return_value = mock_events
        mock_repo_class.return_value = mock_repo

        tool = create_list_events_tool(mock_db, user_email)
        result = tool.invoke({})

        assert isinstance(result, str)
        # Should contain event titles
        assert "Event 1" in result
        assert "Event 2" in result
        # Should contain date info
        assert "2025-12-01" in result

    @patch("src.services.event_tools.EventRepository")
    def test_list_events_tool_shows_no_events_message(self, mock_repo_class, mock_db, user_email):
        """Test that list_events_tool shows message when no events."""
        mock_repo = MagicMock()
        mock_repo.get_active_events.return_value = []
        mock_repo_class.return_value = mock_repo

        tool = create_list_events_tool(mock_db, user_email)
        result = tool.invoke({})

        assert isinstance(result, str)
        # Should indicate no events - check for negative phrasing
        assert ("nenhum" in result.lower() or "vazio" in result.lower()
                or "nada" in result.lower() or "não tem" in result.lower())


class TestDeleteEventTool:
    """Tests for delete_event_tool."""

    @patch("src.services.event_tools.EventRepository")
    def test_delete_event_tool_returns_success_message(self, mock_repo_class, mock_db, user_email):
        """Test that delete_event_tool returns success message."""
        mock_repo = MagicMock()
        mock_repo.delete_event.return_value = True
        mock_repo_class.return_value = mock_repo

        tool = create_delete_event_tool(mock_db, user_email)
        result = tool.invoke({"event_id": "event-123"})

        assert isinstance(result, str)
        assert "sucesso" in result.lower() or "deletado" in result.lower() or "removido" in result.lower()

    @patch("src.services.event_tools.EventRepository")
    def test_delete_event_tool_returns_error_if_not_found(self, mock_repo_class, mock_db, user_email):
        """Test that delete_event_tool returns error message if event not found."""
        mock_repo = MagicMock()
        mock_repo.delete_event.return_value = False
        mock_repo_class.return_value = mock_repo

        tool = create_delete_event_tool(mock_db, user_email)
        result = tool.invoke({"event_id": "nonexistent"})

        assert isinstance(result, str)
        assert "erro" in result.lower() or "não" in result.lower() or "não encontrado" in result.lower()


class TestUpdateEventTool:
    """Tests for update_event_tool."""

    @patch("src.services.event_tools.EventRepository")
    def test_update_event_tool_returns_success_message(self, mock_repo_class, mock_db, user_email):
        """Test that update_event_tool returns success message."""
        mock_repo = MagicMock()
        mock_repo.update_event.return_value = True
        mock_repo_class.return_value = mock_repo

        tool = create_update_event_tool(mock_db, user_email)
        result = tool.invoke({"event_id": "event-123", "title": "Updated Title"})

        assert isinstance(result, str)
        assert "sucesso" in result.lower() or "atualizado" in result.lower() or "modificado" in result.lower()

    @patch("src.services.event_tools.EventRepository")
    def test_update_event_tool_passes_update_data(self, mock_repo_class, mock_db, user_email):
        """Test that update_event_tool passes all update fields to repository."""
        mock_repo = MagicMock()
        mock_repo.update_event.return_value = True
        mock_repo_class.return_value = mock_repo

        tool = create_update_event_tool(mock_db, user_email)
        tool.invoke({
            "event_id": "event-123",
            "title": "New Title",
            "description": "New Desc",
            "date": "2025-12-31",
        })

        mock_repo.update_event.assert_called_once()
        call_args = mock_repo.update_event.call_args
        event_id, user, update_data = call_args[0]

        assert event_id == "event-123"
        assert user == user_email
        assert "title" in update_data
        assert update_data["title"] == "New Title"
