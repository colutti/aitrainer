"""
Unit tests for message/chat handlers and request validation.
"""

import asyncio
import base64
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from src.api.endpoints.message import get_history, message_ai
from src.api.models.chat_history import ChatHistory
from src.api.models.message import MessageRequest
from src.api.models.sender import Sender
from src.api.models.user_profile import UserProfile


@pytest.fixture
def sample_chat_messages():
    return [
        ChatHistory(
            text="What's my workout routine?",
            sender=Sender.STUDENT,
            timestamp="2024-01-29T10:00:00Z",
        ),
        ChatHistory(
            text="Your routine consists of...",
            sender=Sender.TRAINER,
            timestamp="2024-01-29T10:05:00Z",
        ),
    ]


def test_get_history_success(sample_chat_messages):
    mock_brain = MagicMock()
    mock_brain.get_chat_history.return_value = sample_chat_messages

    result = get_history(
        user_email="test@example.com",
        brain=mock_brain,
        limit=20,
        offset=0,
    )

    assert result == sample_chat_messages
    mock_brain.get_chat_history.assert_called_once_with(
        "test@example.com", limit=20, offset=0
    )


def test_get_history_empty():
    mock_brain = MagicMock()
    mock_brain.get_chat_history.return_value = []

    result = get_history(
        user_email="newuser@example.com",
        brain=mock_brain,
        limit=20,
        offset=0,
    )

    assert result == []


def test_get_history_route_does_not_require_brain_query_param():
    from src.api.main import app

    route = next(
        (
            r
            for r in app.routes
            if getattr(r, "path", None) == "/message/history"
            and "GET" in getattr(r, "methods", set())
        ),
        None,
    )

    assert route is not None
    query_param_names = [param.name for param in route.dependant.query_params]
    assert "brain" not in query_param_names


def _collect_stream_text(response) -> str:
    async def _collect() -> str:
        parts = []
        async for chunk in response.body_iterator:
            parts.append(chunk.decode() if isinstance(chunk, bytes) else chunk)
        return "".join(parts)

    return asyncio.run(_collect())


def _make_user_profile(email: str, plan: str = "Free") -> UserProfile:
    return UserProfile(
        email=email,
        gender="Masculino",
        age=30,
        weight=80,
        height=175,
        goal="ganhar massa",
        goal_type="gain",
        weekly_rate=0.5,
        subscription_plan=plan,
    )


def test_message_ai_success():
    mock_brain = MagicMock()

    async def mock_generator():
        yield "Hello, this is your trainer!"

    mock_brain.get_or_create_user_profile.return_value = _make_user_profile(
        "test@example.com"
    )
    mock_brain.check_message_limits.return_value = False
    mock_brain.send_message_ai.return_value = mock_generator()

    response = asyncio.run(
        message_ai(
            message=SimpleNamespace(user_message="What should I eat today?", images=None),
            request=SimpleNamespace(headers={"X-Chat-Stream-Format": "sse-v1"}),
            user_email="test@example.com",
            background_tasks=MagicMock(),
            brain=mock_brain,
        )
    )

    content = _collect_stream_text(response)

    assert response.media_type == "text/event-stream"
    assert "Hello, this is your trainer!" in content


def test_message_ai_defaults_to_legacy_raw_text_for_clients_without_stream_header():
    mock_brain = MagicMock()

    async def mock_generator():
        yield 'event: status\ndata: {"stage":"preparing_context"}\n\n'
        yield 'event: delta\ndata: {"text":"Hello "}\n\n'
        yield 'event: delta\ndata: {"text":"World"}\n\n'
        yield 'event: done\ndata: {"text":"Hello World","persisted":true}\n\n'

    mock_brain.get_or_create_user_profile.return_value = _make_user_profile(
        "test@example.com"
    )
    mock_brain.check_message_limits.return_value = False
    mock_brain.send_message_ai.return_value = mock_generator()

    response = asyncio.run(
        message_ai(
            message=SimpleNamespace(user_message="Oi", images=None),
            request=SimpleNamespace(headers={}),
            user_email="test@example.com",
            background_tasks=MagicMock(),
            brain=mock_brain,
        )
    )

    content = _collect_stream_text(response)

    assert response.media_type == "text/plain"
    assert content == "Hello World"


def test_message_ai_keeps_sse_for_explicit_sse_clients():
    mock_brain = MagicMock()

    async def mock_generator():
        yield 'event: status\ndata: {"stage":"preparing_context"}\n\n'
        yield 'event: delta\ndata: {"text":"Hello"}\n\n'

    mock_brain.get_or_create_user_profile.return_value = _make_user_profile(
        "test@example.com"
    )
    mock_brain.check_message_limits.return_value = False
    mock_brain.send_message_ai.return_value = mock_generator()

    response = asyncio.run(
        message_ai(
            message=SimpleNamespace(user_message="Oi", images=None),
            request=SimpleNamespace(headers={"X-Chat-Stream-Format": "sse-v1"}),
            user_email="test@example.com",
            background_tasks=MagicMock(),
            brain=mock_brain,
        )
    )

    content = _collect_stream_text(response)

    assert response.media_type == "text/event-stream"
    assert 'event: delta\ndata: {"text":"Hello"}\n\n' in content


def test_message_ai_user_not_found():
    mock_brain = MagicMock()
    mock_brain.send_message_ai.side_effect = ValueError("User profile not found")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            message_ai(
                message=SimpleNamespace(user_message="Hello", images=None),
                request=SimpleNamespace(headers={}),
                user_email="nonexistent@example.com",
                background_tasks=MagicMock(),
                brain=mock_brain,
            )
        )

    assert exc_info.value.status_code == 404


def test_message_request_rejects_empty_message():
    with pytest.raises(ValueError, match="EMPTY_MESSAGE"):
        MessageRequest.model_validate({"user_message": "", "images": []})


def test_message_request_rejects_long_message():
    with pytest.raises(ValueError, match="MESSAGE_TOO_LONG"):
        MessageRequest.model_validate({"user_message": "a" * 20001})


def test_message_request_accepts_valid_legacy_payload():
    result = MessageRequest.model_validate(
        {
            "user_message": "Oi",
            "image_base64": base64.b64encode(b"fake").decode("utf-8"),
            "image_mime_type": "image/jpeg",
        }
    )

    assert result.images is not None
    assert len(result.images) == 1


def test_message_ai_special_characters():
    mock_brain = MagicMock()
    mock_brain.get_or_create_user_profile.return_value = _make_user_profile(
        "test@example.com"
    )
    mock_brain.check_message_limits.return_value = False

    async def mock_generator():
        yield "OK"

    mock_brain.send_message_ai.return_value = mock_generator()
    payload = "Preciso aumentar meu músculo! 💪 Pode me ajudar? @trainer #fitness"

    response = asyncio.run(
        message_ai(
            message=SimpleNamespace(user_message=payload, images=None),
            request=SimpleNamespace(headers={}),
            user_email="test@example.com",
            background_tasks=MagicMock(),
            brain=mock_brain,
        )
    )

    assert response.status_code == 200
    assert mock_brain.send_message_ai.call_args[1]["user_input"] == payload


def test_message_request_rejects_too_many_images():
    payload = {
        "user_message": "Analisa",
        "images": [
            {"base64": "ZmFrZQ==", "mime_type": "image/jpeg"},
            {"base64": "ZmFrZQ==", "mime_type": "image/jpeg"},
            {"base64": "ZmFrZQ==", "mime_type": "image/jpeg"},
            {"base64": "ZmFrZQ==", "mime_type": "image/jpeg"},
            {"base64": "ZmFrZQ==", "mime_type": "image/jpeg"},
        ],
    }

    with pytest.raises(ValueError, match="TOO_MANY_IMAGES"):
        MessageRequest.model_validate(payload)


def test_message_request_rejects_oversized_image():
    oversized = base64.b64encode(b"a" * (3 * 1024 * 1024 + 1)).decode("utf-8")
    payload = {
        "user_message": "Analisa",
        "images": [{"base64": oversized, "mime_type": "image/jpeg"}],
    }

    with pytest.raises(ValueError, match="IMAGE_TOO_LARGE"):
        MessageRequest.model_validate(payload)
