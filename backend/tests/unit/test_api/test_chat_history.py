"""
Tests for the ChatHistory model in src/api/models/chat_history.py
"""

from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender


def test_chat_history_clean_text():
    """Test _get_clean_text method."""
    msg = ChatHistory(
        text="  Hello   world!  \n\n  How are  you?  ",
        sender=Sender.STUDENT,
        timestamp="2024-01-01T10:00:00",
    )
    assert msg._get_clean_text() == "Hello world! How are you?"


def test_chat_history_formatted_timestamp_valid():
    """Test _get_formatted_timestamp with valid ISO date."""
    msg = ChatHistory(
        text="test", sender=Sender.STUDENT, timestamp="2024-01-01T10:00:00"
    )
    assert msg._get_formatted_timestamp() == "01/01/2024 10:00"


def test_chat_history_formatted_timestamp_invalid():
    """Test _get_formatted_timestamp with invalid date."""
    msg = ChatHistory(text="test", sender=Sender.STUDENT, timestamp="invalid-date")
    assert msg._get_formatted_timestamp() == "invalid-date"


def test_chat_history_sender_label():
    """Test _get_sender_label method."""
    student_msg = ChatHistory(
        text="test", sender=Sender.STUDENT, timestamp="2024-01-01T10:00:00"
    )
    trainer_msg = ChatHistory(
        text="test", sender=Sender.TRAINER, timestamp="2024-01-01T10:00:00"
    )
    assert "Aluno" in student_msg._get_sender_label()
    assert "Treinador" in trainer_msg._get_sender_label()


def test_chat_history_str_representation():
    """Test __str__ method."""
    msg = ChatHistory(
        text="Hello", sender=Sender.STUDENT, timestamp="2024-01-01T10:00:00"
    )
    s = str(msg)
    assert "**🧑 Aluno** (01/01/2024 10:00):" in s
    assert "> Hello" in s


def test_from_mongodb_chat_message_history():
    """Test conversion from MongoDB history."""

    class MockMsg:
        def __init__(self, content, type_val, timestamp=None, trainer_type=None):
            self.content = content
            self.type = type_val
            self.additional_kwargs = {}
            if timestamp:
                self.additional_kwargs["timestamp"] = timestamp
            if trainer_type:
                self.additional_kwargs["trainer_type"] = trainer_type

    class MockHistory:
        def __init__(self, messages):
            self.messages = messages

    msgs = [
        MockMsg("Hi", "human", "2024-01-01T10:00:00"),
        MockMsg("Hello", "ai", "2024-01-01T10:01:00", "atlas"),
    ]
    history = MockHistory(msgs)

    result = ChatHistory.from_mongodb_chat_message_history(history)

    assert len(result) == 2
    assert result[0].text == "Hi"
    assert result[0].sender == Sender.STUDENT
    assert result[1].text == "Hello"
    assert result[1].sender == Sender.TRAINER
    assert result[1].trainer_type == "atlas"


def test_to_string_list():
    """Test to_string_list static method."""
    msgs = [
        ChatHistory(text="Hi", sender=Sender.STUDENT, timestamp="2024-01-01T10:00:00"),
        ChatHistory(
            text="Hello", sender=Sender.TRAINER, timestamp="2024-01-01T10:01:00"
        ),
    ]

    result = ChatHistory.to_string_list(msgs)
    assert len(result) == 2
    assert "Aluno" in result[0]
    assert "Treinador" in result[1]


def test_format_as_string_empty():
    """Test format_as_string with empty list."""
    assert ChatHistory.format_as_string([]) == "Nenhuma mensagem anterior."


def test_format_as_string_with_messages():
    """Test format_as_string with messages."""
    msgs = [
        ChatHistory(text="Hi", sender=Sender.STUDENT, timestamp="2024-01-01T10:00:00"),
        ChatHistory(
            text="Hello", sender=Sender.TRAINER, timestamp="2024-01-01T10:01:00"
        ),
    ]

    result = ChatHistory.format_as_string(msgs)
    assert "**🧑 Aluno**" in result
    assert "**🏋️ Treinador**" in result
    assert "---" in result


def test_format_with_trainer_context():
    """Test format_with_trainer_context."""
    msgs = [
        ChatHistory(text="Hi", sender=Sender.STUDENT, timestamp="2024-01-01T10:00:00"),
        ChatHistory(
            text="Hello",
            sender=Sender.TRAINER,
            timestamp="2024-01-01T10:01:00",
            trainer_type="atlas",
        ),
        ChatHistory(
            text="Old Hello",
            sender=Sender.TRAINER,
            timestamp="2024-01-01T09:00:00",
            trainer_type="old_trainer",
        ),
    ]

    # Current trainer is atlas
    result = ChatHistory.format_with_trainer_context(msgs, "atlas")

    # 1. User msg: as normal
    assert "**🧑 Aluno**" in result

    # 2. Current trainer msg: as normal
    assert "**🏋️ Treinador** (01/01/2024 10:01)" in result

    # 3. Old trainer msg: with context label
    assert "**🏋️ Treinador [PERFIL ANTERIOR: old_trainer]**" in result
    assert "[Contexto] Old Hello" in result


def test_format_with_trainer_context_empty():
    """Test format_with_trainer_context with empty list."""
    assert (
        ChatHistory.format_with_trainer_context([], "atlas")
        == "Nenhuma mensagem anterior."
    )
