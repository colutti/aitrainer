"""
This module contains the API endpoints for memory management.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.services.auth import verify_token
from src.core.deps import get_ai_trainer_brain
from src.core.logs import logger
from src.api.models.memory_item import MemoryItem, MemoryListResponse
from src.services.trainer import AITrainerBrain

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
AITrainerBrainDep = Annotated[AITrainerBrain, Depends(get_ai_trainer_brain)]


@router.get("/list", response_model=MemoryListResponse)
def list_memories(user_email: CurrentUser, brain: AITrainerBrainDep) -> MemoryListResponse:
    """
    Retrieves the last 50 memories for the authenticated user.

    Args:
        user_email (str): The authenticated user's email.
        brain (AITrainerBrain): The AI trainer brain dependency.

    Returns:
        MemoryListResponse: List of user memories with total count.
    """
    logger.info("=== Memory List Request ===")
    logger.info("User: %s", user_email)

    try:
        raw_memories = brain.get_all_memories(user_email)
        logger.debug("Processing %d raw memories", len(raw_memories))

        memories = [
            MemoryItem(
                id=mem.get("id", ""),
                memory=mem.get("memory", ""),
                created_at=mem.get("created_at"),
                updated_at=mem.get("updated_at"),
            )
            for mem in raw_memories
        ]

        logger.info("Returning %d memories for user: %s", len(memories), user_email)
        return MemoryListResponse(memories=memories, total=len(memories))
    except Exception as e:
        logger.error("Error listing memories for user %s: %s", user_email, e)
        raise HTTPException(status_code=500, detail="Failed to retrieve memories") from e


@router.delete("/{memory_id}")
def delete_memory(
    memory_id: str, user_email: CurrentUser, brain: AITrainerBrainDep
) -> dict:
    """
    Deletes a specific memory for the authenticated user.

    Args:
        memory_id (str): The ID of the memory to delete.
        user_email (str): The authenticated user's email.
        brain (AITrainerBrain): The AI trainer brain dependency.

    Returns:
        dict: Confirmation message.

    Raises:
        HTTPException: If deletion fails.
    """
    logger.info("=== Memory Delete Request ===")
    logger.info("User: %s, Memory ID: %s", user_email, memory_id)

    try:
        brain.delete_memory(memory_id)
        logger.info("Memory %s deleted successfully by user %s", memory_id, user_email)
        return {"message": "Memory deleted successfully"}
    except Exception as e:
        logger.error("Failed to delete memory %s for user %s: %s", memory_id, user_email, e)
        raise HTTPException(status_code=500, detail="Failed to delete memory") from e
