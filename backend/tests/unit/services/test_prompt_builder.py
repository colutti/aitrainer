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
        formatted_history_msgs=[],
        user_input="Como vou treinar?",
        current_date="2026-02-15",
    )

    required_keys = {
        "trainer_profile",
        "user_profile",
        "user_profile_obj",
        "chat_history",
        "user_message",
        "current_date",
        "day_of_week",
        "current_time",
        "trainer_name",
        "user_name",
        "user_timezone",
        "runtime_context",
        "runtime_context_json",
    }
    assert set(input_data.keys()) >= required_keys


def test_build_input_data_uses_provided_date(sample_profile):
    """Verify provided current_date is used."""
    provided_date = "2026-01-15"
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile,
        trainer_profile_summary="",
        user_profile_summary="",
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
        formatted_history_msgs=[],
        user_input="test",
        current_date=None,
    )
    # Should be today's date in YYYY-MM-DD format
    today = datetime.now().strftime("%Y-%m-%d")
    assert input_data["current_date"] == today


def test_get_prompt_template_does_not_add_legacy_summary_block(sample_profile_with_summary):
    """Verify prompt does not include legacy summary tags."""
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile_with_summary,
        trainer_profile_summary="Trainer",
        user_profile_summary="User",
        formatted_history_msgs=[],
        user_input="test",
        current_date="2026-02-15",
    )

    prompt_template = PromptBuilder.get_prompt_template(input_data, is_telegram=False)
    rendered = prompt_template.format(**input_data)

    assert "<resumo_conversas>" not in rendered
    assert "</resumo_conversas>" not in rendered
    assert "## Resumo de conversas anteriores" not in rendered


def test_get_prompt_template_handles_null_summary(sample_profile):
    """Verify no [HISTÓRICO] section when summary is None."""
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile,
        trainer_profile_summary="Trainer",
        user_profile_summary="User",
        formatted_history_msgs=[],
        user_input="test",
        current_date="2026-02-15",
    )

    PromptBuilder.get_prompt_template(input_data, is_telegram=False)

    rendered = PromptBuilder.get_prompt_template(
        input_data, is_telegram=False
    ).format(**input_data)
    assert "<resumo_conversas>" not in rendered


def test_get_prompt_template_handles_empty_string_summary(sample_profile):
    """Verify empty string summary is handled correctly."""
    sample_profile.long_term_summary = ""
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile,
        trainer_profile_summary="Trainer",
        user_profile_summary="User",
        formatted_history_msgs=[],
        user_input="test",
    )

    rendered = PromptBuilder.get_prompt_template(
        input_data, is_telegram=False
    ).format(**input_data)
    assert "<resumo_conversas>" not in rendered


def test_get_prompt_template_adds_telegram_format(sample_profile):
    """Verify Telegram channel is encoded into runtime context."""
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile,
        trainer_profile_summary="Trainer",
        user_profile_summary="User",
        formatted_history_msgs=[],
        user_input="test",
    )

    prompt_template = PromptBuilder.get_prompt_template(input_data, is_telegram=True)
    rendered = prompt_template.format(**input_data)

    assert '"channel": "telegram"' in rendered


def test_get_prompt_template_no_telegram_by_default(sample_profile):
    """Verify app channel is the default runtime context channel."""
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile,
        trainer_profile_summary="Trainer",
        user_profile_summary="User",
        formatted_history_msgs=[],
        user_input="test",
    )

    prompt_template = PromptBuilder.get_prompt_template(input_data, is_telegram=False)
    rendered = prompt_template.format(**input_data)

    assert '"channel": "app"' in rendered


def test_get_prompt_template_renders_without_legacy_summary_placeholder(sample_profile):
    """Verify prompt renders without requiring any summary placeholder."""
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile,
        trainer_profile_summary="Trainer",
        user_profile_summary="User",
        formatted_history_msgs=[],
        user_input="test",
    )

    prompt_template = PromptBuilder.get_prompt_template(input_data, is_telegram=False)
    rendered = prompt_template.format(**input_data)
    assert isinstance(rendered, str)


def test_get_prompt_template_returns_chat_prompt_template(sample_profile):
    """Verify return type is ChatPromptTemplate."""
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile,
        trainer_profile_summary="Trainer",
        user_profile_summary="User",
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
        formatted_history_msgs=[],
        user_input="test",
    )

    assert input_data["user_profile_obj"] is sample_profile_with_summary
    assert input_data["user_profile_obj"].long_term_summary is not None


def test_build_input_data_extracts_trainer_name(sample_profile):
    """Verify trainer_name is extracted from trainer_profile_summary."""
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile,
        trainer_profile_summary="## Trainer\n**Nome:** Atlas\n**Gender:** Male",
        user_profile_summary="User",
        formatted_history_msgs=[],
        user_input="test",
    )
    assert input_data["trainer_name"] == "Atlas"


def test_build_input_data_uses_display_name(sample_profile):
    """Verify user_name uses display_name when available."""
    sample_profile.display_name = "Rafael"
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile,
        trainer_profile_summary="Trainer",
        user_profile_summary="User",
        formatted_history_msgs=[],
        user_input="test",
    )
    assert input_data["user_name"] == "Rafael"


def test_build_input_data_defaults_user_name(sample_profile):
    """Verify user_name defaults to 'Aluno' when no display_name."""
    sample_profile.display_name = None
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile,
        trainer_profile_summary="Trainer",
        user_profile_summary="User",
        formatted_history_msgs=[],
        user_input="test",
    )
    assert input_data["user_name"] == "Aluno"


def test_prompt_renders_security_section(sample_profile):
    """Verify runtime context is rendered in system message."""
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile,
        trainer_profile_summary="Trainer",
        user_profile_summary="User",
        formatted_history_msgs=[],
        user_input="test",
    )
    prompt = PromptBuilder.get_prompt_template(input_data)
    rendered = prompt.format(**input_data)
    assert "RUNTIME_CONTEXT_JSON (PROMPT_CONTEXT_V1)" in rendered
    assert '"contract_version": "prompt_context_v1"' in rendered


def test_prompt_renders_new_section_names(sample_profile):
    """Verify context data is available in rendered prompt."""
    sample_event = type(
        "Evt",
        (),
        {"date": "2026-04-10", "title": "Revisar plano", "recurrence": "none"},
    )()
    input_data = PromptBuilder.build_input_data(
        profile=sample_profile,
        trainer_profile_summary="Trainer",
        user_profile_summary="User",
        formatted_history_msgs=[],
        user_input="test",
        agenda_events=[sample_event],
    )
    prompt = PromptBuilder.get_prompt_template(input_data)
    rendered = prompt.format(**input_data)
    assert '"trainer"' in rendered
    assert "Revisar plano" in rendered
