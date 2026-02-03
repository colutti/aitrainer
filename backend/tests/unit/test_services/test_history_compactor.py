
import pytest
import json
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from src.services.history_compactor import HistoryCompactor
from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender
from src.api.models.user_profile import UserProfile


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.update_user_profile_fields.return_value = True
    return db


@pytest.fixture
def mock_llm_client():
    client = MagicMock()

    # Mock stream_simple to return an async generator
    async def async_gen(*args, **kwargs):
        yield "Updated Summary Content"

    client.stream_simple = MagicMock(side_effect=async_gen)
    return client


def test_history_compactor_skips_short_history(mock_db, mock_llm_client):
    """Should not compact if history is within window."""
    compactor = HistoryCompactor(mock_db, mock_llm_client)

    # Mock Profile - FULL FIELDS to satisfy Pydantic
    profile = UserProfile(
        email="test@test.com",
        goal="test",
        gender="Masculino",
        age=30,
        weight=70.0,
        height=175,
        goal_type="maintain",
        weekly_rate=0.5,
    )
    mock_db.get_user_profile.return_value = profile

    # Mock Short History (10 msgs)
    mock_db.get_chat_history.return_value = [MagicMock() for _ in range(10)]

    compactor.compact_history("test@test.com", active_window_size=20)

    # Assertions
    mock_llm_client.stream_simple.assert_not_called()
    mock_db.update_user_profile_fields.assert_not_called()


def test_history_compactor_summarizes_old_messages(mock_db, mock_llm_client):
    """Should compact messages older than window."""
    # Mock LLM to return valid JSON
    async def async_gen(*args, **kwargs):
        yield '{"preferences": []}'
    mock_llm_client.stream_simple = MagicMock(side_effect=async_gen)

    compactor = HistoryCompactor(mock_db, mock_llm_client)

    # Mock Profile
    profile = UserProfile(
        email="test@test.com",
        goal="test",
        gender="Masculino",
        age=30,
        weight=70.0,
        height=175,
        goal_type="maintain",
        weekly_rate=0.5,
    )
    mock_db.get_user_profile.return_value = profile

    # Mock Long History (30 msgs), Window (10) -> Compact 20
    # Create fake messages with timestamps (with meaningful text >= 10 chars)
    base_ts = datetime(2026, 1, 1, 10, 0)
    messages = []
    for i in range(30):
        ts = base_ts + timedelta(minutes=i)
        msg = ChatHistory(
            sender=Sender.STUDENT, text=f"This is message number {i}", timestamp=ts.isoformat()
        )
        messages.append(msg)

    mock_db.get_chat_history.return_value = messages

    # Run
    compactor.compact_history("test@test.com", active_window_size=10, compaction_threshold=20)

    # Assertions
    mock_llm_client.stream_simple.assert_called_once()
    mock_db.update_user_profile_fields.assert_called_once()

    # Check if fields were updated correctly
    updated_fields = mock_db.update_user_profile_fields.call_args[0][1]
    assert "preferences" in updated_fields["long_term_summary"]
    # The last compacted message should be index 19 (since 20-29 are active window)
    expected_ts = messages[19].timestamp
    assert updated_fields["last_compaction_timestamp"] == expected_ts


def test_history_compactor_idempotency(mock_db, mock_llm_client):
    """Should ignore messages already compacted (based on timestamp)."""
    compactor = HistoryCompactor(mock_db, mock_llm_client)

    # Last compaction was at Minute 19
    base_ts = datetime(2026, 1, 1, 10, 0)
    last_compacted_ts = (base_ts + timedelta(minutes=19)).isoformat()

    profile = UserProfile(
        email="test@test.com",
        goal="test",
        gender="Masculino",
        age=30,
        weight=70.0,
        height=175,
        goal_type="maintain",
        weekly_rate=0.5,
        last_compaction_timestamp=last_compacted_ts,
    )
    mock_db.get_user_profile.return_value = profile

    # Same history as before (with meaningful text)
    messages = []
    for i in range(30):
        ts = base_ts + timedelta(minutes=i)
        msg = ChatHistory(
            sender=Sender.STUDENT, text=f"This is message number {i}", timestamp=ts.isoformat()
        )
        messages.append(msg)
    mock_db.get_chat_history.return_value = messages

    # Run with same window
    compactor.compact_history("test@test.com", active_window_size=10, compaction_threshold=20)

    # Since all "old" messages (0-19) are <= last_compaction_timestamp,
    # NO NEW lines to summarize.
    mock_llm_client.stream_simple.assert_not_called()
    mock_db.update_user_profile_fields.assert_not_called()


def test_preprocess_filters_non_student_messages(mock_db, mock_llm_client):
    """Should keep only student messages."""
    compactor = HistoryCompactor(mock_db, mock_llm_client)

    messages = [
        ChatHistory(
            sender=Sender.TRAINER,
            text="list_hevy_routines executado → 3 rotinas",
            timestamp="2026-01-31T10:00:00",
        ),
        ChatHistory(
            sender=Sender.SYSTEM,
            text="Ação executada: update_hevy_routine",
            timestamp="2026-01-31T10:01:00",
        ),
        ChatHistory(
            sender=Sender.STUDENT,
            text="Vou fazer Push 2x por semana",
            timestamp="2026-01-31T10:02:00",
        ),
    ]

    filtered = compactor._preprocess_messages(messages)

    assert len(filtered) == 1
    assert filtered[0].sender == Sender.STUDENT
    assert "Push 2x" in filtered[0].text


def test_preprocess_filters_greetings(mock_db, mock_llm_client):
    """Should filter trivial greetings even from student."""
    compactor = HistoryCompactor(mock_db, mock_llm_client)

    messages = [
        ChatHistory(
            sender=Sender.STUDENT,
            text="oi",
            timestamp="2026-01-31T10:00:00",
        ),
        ChatHistory(
            sender=Sender.STUDENT,
            text="Olá!",
            timestamp="2026-01-31T10:01:00",
        ),
        ChatHistory(
            sender=Sender.STUDENT,
            text="blz",
            timestamp="2026-01-31T10:02:00",
        ),
        ChatHistory(
            sender=Sender.STUDENT,
            text="ok",
            timestamp="2026-01-31T10:03:00",
        ),
        ChatHistory(
            sender=Sender.STUDENT,
            text="Quero treinar Push 2x por semana",
            timestamp="2026-01-31T10:04:00",
        ),
    ]

    filtered = compactor._preprocess_messages(messages)

    assert len(filtered) == 1
    assert "Push 2x" in filtered[0].text


def test_preprocess_filters_short_messages(mock_db, mock_llm_client):
    """Should filter messages shorter than 10 chars."""
    compactor = HistoryCompactor(mock_db, mock_llm_client)

    messages = [
        ChatHistory(
            sender=Sender.STUDENT,
            text="sim",
            timestamp="2026-01-31T10:00:00",
        ),
        ChatHistory(
            sender=Sender.STUDENT,
            text="não",
            timestamp="2026-01-31T10:01:00",
        ),
        ChatHistory(
            sender=Sender.STUDENT,
            text="Prefiro treinar de manhã",
            timestamp="2026-01-31T10:02:00",
        ),
    ]

    filtered = compactor._preprocess_messages(messages)

    assert len(filtered) == 1
    assert "manhã" in filtered[0].text


def test_preprocess_keeps_relevant_student_messages(mock_db, mock_llm_client):
    """Should keep relevant student messages with decisions/preferences."""
    compactor = HistoryCompactor(mock_db, mock_llm_client)

    messages = [
        ChatHistory(
            sender=Sender.STUDENT,
            text="Tenho uma lesão no joelho esquerdo",
            timestamp="2026-01-31T10:00:00",
        ),
        ChatHistory(
            sender=Sender.STUDENT,
            text="Minha meta é perder 5kg em 3 meses",
            timestamp="2026-01-31T10:01:00",
        ),
        ChatHistory(
            sender=Sender.STUDENT,
            text="Prefiro treinar com máquinas, não gosto de barra",
            timestamp="2026-01-31T10:02:00",
        ),
    ]

    filtered = compactor._preprocess_messages(messages)

    assert len(filtered) == 3
    assert any("lesão" in m.text for m in filtered)
    assert any("meta" in m.text for m in filtered)
    assert any("máquinas" in m.text for m in filtered)


def test_compact_history_uses_preprocessing(mock_db, mock_llm_client):
    """Should preprocess messages before compaction, filtering trainer messages."""
    # Mock LLM to return valid JSON
    async def async_gen(*args, **kwargs):
        yield '{"preferences": ["[31/01] Push 2x/semana"]}'
    mock_llm_client.stream_simple = MagicMock(side_effect=async_gen)

    compactor = HistoryCompactor(mock_db, mock_llm_client)

    profile = UserProfile(
        email="test@test.com",
        goal="test",
        gender="Masculino",
        age=30,
        weight=70.0,
        height=175,
        goal_type="maintain",
        weekly_rate=0.5,
    )
    mock_db.get_user_profile.return_value = profile

    # 40 messages: mix of student, trainer, system
    base_ts = datetime(2026, 1, 31, 10, 0)
    messages = []
    for i in range(40):
        ts = base_ts + timedelta(minutes=i)
        if i % 3 == 0:
            # Student message with content
            msg = ChatHistory(
                sender=Sender.STUDENT,
                text=f"Prefiro treinar assim {i}",
                timestamp=ts.isoformat(),
            )
        elif i % 3 == 1:
            # Trainer message (should be filtered)
            msg = ChatHistory(
                sender=Sender.TRAINER,
                text=f"list_hevy_routines executado → {i} rotinas",
                timestamp=ts.isoformat(),
            )
        else:
            # System message (should be filtered)
            msg = ChatHistory(
                sender=Sender.SYSTEM,
                text=f"Ação executada: tool_{i}",
                timestamp=ts.isoformat(),
            )
        messages.append(msg)

    mock_db.get_chat_history.return_value = messages

    # Run compaction
    compactor.compact_history("test@test.com", active_window_size=10, compaction_threshold=30)

    # Verify LLM was called
    mock_llm_client.stream_simple.assert_called_once()

    # Get the input_data passed to LLM
    call_kwargs = mock_llm_client.stream_simple.call_args[1]
    new_lines = call_kwargs["input_data"]["new_lines"]

    # Should NOT contain trainer/system messages
    assert "executado" not in new_lines
    assert "Ação executada" not in new_lines
    # Should contain student messages
    assert "Prefiro treinar" in new_lines


def test_compaction_produces_clean_json_output(mock_db, mock_llm_client):
    """
    E2E test: Given mixed messages, compaction should:
    1. Filter to student messages only
    2. Call LLM with clean input
    3. Store valid JSON with dated facts
    """
    # Mock LLM to return realistic output
    async def async_gen(*args, **kwargs):
        yield json.dumps({
            "health": [],
            "goals": ["[31/01] Meta: perder 0.25kg/semana"],
            "preferences": ["[31/01] Treino Push 2x/semana", "[31/01] Prefere máquinas"],
            "progress": [],
            "restrictions": []
        }, ensure_ascii=False)
    mock_llm_client.stream_simple = MagicMock(side_effect=async_gen)

    compactor = HistoryCompactor(mock_db, mock_llm_client)

    profile = UserProfile(
        email="test@test.com",
        goal="perder peso",
        gender="Masculino",
        age=45,
        weight=75.0,
        height=175,
        goal_type="lose",
        weekly_rate=0.25,
    )
    mock_db.get_user_profile.return_value = profile

    # Create realistic mixed messages
    base_ts = datetime(2026, 1, 31, 10, 0)
    messages = [
        # Student: greeting (should be filtered)
        ChatHistory(sender=Sender.STUDENT, text="oi", timestamp=(base_ts + timedelta(minutes=0)).isoformat()),
        # Trainer: tool log (should be filtered)
        ChatHistory(sender=Sender.TRAINER, text="list_hevy_routines executado → 3 rotinas", timestamp=(base_ts + timedelta(minutes=1)).isoformat()),
        # Student: decision (should be kept)
        ChatHistory(sender=Sender.STUDENT, text="Vou fazer o treino de Push 2x por semana", timestamp=(base_ts + timedelta(minutes=2)).isoformat()),
        # System: tool log (should be filtered)
        ChatHistory(sender=Sender.SYSTEM, text="update_hevy_routine executado → Rotina atualizada", timestamp=(base_ts + timedelta(minutes=3)).isoformat()),
        # Student: preference (should be kept)
        ChatHistory(sender=Sender.STUDENT, text="Prefiro usar máquinas, não gosto de barra", timestamp=(base_ts + timedelta(minutes=4)).isoformat()),
        # Trainer: response (should be filtered)
        ChatHistory(sender=Sender.TRAINER, text="Perfeito, vou ajustar sua rotina!", timestamp=(base_ts + timedelta(minutes=5)).isoformat()),
    ]

    # Add more messages to reach threshold (40 total)
    for i in range(34):
        ts = base_ts + timedelta(minutes=10 + i)
        messages.append(
            ChatHistory(sender=Sender.STUDENT, text=f"Mensagem de contexto numero {i}", timestamp=ts.isoformat())
        )

    mock_db.get_chat_history.return_value = messages

    # Run compaction
    compactor.compact_history("test@test.com", active_window_size=10, compaction_threshold=30)

    # Verify LLM was called with filtered input
    call_kwargs = mock_llm_client.stream_simple.call_args[1]
    new_lines = call_kwargs["input_data"]["new_lines"]

    # Should NOT contain system/trainer noise
    assert "executado" not in new_lines
    assert "list_hevy_routines" not in new_lines
    assert "update_hevy_routine" not in new_lines

    # Should contain student decisions
    assert "Push 2x" in new_lines
    assert "máquinas" in new_lines

    # Verify database was updated with valid JSON
    mock_db.update_user_profile_fields.assert_called_once()
    update_call = mock_db.update_user_profile_fields.call_args[0]
    stored_summary = update_call[1]["long_term_summary"]

    # Should be valid JSON
    summary_dict = json.loads(stored_summary)

    # Should have dated facts
    assert any("[31/01]" in fact for fact in summary_dict.get("preferences", []))
    assert any("[31/01]" in fact for fact in summary_dict.get("goals", []))


def test_event_loop_isolation_background_task(mock_db, mock_llm_client):
    """
    Test that compact_history can run from background task without event loop conflicts.
    This validates the fix for: Task <Task pending...> got Future attached to different loop
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    # Mock LLM to return valid JSON
    async def async_gen(*args, **kwargs):
        yield '{"health": [], "restrictions": [], "preferences": ["[31/01] Treino"]}'
    mock_llm_client.stream_simple = MagicMock(side_effect=async_gen)

    compactor = HistoryCompactor(mock_db, mock_llm_client)

    profile = UserProfile(
        email="bg-test@test.com",
        goal="test",
        gender="Masculino",
        age=30,
        weight=70.0,
        height=175,
        goal_type="maintain",
        weekly_rate=0.5,
    )
    mock_db.get_user_profile.return_value = profile

    # Create enough messages to trigger compaction
    base_ts = datetime(2026, 1, 31, 10, 0)
    messages = []
    for i in range(60):
        ts = base_ts + timedelta(minutes=i)
        msg = ChatHistory(
            sender=Sender.STUDENT,
            text=f"Mensagem numero {i} com conteudo relevante para teste",
            timestamp=ts.isoformat(),
        )
        messages.append(msg)
    mock_db.get_chat_history.return_value = messages

    # Run compaction in a background thread (simulating FastAPI BackgroundTasks)
    # This should NOT raise "Task attached to different loop" error
    error_occurred = None

    def run_in_thread():
        nonlocal error_occurred
        try:
            compactor.compact_history("bg-test@test.com", active_window_size=10, compaction_threshold=30)
        except Exception as e:
            error_occurred = e

    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(run_in_thread).result(timeout=10)

    # Assert no error occurred
    assert error_occurred is None, f"Background task failed with: {error_occurred}"
    # Verify compaction actually ran
    mock_llm_client.stream_simple.assert_called_once()
    mock_db.update_user_profile_fields.assert_called_once()
