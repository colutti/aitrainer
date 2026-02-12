"""
This module contains the API endpoints for messaging.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

from src.services.auth import verify_token
from src.core.deps import get_ai_trainer_brain
from src.api.models.message import MessageRequest
from src.services.trainer import AITrainerBrain
from src.core.logs import logger

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
AITrainerBrainDep = Annotated[AITrainerBrain, Depends(get_ai_trainer_brain)]


@router.get("/history")
def get_history(
    user_email: CurrentUser, brain: AITrainerBrainDep, limit: int = 20, offset: int = 0
) -> list:
    """
    Returns the chat message history for the authenticated user,
    excluding internal system notifications.
    """
    logger.info(
        "Retrieving chat history for user: %s (limit: %d, offset: %d)",
        user_email, limit, offset,
    )
    messages = brain.get_chat_history(user_email, limit=limit, offset=offset)
    return messages


@router.post("/message")
async def message_ai(
    message: MessageRequest,
    user_email: CurrentUser,
    brain: AITrainerBrainDep,
    background_tasks: BackgroundTasks,
) -> StreamingResponse:
    """
    Handles an AI messaging request for an authenticated user.
    """
    logger.info("Received message from user %s: %s", user_email, message.user_message)
    try:
        response_generator = brain.send_message_ai(
            user_email=user_email,
            user_input=message.user_message,
            background_tasks=background_tasks,
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
