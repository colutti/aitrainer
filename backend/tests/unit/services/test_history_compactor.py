
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


@pytest.mark.asyncio
async def test_history_compactor_skips_short_history(mock_db, mock_llm_client):
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

    await compactor.compact_history("test@test.com", active_window_size=20)

    # Assertions
    mock_llm_client.stream_simple.assert_not_called()
    mock_db.update_user_profile_fields.assert_not_called()


@pytest.mark.asyncio
async def test_history_compactor_summarizes_old_messages(mock_db, mock_llm_client):
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
    await compactor.compact_history("test@test.com", active_window_size=10, compaction_threshold=20)

    # Assertions
    mock_llm_client.stream_simple.assert_called_once()
    mock_db.update_user_profile_fields.assert_called_once()

    # Check if fields were updated correctly
    updated_fields = mock_db.update_user_profile_fields.call_args[0][1]
    assert "preferences" in updated_fields["long_term_summary"]
    # The last compacted message should be index 19 (since 20-29 are active window)
    expected_ts = messages[19].timestamp
    assert updated_fields["last_compaction_timestamp"] == expected_ts


@pytest.mark.asyncio
async def test_history_compactor_idempotency(mock_db, mock_llm_client):
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
    await compactor.compact_history("test@test.com", active_window_size=10, compaction_threshold=20)

    # Since all "old" messages (0-19) are <= last_compaction_timestamp,
    # NO NEW lines to summarize.
    mock_llm_client.stream_simple.assert_not_called()
    mock_db.update_user_profile_fields.assert_not_called()


def test_preprocess_filters_non_student_messages(mock_db, mock_llm_client):
    """Should keep student and trainer messages, but filter out system messages."""
    compactor = HistoryCompactor(mock_db, mock_llm_client)

    messages = [
        ChatHistory(
            sender=Sender.TRAINER,
            text="Ótimo, vou atualizar suas rotinas para 2x por semana",
            timestamp="2026-01-31T10:00:00",
        ),
        ChatHistory(
            sender=Sender.SYSTEM,
            text="✅ Tool 'update_hevy_routine' executed. Result: ...",
            timestamp="2026-01-31T10:01:00",
        ),
        ChatHistory(
            sender=Sender.STUDENT,
            text="Vou fazer Push 2x por semana",
            timestamp="2026-01-31T10:02:00",
        ),
    ]

    filtered = compactor._preprocess_messages(messages)

    # Should have student (1) + trainer (1) messages, but NOT system (1)
    assert len(filtered) == 2
    senders = {msg.sender for msg in filtered}
    assert Sender.STUDENT in senders
    assert Sender.TRAINER in senders
    assert Sender.SYSTEM not in senders
    assert "Push 2x" in [msg.text for msg in filtered if msg.sender == Sender.STUDENT][0]


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


@pytest.mark.asyncio
async def test_compact_history_uses_preprocessing(mock_db, mock_llm_client):
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
            # Trainer message (now KEPT, not filtered)
            msg = ChatHistory(
                sender=Sender.TRAINER,
                text=f"Ótimo, vou atualizar suas rotinas {i}",
                timestamp=ts.isoformat(),
            )
        else:
            # System message (FILTERED - tool results)
            msg = ChatHistory(
                sender=Sender.SYSTEM,
                text=f"✅ Tool executed: tool_{i}",
                timestamp=ts.isoformat(),
            )
        messages.append(msg)

    mock_db.get_chat_history.return_value = messages

    # Run compaction
    await compactor.compact_history("test@test.com", active_window_size=10, compaction_threshold=30)

    # Verify LLM was called
    mock_llm_client.stream_simple.assert_called_once()

    # Get the input_data passed to LLM
    call_kwargs = mock_llm_client.stream_simple.call_args[1]
    new_lines = call_kwargs["input_data"]["new_lines"]

    # Should NOT contain system messages (tool results)
    assert "Tool executed" not in new_lines
    # Should contain both student and trainer messages
    assert "Prefiro treinar" in new_lines
    assert "Ótimo, vou atualizar" in new_lines


@pytest.mark.asyncio
async def test_compaction_produces_clean_json_output(mock_db, mock_llm_client):
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
        # Student: greeting (should be filtered - too short)
        ChatHistory(sender=Sender.STUDENT, text="oi", timestamp=(base_ts + timedelta(minutes=0)).isoformat()),
        # System: tool log (should be filtered - system message)
        ChatHistory(sender=Sender.SYSTEM, text="✅ Tool 'search_hevy_exercises' executed", timestamp=(base_ts + timedelta(minutes=1)).isoformat()),
        # Student: decision (should be kept)
        ChatHistory(sender=Sender.STUDENT, text="Vou fazer o treino de Push 2x por semana", timestamp=(base_ts + timedelta(minutes=2)).isoformat()),
        # System: tool log (should be filtered - system message)
        ChatHistory(sender=Sender.SYSTEM, text="✅ Tool 'update_hevy_routine' executed", timestamp=(base_ts + timedelta(minutes=3)).isoformat()),
        # Student: preference (should be kept)
        ChatHistory(sender=Sender.STUDENT, text="Prefiro usar máquinas, não gosto de barra", timestamp=(base_ts + timedelta(minutes=4)).isoformat()),
        # Trainer: meaningful response (should be KEPT - contains useful context)
        ChatHistory(sender=Sender.TRAINER, text="Perfeito, vou ajustar sua rotina para Push 2x com máquinas!", timestamp=(base_ts + timedelta(minutes=5)).isoformat()),
    ]

    # Add more messages to reach threshold (40 total)
    for i in range(34):
        ts = base_ts + timedelta(minutes=10 + i)
        messages.append(
            ChatHistory(sender=Sender.STUDENT, text=f"Mensagem de contexto numero {i}", timestamp=ts.isoformat())
        )

    mock_db.get_chat_history.return_value = messages

    # Run compaction
    await compactor.compact_history("test@test.com", active_window_size=10, compaction_threshold=30)

    # Verify LLM was called with filtered input
    call_kwargs = mock_llm_client.stream_simple.call_args[1]
    new_lines = call_kwargs["input_data"]["new_lines"]

    # Should NOT contain system messages (tool results)
    assert "Tool" not in new_lines or "Tool 'search_hevy_exercises'" not in new_lines

    # Should contain student decisions AND trainer responses
    assert "Push 2x" in new_lines
    assert "máquinas" in new_lines
    assert "Treinador:" in new_lines  # Trainer messages included

    # Verify database was updated with valid JSON
    mock_db.update_user_profile_fields.assert_called_once()
    update_call = mock_db.update_user_profile_fields.call_args[0]
    stored_summary = update_call[1]["long_term_summary"]

    # Should be valid JSON
    summary_dict = json.loads(stored_summary)

    # Should have dated facts
    assert any("[31/01]" in fact for fact in summary_dict.get("preferences", []))
    assert any("[31/01]" in fact for fact in summary_dict.get("goals", []))


@pytest.mark.asyncio
async def test_event_loop_isolation_background_task(mock_db, mock_llm_client):
    """
    Test that compact_history (now native async) works correctly when awaited.

    Previously this tested ThreadPoolExecutor execution with asyncio.run() wrapper.
    Now compact_history is a native async function that FastAPI runs directly in its event loop.
    """
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

    # Run compaction as native async (like FastAPI does with async background tasks)
    # This should NOT raise "Task attached to different loop" error
    error_occurred = None
    try:
        await compactor.compact_history("bg-test@test.com", active_window_size=10, compaction_threshold=30)
    except Exception as e:
        error_occurred = e

    # Assert no error occurred
    assert error_occurred is None, f"Background task failed with: {error_occurred}"
    # Verify compaction actually ran
    mock_llm_client.stream_simple.assert_called_once()
    mock_db.update_user_profile_fields.assert_called_once()


@pytest.mark.asyncio
async def test_history_compactor_logs_tokens_in_callback(mock_db, mock_llm_client):
    """
    Test that history_compactor passes log_callback to stream_simple.
    This ensures resumos (summaries) can register tokens when LLM provides them.

    Note: This test verifies the integration point - actual token capture
    is tested in test_llm_client.py::test_stream_simple_captures_token_usage
    """
    compactor = HistoryCompactor(mock_db, mock_llm_client)

    # Track if log_callback was passed to stream_simple
    captured_callback = []

    async def mock_stream_simple(*args, **kwargs):
        # Capture the log_callback that was passed
        log_cb = kwargs.get("log_callback")
        if log_cb:
            captured_callback.append(log_cb)
        yield '{"preferences": []}'

    mock_llm_client.stream_simple = MagicMock(side_effect=mock_stream_simple)

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

    # Create 70 messages, with sufficient length to not be filtered
    base_ts = datetime(2026, 1, 1, 10, 0)
    messages = []
    for i in range(70):
        ts = base_ts + timedelta(minutes=i)
        msg = ChatHistory(
            sender=Sender.STUDENT,
            text=f"This is message {i} with enough content to not get filtered by preprocessor",
            timestamp=ts.isoformat(),
        )
        messages.append(msg)
    mock_db.get_chat_history.return_value = messages

    # Provide a mock log_callback
    mock_log = MagicMock()

    # Run compaction - this should pass log_callback to stream_simple
    await compactor.compact_history(
        "test@test.com",
        active_window_size=10,
        log_callback=mock_log,
        compaction_threshold=20,
    )

    # VERIFY: stream_simple was called with a log_callback
    assert mock_llm_client.stream_simple.called, "stream_simple should be called during compaction"
    call_kwargs = mock_llm_client.stream_simple.call_args[1]
    assert "log_callback" in call_kwargs, "stream_simple should receive log_callback"
    assert call_kwargs["log_callback"] is mock_log, "log_callback should be passed through"


def test_merge_summary_preserves_existing_categories(mock_db, mock_llm_client):
    """Test that merge preserves categories not in LLM response."""
    compactor = HistoryCompactor(mock_db, mock_llm_client)

    existing = json.dumps({
        "health": ["[01/02] Lesao no joelho"],
        "goals": ["[01/02] Perder 5kg"],
        "preferences": ["[31/01] Treinar 2x/semana"],
        "progress": [],
        "restrictions": []
    })

    # LLM only returns updated preferences
    new_data = {
        "preferences": ["[15/02] Agora treinar 3x/semana"]
    }

    merged = compactor._merge_summary(existing, new_data)

    # Health and goals should be preserved
    assert merged["health"] == ["[01/02] Lesao no joelho"]
    assert merged["goals"] == ["[01/02] Perder 5kg"]
    # Preferences should be updated
    assert merged["preferences"] == ["[15/02] Agora treinar 3x/semana"]
    # Empty categories should be preserved
    assert merged["progress"] == []
    assert merged["restrictions"] == []


def test_merge_summary_with_empty_llm_response(mock_db, mock_llm_client):
    """Test that empty LLM response preserves existing summary."""
    compactor = HistoryCompactor(mock_db, mock_llm_client)

    existing = json.dumps({
        "health": ["[01/02] Lesao"],
        "goals": ["[01/02] Meta"],
        "preferences": [],
        "progress": [],
        "restrictions": []
    })

    # LLM returns no new facts
    new_data = {}

    merged = compactor._merge_summary(existing, new_data)

    # Everything should be preserved
    assert merged["health"] == ["[01/02] Lesao"]
    assert merged["goals"] == ["[01/02] Meta"]


def test_merge_summary_with_no_existing_summary(mock_db, mock_llm_client):
    """Test merge when there's no existing summary."""
    compactor = HistoryCompactor(mock_db, mock_llm_client)

    # No existing summary
    new_data = {
        "goals": ["[15/02] Novo objetivo"],
        "preferences": ["[15/02] Malha seg/qua/sex"]
    }

    merged = compactor._merge_summary(None, new_data)

    # Should create skeleton with new data
    assert merged["goals"] == ["[15/02] Novo objetivo"]
    assert merged["preferences"] == ["[15/02] Malha seg/qua/sex"]
    assert merged["health"] == []
    assert merged["progress"] == []
    assert merged["restrictions"] == []


def test_merge_summary_multiple_categories_updated(mock_db, mock_llm_client):
    """Test merge with updates to multiple categories."""
    compactor = HistoryCompactor(mock_db, mock_llm_client)

    existing = json.dumps({
        "health": ["[01/02] Sem lesoes"],
        "goals": ["[01/02] Perder 5kg"],
        "preferences": ["[31/01] 2x/semana"],
        "progress": ["[10/02] 2kg perdidos"],
        "restrictions": []
    })

    # LLM updates 2 categories
    new_data = {
        "health": ["[15/02] Dor no ombro direito"],
        "progress": ["[15/02] 3kg perdidos"]
    }

    merged = compactor._merge_summary(existing, new_data)

    # Updated categories
    assert merged["health"] == ["[15/02] Dor no ombro direito"]
    assert merged["progress"] == ["[15/02] 3kg perdidos"]
    # Unchanged categories
    assert merged["goals"] == ["[01/02] Perder 5kg"]
    assert merged["preferences"] == ["[31/01] 2x/semana"]


@pytest.mark.asyncio
async def test_compact_history_merges_with_existing_summary(mock_db, mock_llm_client):
    """Integration test: verify compaction merges with existing summary."""
    async def async_gen(*args, **kwargs):
        # LLM only updates health, other categories NOT returned
        yield json.dumps({
            "health": ["[15/02] Nova lesao"]
        })
    mock_llm_client.stream_simple = MagicMock(side_effect=async_gen)

    compactor = HistoryCompactor(mock_db, mock_llm_client)

    existing_summary = json.dumps({
        "health": ["[01/02] Lesao anterior"],
        "goals": ["[01/02] Perder peso"],
        "preferences": ["[31/01] Treinar 2x"],
        "progress": [],
        "restrictions": []
    })

    profile = UserProfile(
        email="test@test.com",
        goal="test",
        gender="Masculino",
        age=30,
        weight=70.0,
        height=175,
        goal_type="maintain",
        weekly_rate=0.5,
        long_term_summary=existing_summary,
    )
    mock_db.get_user_profile.return_value = profile

    # 70 messages to trigger compaction
    base_ts = datetime(2026, 2, 15, 10, 0)
    messages = []
    for i in range(70):
        ts = base_ts + timedelta(minutes=i)
        msg = ChatHistory(
            sender=Sender.STUDENT,
            text=f"Mensagem numero {i} com conteudo relevante",
            timestamp=ts.isoformat(),
        )
        messages.append(msg)

    mock_db.get_chat_history.return_value = messages

    await compactor.compact_history("test@test.com", active_window_size=10, compaction_threshold=20)

    # Verify merge happened
    call_args = mock_db.update_user_profile_fields.call_args[0]
    stored_summary_str = call_args[1]["long_term_summary"]
    stored_summary = json.loads(stored_summary_str)

    # Old health should be replaced (not preserved)
    assert any("[15/02]" in h for h in stored_summary.get("health", []))
    # Goals should be preserved (not in LLM response)
    assert any("Perder peso" in g for g in stored_summary.get("goals", []))
    # Preferences should be preserved
    assert any("Treinar 2x" in p for p in stored_summary.get("preferences", []))


def test_parse_json_response_with_markdown_fence(mock_db, mock_llm_client):
    """Test JSON parsing with markdown code fence."""
    compactor = HistoryCompactor(mock_db, mock_llm_client)

    response_with_fence = """```json
{"health": ["[15/02] Lesao"], "goals": [], "preferences": [], "progress": [], "restrictions": []}
```"""

    result = compactor._parse_json_response(response_with_fence)

    assert result is not None
    assert result["health"] == ["[15/02] Lesao"]


def test_parse_json_response_invalid_json_returns_none(mock_db, mock_llm_client):
    """Test that invalid JSON returns None."""
    compactor = HistoryCompactor(mock_db, mock_llm_client)

    invalid_json = '{"health": ["unclosed'

    result = compactor._parse_json_response(invalid_json)

    assert result is None


@pytest.mark.asyncio
async def test_compact_history_advances_timestamp_on_empty_result(mock_db, mock_llm_client):
    """Test that empty LLM result still advances last_compaction_timestamp."""
    async def async_gen(*args, **kwargs):
        yield json.dumps({})  # Empty response - no new facts
    mock_llm_client.stream_simple = MagicMock(side_effect=async_gen)

    compactor = HistoryCompactor(mock_db, mock_llm_client)

    base_ts = datetime(2026, 2, 15, 10, 0)
    last_ts_str = (base_ts + timedelta(minutes=10)).isoformat()

    profile = UserProfile(
        email="test@test.com",
        goal="test",
        gender="Masculino",
        age=30,
        weight=70.0,
        height=175,
        goal_type="maintain",
        weekly_rate=0.5,
        long_term_summary='{"health": [], "goals": [], "preferences": [], "progress": [], "restrictions": []}',
        last_compaction_timestamp=last_ts_str,
    )
    mock_db.get_user_profile.return_value = profile

    # 70 messages with timestamps after last compaction
    messages = []
    for i in range(70):
        ts = base_ts + timedelta(minutes=15 + i)
        msg = ChatHistory(
            sender=Sender.STUDENT,
            text=f"Mensagem numero {i}",
            timestamp=ts.isoformat(),
        )
        messages.append(msg)

    mock_db.get_chat_history.return_value = messages

    await compactor.compact_history("test@test.com", active_window_size=10, compaction_threshold=20)

    # Verify timestamp was advanced even with empty response
    call_args = mock_db.update_user_profile_fields.call_args[0]
    new_ts = call_args[1]["last_compaction_timestamp"]
    assert new_ts > last_ts_str


def test_compaction_threshold_gap_new_user(mock_db, mock_llm_client):
    """Test that low threshold (25) triggers compaction for new users."""
    async def async_gen(*args, **kwargs):
        yield json.dumps({"preferences": []})
    mock_llm_client.stream_simple = MagicMock(side_effect=async_gen)

    compactor = HistoryCompactor(mock_db, mock_llm_client)

    profile = UserProfile(
        email="new-user@test.com",
        goal="test",
        gender="Masculino",
        age=30,
        weight=70.0,
        height=175,
        goal_type="maintain",
        weekly_rate=0.5,
    )
    mock_db.get_user_profile.return_value = profile

    # 25 messages with window=20, threshold=25 should trigger compaction
    base_ts = datetime(2026, 2, 15, 10, 0)
    messages = []
    for i in range(25):
        ts = base_ts + timedelta(minutes=i)
        msg = ChatHistory(
            sender=Sender.STUDENT,
            text=f"Mensagem numero {i} com conteudo",
            timestamp=ts.isoformat(),
        )
        messages.append(msg)

    mock_db.get_chat_history.return_value = messages

    # This must be run in async context
    import asyncio
    asyncio.run(compactor.compact_history("new-user@test.com", active_window_size=20, compaction_threshold=25))

    # Verify LLM was called (compaction triggered)
    mock_llm_client.stream_simple.assert_called_once()
    # Verify messages 0-4 were compacted
    call_kwargs = mock_llm_client.stream_simple.call_args[1]
    new_lines = call_kwargs["input_data"]["new_lines"]
    assert "Mensagem numero 0" in new_lines
    assert "Mensagem numero 4" in new_lines
