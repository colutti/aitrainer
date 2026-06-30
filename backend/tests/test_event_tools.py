"""Tests for event management tools."""

from copy import deepcopy
from unittest.mock import MagicMock, patch
from bson import ObjectId
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


class FakeUpdateResult:
    def __init__(self, *, modified_count: int = 0) -> None:
        self.modified_count = modified_count


class FakeDeleteResult:
    def __init__(self, *, deleted_count: int = 0) -> None:
        self.deleted_count = deleted_count


class FakeInsertResult:
    def __init__(self, inserted_id: ObjectId) -> None:
        self.inserted_id = inserted_id


class FakeCursor:
    def __init__(self, docs: list[dict]) -> None:
        self._docs = docs

    def sort(self, field: str, direction: int):
        reverse = direction < 0
        self._docs.sort(
            key=lambda doc: (
                doc.get(field) is not None,
                doc.get(field) if doc.get(field) is not None else "",
            ),
            reverse=reverse,
        )
        return self

    def __iter__(self):
        return iter([deepcopy(doc) for doc in self._docs])


class FakeCollection:
    def __init__(self) -> None:
        self.docs: list[dict] = []

    def create_index(self, *_args, **_kwargs) -> None:
        return None

    def _matches(self, doc: dict, query: dict) -> bool:
        for key, value in query.items():
            if key == "$or":
                return any(self._matches(doc, branch) for branch in value)
            current = doc.get(key)
            if isinstance(value, dict):
                if "$gte" in value and current < value["$gte"]:
                    return False
                continue
            if key == "_id":
                if str(current) != str(value):
                    return False
                continue
            if current != value:
                return False
        return True

    def insert_one(self, data: dict) -> FakeInsertResult:
        inserted_id = ObjectId()
        self.docs.append({"_id": inserted_id, **deepcopy(data)})
        return FakeInsertResult(inserted_id)

    def find(self, query: dict) -> FakeCursor:
        return FakeCursor(
            [deepcopy(doc) for doc in self.docs if self._matches(doc, query)]
        )

    def update_one(self, query: dict, update: dict) -> FakeUpdateResult:
        for doc in self.docs:
            if self._matches(doc, query):
                original = deepcopy(doc)
                for key, value in update.get("$set", {}).items():
                    doc[key] = deepcopy(value)
                return FakeUpdateResult(modified_count=0 if doc == original else 1)
        return FakeUpdateResult(modified_count=0)

    def delete_one(self, query: dict) -> FakeDeleteResult:
        for index, doc in enumerate(self.docs):
            if self._matches(doc, query):
                del self.docs[index]
                return FakeDeleteResult(deleted_count=1)
        return FakeDeleteResult(deleted_count=0)


class FakeDatabase:
    def __init__(self) -> None:
        self._collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self._collections:
            self._collections[name] = FakeCollection()
        return self._collections[name]


class TestCreateEventTool:
    """Tests for create_event_tool."""

    @patch("src.services.event_tools.EventRepository")
    def test_create_event_tool_returns_success_message(self, mock_repo_class, mock_db, user_email):
        """Test that create_event_tool returns success message with event ID."""
        mock_repo = MagicMock()
        mock_repo.save_event.return_value = "event-123"
        mock_repo_class.return_value = mock_repo

        tool = create_create_event_tool(mock_db, user_email)
        # Local tools need to be invoked with invoke() or use .func()
        result = tool.invoke({
            "title": "Test Event",
            "description": "Test",
            "date": "2025-12-01",
            "recurrence": "none"
        })

        assert isinstance(result, str)
        assert "event-123" in result or "sucesso" in result.lower() or "criado" in result.lower()

    @patch("src.services.event_tools.EventRepository")
    def test_create_event_tool_rejects_invalid_date(self, mock_repo_class, mock_db, user_email):
        """Test that create_event_tool returns error for invalid date format."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        tool = create_create_event_tool(mock_db, user_email)
        result = tool.invoke({
            "title": "Test",
            "date": "01/12/2025",  # wrong format
        })

        assert isinstance(result, str)
        assert "❌" in result or "erro" in result.lower() or "inválid" in result.lower()
        mock_repo.save_event.assert_not_called()

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

    @patch("src.services.event_tools.EventRepository")
    def test_update_event_tool_rejects_invalid_date(self, mock_repo_class, mock_db, user_email):
        """Test that update_event_tool rejects invalid date format."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        tool = create_update_event_tool(mock_db, user_email)
        result = tool.invoke({"event_id": "event-123", "date": "01/12/2025"})

        assert isinstance(result, str)
        assert "❌" in result or "inválid" in result.lower()
        # Should NOT call repository
        mock_repo.update_event.assert_not_called()

    @patch("src.services.event_tools.EventRepository")
    def test_update_event_tool_clears_date_with_flag(self, mock_repo_class, mock_db, user_email):
        """Test that update_event_tool can clear date with clear_date=True."""
        mock_repo = MagicMock()
        mock_repo.update_event.return_value = True
        mock_repo_class.return_value = mock_repo

        tool = create_update_event_tool(mock_db, user_email)
        tool.invoke({"event_id": "event-123", "date": "NONE"})

        call_args = mock_repo.update_event.call_args
        _, _, update_data = call_args[0]

        assert "date" in update_data
        assert update_data["date"] is None


def test_event_tools_stateful_roundtrip_create_list_update_clear_date_and_delete():
    database = FakeDatabase()
    owner_tool_create = create_create_event_tool(database, "owner@example.com")
    owner_tool_list = create_list_events_tool(database, "owner@example.com")
    owner_tool_update = create_update_event_tool(database, "owner@example.com")
    owner_tool_delete = create_delete_event_tool(database, "owner@example.com")
    other_user_delete = create_delete_event_tool(database, "other@example.com")

    with patch("src.services.event_tools.datetime") as mock_datetime:
        mock_datetime.now.return_value.isoformat.return_value = "2026-07-01T10:00:00"

        create_result = owner_tool_create.invoke(
            {
                "title": "Check-in de peso",
                "description": "Revisar progresso semanal",
                "date": "2099-07-10",
                "recurrence": "weekly",
            }
        )

    assert "✅" in create_result
    assert "Check-in de peso" in create_result
    created_event_id = create_result.split("ID: ")[-1].strip()

    no_deadline_result = owner_tool_create.invoke(
        {
            "title": "Lembrar da água",
            "description": "Meta aberta",
            "recurrence": "monthly",
        }
    )
    assert "✅" in no_deadline_result
    second_event_id = no_deadline_result.split("ID: ")[-1].strip()

    list_before_update = owner_tool_list.invoke({})
    assert "Check-in de peso" in list_before_update
    assert "Lembrar da água" in list_before_update
    assert "2099-07-10" in list_before_update
    assert second_event_id in list_before_update

    update_result = owner_tool_update.invoke(
        {
            "event_id": created_event_id,
            "title": "Check-in quinzenal",
            "description": "Revisar peso, medidas e sono",
            "date": "NONE",
            "recurrence": "monthly",
        }
    )
    assert "✅" in update_result

    list_after_update = owner_tool_list.invoke({})
    assert "Check-in quinzenal" in list_after_update
    assert "Revisar peso, medidas e sono" in list_after_update
    assert "🔄 monthly" in list_after_update
    assert "📅 Sem prazo" in list_after_update
    assert "2099-07-10" not in list_after_update

    invalid_update = owner_tool_update.invoke(
        {"event_id": created_event_id, "date": "10/07/2099"}
    )
    assert "❌" in invalid_update

    unauthorized_delete = other_user_delete.invoke({"event_id": created_event_id})
    assert "❌" in unauthorized_delete

    delete_result = owner_tool_delete.invoke({"event_id": created_event_id})
    assert "✅" in delete_result

    final_list = owner_tool_list.invoke({})
    assert "Check-in quinzenal" not in final_list
    assert "Lembrar da água" in final_list

    delete_second = owner_tool_delete.invoke({"event_id": second_event_id})
    assert "✅" in delete_second
    empty_list = owner_tool_list.invoke({})
    assert "não tem eventos" in empty_list.lower() or "nenhum" in empty_list.lower()
