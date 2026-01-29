"""
Comprehensive tests for message/chat endpoints.
Tests cover message history retrieval and AI message processing with streaming.
"""

from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
import pytest

from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_ai_trainer_brain
from src.api.models.sender import Sender


client = TestClient(app)


# Fixtures
@pytest.fixture
def mock_user_email():
    return "test@example.com"


@pytest.fixture
def sample_chat_messages():
    """Sample chat history with various message types."""
    from src.api.models.message import Message
    return [
        {
            "id": "msg_1",
            "user_email": "test@example.com",
            "sender": Sender.USER,
            "content": "What's my workout routine?",
            "timestamp": "2024-01-29T10:00:00Z"
        },
        {
            "id": "msg_2",
            "user_email": "test@example.com",
            "sender": Sender.TRAINER,
            "content": "Your routine consists of...",
            "timestamp": "2024-01-29T10:05:00Z"
        },
        {
            "id": "msg_3",
            "user_email": "test@example.com",
            "sender": Sender.SYSTEM,
            "content": "[Internal logging]",
            "timestamp": "2024-01-29T10:06:00Z"
        }
    ]


# Test: GET /message/history - Success Case
def test_get_history_success(sample_chat_messages):
    """Test successful retrieval of chat history."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_brain.get_chat_history.return_value = sample_chat_messages
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.get(
        "/message/history",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2  # SYSTEM messages filtered out

    # Verify SYSTEM messages are excluded
    for msg in data:
        assert msg["sender"] != Sender.SYSTEM

    mock_brain.get_chat_history.assert_called_once_with("test@example.com")

    app.dependency_overrides = {}


# Test: GET /message/history - Empty History
def test_get_history_empty():
    """Test chat history retrieval when user has no messages."""
    app.dependency_overrides[verify_token] = lambda: "newuser@example.com"
    mock_brain = MagicMock()
    mock_brain.get_chat_history.return_value = []
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.get(
        "/message/history",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data == []

    app.dependency_overrides = {}


# Test: GET /message/history - Unauthorized
def test_get_history_unauthorized():
    """Test chat history retrieval without authentication."""
    response = client.get("/message/history")

    assert response.status_code == 403


# Test: GET /message/history - Only System Messages (All Filtered)
def test_get_history_only_system_messages():
    """Test that only system messages returns empty list."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_brain.get_chat_history.return_value = [
        {
            "id": "msg_1",
            "user_email": "test@example.com",
            "sender": Sender.SYSTEM,
            "content": "[Internal]",
            "timestamp": "2024-01-29T10:00:00Z"
        }
    ]
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.get(
        "/message/history",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

    app.dependency_overrides = {}


# Test: POST /message/message - Success Case
def test_message_ai_success():
    """Test sending a message to AI trainer with streaming response."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()

    def mock_generator():
        yield "Hello, "
        yield "this is "
        yield "your trainer!"

    mock_brain.send_message_ai.return_value = mock_generator()
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    payload = {
        "user_message": "What should I eat today?"
    }

    response = client.post(
        "/message/message",
        json=payload,
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"

    # Streaming response - read chunks
    content = response.text
    assert len(content) > 0

    app.dependency_overrides = {}


# Test: POST /message/message - User Not Found
def test_message_ai_user_not_found():
    """Test message endpoint when user profile not found."""
    app.dependency_overrides[verify_token] = lambda: "nonexistent@example.com"
    mock_brain = MagicMock()
    mock_brain.send_message_ai.side_effect = ValueError("User profile not found")
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    payload = {
        "user_message": "Hello"
    }

    response = client.post(
        "/message/message",
        json=payload,
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 404

    app.dependency_overrides = {}


# Test: POST /message/message - Empty Message
def test_message_ai_empty_message():
    """Test sending empty message."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"

    payload = {
        "user_message": ""
    }

    response = client.post(
        "/message/message",
        json=payload,
        headers={"Authorization": "Bearer test_token"}
    )

    # Should either reject or process empty message
    assert response.status_code in [200, 422]

    app.dependency_overrides = {}


# Test: POST /message/message - Unauthorized
def test_message_ai_unauthorized():
    """Test sending message without authentication."""
    payload = {
        "user_message": "Hello trainer"
    }

    response = client.post("/message/message", json=payload)

    assert response.status_code == 403


# Test: POST /message/message - Long Message
def test_message_ai_long_message():
    """Test sending a very long message."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_brain.send_message_ai.return_value = (x for x in ["Response"])
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    # Create message with 5000+ characters
    long_message = "a" * 5000

    payload = {
        "user_message": long_message
    }

    response = client.post(
        "/message/message",
        json=payload,
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    mock_brain.send_message_ai.assert_called_once()

    app.dependency_overrides = {}


# Test: POST /message/message - Message with Special Characters
def test_message_ai_special_characters():
    """Test message containing special characters and Unicode."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_brain.send_message_ai.return_value = (x for x in ["OK"])
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    payload = {
        "user_message": "Preciso aumentar meu músculo! 💪 Pode me ajudar? @trainer #fitness"
    }

    response = client.post(
        "/message/message",
        json=payload,
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    call_args = mock_brain.send_message_ai.call_args
    assert call_args[1]["user_input"] == payload["user_message"]

    app.dependency_overrides = {}
