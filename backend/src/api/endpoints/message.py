"""This module contains the API endpoints for messaging."""

from __future__ import annotations

from typing import Annotated, TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

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

class ClientMessageErrorPayload(BaseModel):
    """Payload reported by frontend when chat streaming fails on client side."""

    request_id: str | None = None
    error_name: str | None = None
    error_message: str | None = None
    error_stack: str | None = None
    phase: str | None = None
    response_status: int | None = None
    response_body: str | None = None


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
    request_id = request.headers.get("X-Request-Id")
    logger.info(
        "Received message from user %s (request_id=%s): %s",
        user_email,
        request_id,
        message.user_message,
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
        return StreamingResponse(
            response_generator,
            media_type="text/event-stream",
            headers={
                "X-Accel-Buffering": "no",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                **({"X-Request-Id": request_id} if request_id else {}),
            },
        )
    except ValueError as e:
        logger.error("Error processing message for user %s: %s", user_email, e)
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/client-error")
def message_client_error(
    payload: ClientMessageErrorPayload,
    user_email: CurrentUser,
) -> dict:
    """Receives frontend-side chat stream failures for incident correlation."""
    logger.error(
        "Client chat error reported by %s: request_id=%s phase=%s name=%s "
        "message=%s status=%s body=%s stack=%s",
        user_email,
        payload.request_id,
        payload.phase,
        payload.error_name,
        payload.error_message,
        payload.response_status,
        payload.response_body,
        payload.error_stack,
    )
    return {"ok": True}
