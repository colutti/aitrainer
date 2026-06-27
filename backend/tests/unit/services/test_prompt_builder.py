"""Tests for prompt builder context payloads."""

from types import SimpleNamespace

from src.services.prompt_builder import PromptBuilder


def test_build_input_data_includes_formatted_history_summary():
    profile = SimpleNamespace(timezone="UTC", display_name="Aluno")
    history = [
        SimpleNamespace(content='<msg data="30/04" hora="10:00">treinei peito</msg>'),
        SimpleNamespace(
            content=(
                '<msg data="30/04" hora="10:01">'
                '<treinador name="Atlas">boa</treinador></msg>'
            )
        ),
    ]

    data = PromptBuilder.build_input_data(
        profile=profile,
        trainer_profile_summary="**Nome:** Atlas",
        user_profile_summary="perfil",
        formatted_history_msgs=history,
        user_input="oi",
        current_date="2026-04-30",
        agenda_events=[],
        plan_snapshot=None,
        metabolism_data=None,
    )

    assert data["formatted_history"] == "\n".join(msg.content for msg in history)


def test_format_metabolism_section_shows_macro_targets():
    """Regression: calculate_macro_targets returns protein/carbs/fat keys,
    but prompt builder looked for protein_g/carbs_g/fat_g, causing
    'indisponivel' to always be shown to the trainer."""
    metabolism_data = {
        "tdee": 2500,
        "daily_target": 2200,
        "goal_type": "lose",
        "goal_weekly_rate": -0.5,
        "confidence": "medium",
        "macro_targets": {"protein": 128, "carbs": 202, "fat": 54},
    }
    result = PromptBuilder._format_metabolism_section(metabolism_data)
    assert "128" in result, "protein value should appear in formatted section"
    assert "202" in result, "carbs value should appear in formatted section"
    assert "54" in result, "fat value should appear in formatted section"
    assert "indisponivel" not in result, "should never show indisponivel when data exists"
