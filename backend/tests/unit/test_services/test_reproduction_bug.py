import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from src.services.history_compactor import HistoryCompactor
from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender
from src.api.models.user_profile import UserProfile

@pytest.mark.asyncio
async def test_compact_history_identifies_student_messages():
    # Setup mocks
    db = MagicMock()
    llm = AsyncMock()
    compactor = HistoryCompactor(db, llm)
    
    user_email = "test@example.com"
    profile = UserProfile(
        email=user_email,
        long_term_summary="{}",
        last_compaction_timestamp=None,
        gender="Masculino",
        age=30,
        weight=70,
        height=175,
        goal="Test",
        goal_type="maintain"
    )
    db.get_user_profile.return_value = profile
    
    # Create 70 messages to exceed compaction_threshold (60)
    messages = []
    for i in range(70):
        messages.append(ChatHistory(
            sender=Sender.STUDENT,
            text=f"Mensagem relevante do aluno {i} que deve ser detectada",
            timestamp=datetime.now().isoformat()
        ))
    
    db.get_chat_history.return_value = messages
    db.update_user_profile_fields.return_value = True
    
    async def mock_gen(*args, **kwargs):
        yield '{"health": "ok", "restrictions": "none"}'
    llm.stream_simple.side_effect = mock_gen

    # Run compaction
    await compactor.compact_history(user_email)
    
    # Verify that the LLM was called with new lines
    # If the bug was present, new_lines would be empty and LLM wouldn't be called
    call_args = llm.stream_simple.call_args
    assert call_args is not None
    input_data = call_args.kwargs['input_data']
    assert "Aluno:" in input_data['new_lines']
    assert "Mensagem relevante" in input_data['new_lines']
