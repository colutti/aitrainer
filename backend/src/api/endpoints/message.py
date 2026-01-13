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
def get_history(user_email: CurrentUser, brain: AITrainerBrainDep) -> list:
    """
    Returns the chat message history for the authenticated user.
    """
    logger.info("Retrieving chat history for user: %s", user_email)
    messages = brain.get_chat_history(user_email)
    return messages


@router.post("/message")
def message_ai(
    message: MessageRequest, 
    user_email: CurrentUser, 
    brain: AITrainerBrainDep,
    background_tasks: BackgroundTasks
) -> StreamingResponse:
    """
    Handles an AI messaging request for an authenticated user.

    Args:
        message (MessageRequest): The user's message input.
        user_email (str): The authenticated user's email.
        brain (AITrainerBrain): The AI trainer brain dependency.
        background_tasks (BackgroundTasks): FastAPI background tasks for async operations.

    Returns:
        StreamingResponse: A streaming response containing the AI-generated reply chunks.

    Raises:
        HTTPException: If the user profile is not found (404).
    """
    logger.info("Received message from user %s: %s", user_email, message.user_message)
    try:
        response_generator = brain.send_message_ai(
            user_email=user_email,
            user_input=message.user_message,
            background_tasks=background_tasks
        )
        return StreamingResponse(response_generator, media_type="text/plain")
    except ValueError as e:
        logger.error("Error processing message for user %s: %s", user_email, e)
        raise HTTPException(status_code=404, detail=str(e)) from e

