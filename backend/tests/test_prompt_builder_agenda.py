"""
Tests for agenda injection in prompt_builder.

Tests that events are formatted and injected correctly in the prompt.
"""

from unittest.mock import MagicMock
import pytest
from src.services.prompt_builder import PromptBuilder
from src.api.models.scheduled_event import ScheduledEventWithId


@pytest.fixture
def sample_events():
    """Sample events for testing."""
    return [
        ScheduledEventWithId(
            id="1",
            user_email="test@example.com",
            title="Emagrecer para o verão",
            date="2025-12-01",
            recurrence="none",
            active=True,
            created_at="2025-02-24T10:00:00",
        ),
        ScheduledEventWithId(
            id="2",
            user_email="test@example.com",
            title="Check-in de peso",
            date=None,
            recurrence="weekly",
            active=True,
            created_at="2025-02-24T10:00:00",
        ),
    ]


class TestAgendaFormatting:
    """Tests for agenda event formatting."""

    def test_format_agenda_with_events(self, sample_events):
        """Test that events are formatted into agenda string."""
        formatted = PromptBuilder._format_agenda_section(sample_events)

        assert isinstance(formatted, str)
        # Should contain event titles
        assert "Emagrecer para o verão" in formatted
        assert "Check-in de peso" in formatted
        # Should contain date info
        assert "2025-12-01" in formatted

    def test_format_agenda_empty_list(self):
        """Test that empty event list returns empty string."""
        formatted = PromptBuilder._format_agenda_section([])

        assert formatted == ""

    def test_format_agenda_with_recurrence(self, sample_events):
        """Test that recurrence is shown for recurring events."""
        formatted = PromptBuilder._format_agenda_section(sample_events)

        # Weekly event should show recurrence
        assert "weekly" in formatted.lower() or "semanal" in formatted.lower()


class TestInputDataWithAgenda:
    """Tests for build_input_data with agenda_events."""

    def test_build_input_data_includes_agenda_section(self, sample_events):
        """Test that build_input_data includes formatted agenda."""
        profile = MagicMock()
        profile.long_term_summary = None

        input_data = PromptBuilder.build_input_data(
            profile=profile,
            trainer_profile_summary="Test trainer",
            user_profile_summary="Test profile",
            relevant_memories_str="",
            chat_history_summary="",
            formatted_history_msgs=[],
            user_input="Hello",
            agenda_events=sample_events,
        )

        assert "agenda_section" in input_data
        assert "Emagrecer para o verão" in input_data["agenda_section"]

    def test_build_input_data_empty_agenda(self):
        """Test that build_input_data with empty agenda returns empty section."""
        profile = MagicMock()
        profile.long_term_summary = None

        input_data = PromptBuilder.build_input_data(
            profile=profile,
            trainer_profile_summary="Test trainer",
            user_profile_summary="Test profile",
            relevant_memories_str="",
            chat_history_summary="",
            formatted_history_msgs=[],
            user_input="Hello",
            agenda_events=[],
        )

        assert input_data.get("agenda_section") == ""
