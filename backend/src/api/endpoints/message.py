"""This module contains the API endpoints for messaging."""

from __future__ import annotations

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
    logger.info("Received message from user %s: %s", user_email, message.user_message)

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
            },
        )
    except ValueError as e:
        logger.error("Error processing message for user %s: %s", user_email, e)
        raise HTTPException(status_code=404, detail=str(e)) from e
