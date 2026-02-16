"""
Tests for the PromptBuilder service.
Verifies that prompts are built correctly and long_term_summary is injected.
"""

import pytest
from datetime import datetime
from src.services.prompt_builder import PromptBuilder
from src.api.models.user_profile import UserProfile


@pytest.fixture
def sample_profile():
    """Create a basic user profile for testing."""
    return UserProfile(
        email="test@example.com",
        goal="perder peso",
        gender="Masculino",
        age=30,
        weight=80.0,
        height=175,
        goal_type="lose",
        weekly_rate=0.5,
    )


@pytest.fixture
def sample_profile_with_summary():
    """Create a user profile with a long_term_summary."""
    return UserProfile(
        email="test@example.com",
        goal="perder peso",
        gender="Masculino",
        age=30,
        weight=80.0,
        height=175,
        goal_type="lose",
        weekly_rate=0.5,
        long_term_summary='{"goals": ["[01/02] Perder 5kg"], "preferences": ["[31/01] Treinar 2x/semana"], "health": [], "progress": [], "restrictions": []}',
    )


def test_build_input_data_returns_all_required_keys(sample_profile):
    """Verify build_input_data returns all expected keys."""
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile,
        trainer_profile_summary="Trainer: Atlas",
        user_profile_summary="User: 30y, 80kg",
        relevant_memories_str="",
        chat_history_summary="",
        formatted_history_msgs=[],
        user_input="Como vou treinar?",
        current_date="2026-02-15",
    )

    required_keys = {
        "trainer_profile",
        "user_profile",
        "user_profile_obj",
        "relevant_memories",
        "chat_history_summary",
        "chat_history",
        "user_message",
        "current_date",
        "day_of_week",
        "current_time",
    }
    assert set(input_data.keys()) >= required_keys


def test_build_input_data_uses_provided_date(sample_profile):
    """Verify provided current_date is used."""
    provided_date = "2026-01-15"
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile,
        trainer_profile_summary="",
        user_profile_summary="",
        relevant_memories_str="",
        chat_history_summary="",
        formatted_history_msgs=[],
        user_input="test",
        current_date=provided_date,
    )
    assert input_data["current_date"] == provided_date


def test_build_input_data_generates_date_when_not_provided(sample_profile):
    """Verify current_date is generated when not provided."""
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile,
        trainer_profile_summary="",
        user_profile_summary="",
        relevant_memories_str="",
        chat_history_summary="",
        formatted_history_msgs=[],
        user_input="test",
        current_date=None,
    )
    # Should be today's date in YYYY-MM-DD format
    today = datetime.now().strftime("%Y-%m-%d")
    assert input_data["current_date"] == today


def test_get_prompt_template_injects_long_term_summary(sample_profile_with_summary):
    """Verify long_term_summary is injected into the system prompt."""
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile_with_summary,
        trainer_profile_summary="Trainer",
        user_profile_summary="User",
        relevant_memories_str="",
        chat_history_summary="",
        formatted_history_msgs=[],
        user_input="test",
        current_date="2026-02-15",
    )

    prompt_template = PromptBuilder.get_prompt_template(input_data, is_telegram=False)
    rendered = prompt_template.format(**input_data)

    # Verify <historico> section is present (new XML structure)
    assert "<historico>" in rendered
    assert "</historico>" in rendered
    # Verify the summary content is there
    assert "Perder 5kg" in rendered
    assert "Treinar 2x/semana" in rendered


def test_get_prompt_template_handles_null_summary(sample_profile):
    """Verify no [HISTÓRICO] section when summary is None."""
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile,
        trainer_profile_summary="Trainer",
        user_profile_summary="User",
        relevant_memories_str="",
        chat_history_summary="",
        formatted_history_msgs=[],
        user_input="test",
        current_date="2026-02-15",
    )

    PromptBuilder.get_prompt_template(input_data, is_telegram=False)

    # [HISTÓRICO] section should not appear if summary is None
    # Or should appear but be empty
    assert input_data["long_term_summary_section"] == ""


def test_get_prompt_template_handles_empty_string_summary(sample_profile):
    """Verify empty string summary is handled correctly."""
    sample_profile.long_term_summary = ""
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile,
        trainer_profile_summary="Trainer",
        user_profile_summary="User",
        relevant_memories_str="",
        chat_history_summary="",
        formatted_history_msgs=[],
        user_input="test",
    )

    PromptBuilder.get_prompt_template(input_data, is_telegram=False)

    assert input_data["long_term_summary_section"] == ""


def test_get_prompt_template_adds_telegram_format(sample_profile):
    """Verify Telegram format is added when is_telegram=True."""
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile,
        trainer_profile_summary="Trainer",
        user_profile_summary="User",
        relevant_memories_str="",
        chat_history_summary="",
        formatted_history_msgs=[],
        user_input="test",
    )

    prompt_template = PromptBuilder.get_prompt_template(input_data, is_telegram=True)
    rendered = prompt_template.format(**input_data)

    assert "FORMATO TELEGRAM" in rendered


def test_get_prompt_template_no_telegram_by_default(sample_profile):
    """Verify Telegram format is NOT added by default."""
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile,
        trainer_profile_summary="Trainer",
        user_profile_summary="User",
        relevant_memories_str="",
        chat_history_summary="",
        formatted_history_msgs=[],
        user_input="test",
    )

    prompt_template = PromptBuilder.get_prompt_template(input_data, is_telegram=False)
    rendered = prompt_template.format(**input_data)

    assert "FORMATO TELEGRAM" not in rendered


def test_get_prompt_template_removes_legacy_placeholder(sample_profile):
    """Verify legacy {chat_history_summary} placeholder is removed."""
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile,
        trainer_profile_summary="Trainer",
        user_profile_summary="User",
        relevant_memories_str="",
        chat_history_summary="",
        formatted_history_msgs=[],
        user_input="test",
    )

    prompt_template = PromptBuilder.get_prompt_template(input_data, is_telegram=False)
    # Should not raise KeyError about chat_history_summary
    rendered = prompt_template.format(**input_data)
    assert isinstance(rendered, str)


def test_get_prompt_template_returns_chat_prompt_template(sample_profile):
    """Verify return type is ChatPromptTemplate."""
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile,
        trainer_profile_summary="Trainer",
        user_profile_summary="User",
        relevant_memories_str="",
        chat_history_summary="",
        formatted_history_msgs=[],
        user_input="test",
    )

    prompt_template = PromptBuilder.get_prompt_template(input_data)
    # Should be ChatPromptTemplate
    assert hasattr(prompt_template, "format_messages")
    assert hasattr(prompt_template, "format")


def test_build_input_data_passes_profile_object(sample_profile_with_summary):
    """Verify user_profile_obj is the actual profile object."""
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile_with_summary,
        trainer_profile_summary="",
        user_profile_summary="",
        relevant_memories_str="",
        chat_history_summary="",
        formatted_history_msgs=[],
        user_input="test",
    )

    assert input_data["user_profile_obj"] is sample_profile_with_summary
    assert input_data["user_profile_obj"].long_term_summary is not None
