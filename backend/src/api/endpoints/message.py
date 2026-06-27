"""This module contains the API endpoints for messaging."""

from __future__ import annotations

import hashlib
import inspect
import json
from typing import Annotated, TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse

from src.core.demo_access import WritableCurrentUser
from src.services.auth import verify_token
from src.core.deps import get_ai_trainer_brain
from src.api.models.message import MessageRequest
from src.core.subscription import can_use_image_input
from src.core.logs import logger

if TYPE_CHECKING:
    from src.services.trainer import AITrainerBrain

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
SSE_STREAM_HEADER = "X-Chat-Stream-Format"
SSE_STREAM_VERSION = "sse-v1"


def _parse_sse_event(frame: str) -> tuple[str, dict] | None:
    """Parse one SSE frame emitted by the trainer service."""
    stripped = frame.strip()
    if not stripped.startswith("event:"):
        return None

    lines = stripped.splitlines()
    event_name = ""
    data_lines: list[str] = []
    for line in lines:
        if line.startswith("event:"):
            event_name = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            data_lines.append(line.split(":", 1)[1].strip())

    if not event_name or not data_lines:
        return None

    try:
        payload = json.loads("\n".join(data_lines))
    except json.JSONDecodeError:
        return None
    return event_name, payload


async def _adapt_sse_for_legacy_clients(response_generator):
    # pylint: disable=too-many-branches
    """Convert structured SSE stream into plain text for older frontend bundles."""
    raw_buffer = ""
    accumulated_text = ""

    if hasattr(response_generator, "__aiter__"):
        iterator = response_generator
    else:
        async def _sync_to_async():
            for item in response_generator:
                yield item

        iterator = _sync_to_async()

    async for chunk in iterator:
        if inspect.isawaitable(chunk):
            chunk = await chunk
        if not isinstance(chunk, str):
            continue
        raw_buffer += chunk
        frames = raw_buffer.split("\n\n")
        raw_buffer = frames.pop() or ""

        for frame in frames:
            parsed = _parse_sse_event(frame)
            if parsed is None:
                yield frame
                continue

            event_name, payload = parsed
            if event_name == "delta":
                text = str(payload.get("text") or "")
                accumulated_text += text
                if text:
                    yield text
            elif event_name == "done":
                final_text = str(payload.get("text") or "")
                if final_text and not accumulated_text:
                    yield final_text
            elif event_name == "error":
                message = str(payload.get("message") or "")
                if message:
                    yield message

    if raw_buffer.strip():
        yield raw_buffer

@router.get("/history")
def get_history(
    user_email: CurrentUser,
    brain: "AITrainerBrain" = Depends(get_ai_trainer_brain),
    limit: int = 20,
    offset: int = 0,
) -> list:
    """
    Returns the chat message history for the authenticated user,
    excluding internal system notifications.
    """
    logger.info(
        "Retrieving chat history for user: %s (limit: %d, offset: %d)",
        user_email,
        limit,
        offset,
    )
    messages = brain.get_chat_history(user_email, limit=limit, offset=offset)
    return messages


@router.post("")
async def message_ai(
    message: MessageRequest,
    request: Request,
    user_email: WritableCurrentUser,
    background_tasks: BackgroundTasks,
    brain: "AITrainerBrain" = Depends(get_ai_trainer_brain),
) -> StreamingResponse:
    """
    Handles an AI messaging request for an authenticated user.
    """
    preview = message.user_message.replace("\n", " ")[:120]
    message_hash = hashlib.sha256(message.user_message.encode("utf-8")).hexdigest()[:12]
    logger.info(
        "Received message from user %s (chars=%d, images=%d, sha=%s, preview=%s)",
        user_email,
        len(message.user_message),
        len(message.images or []),
        message_hash,
        preview,
    )

    # Detect and save timezone from header
    tz = request.headers.get("X-User-Timezone")
    if tz:
        profile = brain.get_or_create_user_profile(user_email)
        if tz != profile.timezone:
            logger.info("Updating timezone for %s to %s", user_email, tz)
            brain.update_user_profile_fields(user_email, {"timezone": tz})
    try:
        # Pre-flight limits check to avoid StreamingResponse generator crash
        profile = brain.get_or_create_user_profile(user_email)
        brain.check_message_limits(profile)
        if message.images and not can_use_image_input(profile.subscription_plan):
            raise HTTPException(status_code=403, detail="IMAGE_NOT_ALLOWED_FOR_PLAN")

        wants_sse = request.headers.get(SSE_STREAM_HEADER) == SSE_STREAM_VERSION
        response_generator = brain.send_message_ai(
            user_email=user_email,
            user_input=message.user_message,
            background_tasks=background_tasks,
            message_options={
                "is_telegram": False,
                "image_payloads": (
                    [
                        {
                            "base64": img.base64_data,
                            "mime_type": img.mime_type,
                        }
                        for img in message.images
                    ]
                    if message.images
                    else None
                ),
            },
        )
        body_iterator = response_generator if wants_sse else _adapt_sse_for_legacy_clients(
            response_generator
        )
        return StreamingResponse(
            body_iterator,
            media_type="text/event-stream" if wants_sse else "text/plain",
            headers={
                "X-Accel-Buffering": "no",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
    except ValueError as e:
        logger.error("Error processing message for user %s: %s", user_email, e)
        raise HTTPException(status_code=404, detail=str(e)) from e
