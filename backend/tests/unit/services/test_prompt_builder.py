"""Tests for prompt builder context payloads."""

from types import SimpleNamespace

from langchain_core.messages import AIMessage, HumanMessage

from src.services.prompt_builder import PromptBuilder


def test_build_input_data_includes_formatted_history_summary():
    profile = SimpleNamespace(timezone="UTC", display_name="Aluno")
    history = [
        HumanMessage(content='<msg data="30/04" hora="10:00">treinei peito</msg>'),
        AIMessage(
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
