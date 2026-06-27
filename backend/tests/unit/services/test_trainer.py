"""Tests for the AITrainerBrain facade."""

from __future__ import annotations

from datetime import datetime

import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock

from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender
from src.api.models.user_profile import UserProfile
from src.prompts.prompt_template import PROMPT_TEMPLATE
from src.services.trainer import AITrainerBrain


@pytest.fixture
def brain():
    """Create facade with mocked database."""
    return AITrainerBrain(database=MagicMock())


def test_get_chat_history_sanitizes_only_trainer_internal_tags(brain):
    user_email = "test@test.com"
    brain.database.get_chat_history.return_value = [
        ChatHistory(
            text='<msg data="03/04" hora="14:57"><treinador name="Atlas">Resposta antiga</treinador></msg>',
            sender=Sender.TRAINER,
            timestamp="2026-04-03T14:57:00",
        ),
        ChatHistory(
            text='Dados do usuário: <msg data="arquivo.csv">linha 1</msg>',
            sender=Sender.STUDENT,
            timestamp="2026-04-03T14:58:00",
        ),
    ]

    messages = brain.get_chat_history(user_email, limit=20, offset=0)

    assert messages[0].text == "Resposta antiga"
    assert messages[1].text == 'Dados do usuário: <msg data="arquivo.csv">linha 1</msg>'


def test_format_sse_event_serializes_payload():
    chunk = AITrainerBrain.format_sse_event("done", {"text": "oi", "persisted": True})

    assert chunk == 'event: done\ndata: {"text":"oi","persisted":true}\n\n'


def test_add_to_mongo_history_persists_pair_in_one_batch(brain):
    """Conversation persistence delegates the pair to one repository operation."""
    brain.add_to_mongo_history(
        "test@test.com",
        "Pode atualizar o plano",
        "Plano atualizado",
        {"trainer_type": "atlas"},
    )

    brain.database.add_many_to_history.assert_called_once()
    messages, session_id, trainer_type = brain.database.add_many_to_history.call_args.args
    assert session_id == "test@test.com"
    assert trainer_type == "atlas"
    assert [message.sender for message in messages] == [Sender.STUDENT, Sender.TRAINER]
    brain.database.add_to_history.assert_not_called()


def test_check_message_limits_blocks_free_daily_limit(brain):
    profile = UserProfile(
        email="test@test.com",
        gender="Masculino",
        age=30,
        height=175,
        goal="manter rotina",
        goal_type="maintain",
        subscription_plan="Free",
        messages_sent_today=20,
        last_message_date=datetime.now().strftime("%Y-%m-%d"),
    )

    with pytest.raises(HTTPException) as exc_info:
        brain.check_message_limits(profile)

    assert exc_info.value.detail == "DAILY_LIMIT_REACHED"


def test_prompt_preserves_weekly_schedule_frequency_rule():
    """Pending prompt hardening from the worktree must remain in place."""
    assert "frequency_per_week" in PROMPT_TEMPLATE
    assert "weekly_schedule" in PROMPT_TEMPLATE
    assert "corresponder EXATAMENTE" in PROMPT_TEMPLATE
