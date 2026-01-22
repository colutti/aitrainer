"""
This module contains the API endpoints for memory management.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from qdrant_client import QdrantClient

from src.services.auth import verify_token
from src.core.config import settings
from src.core.deps import get_ai_trainer_brain, get_qdrant_client
from src.core.logs import logger
from src.api.models.memory_item import MemoryItem, MemoryListResponse
from src.services.trainer import AITrainerBrain

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
AITrainerBrainDep = Annotated[AITrainerBrain, Depends(get_ai_trainer_brain)]
QdrantClientDep = Annotated[QdrantClient, Depends(get_qdrant_client)]


@router.get("/list", response_model=MemoryListResponse)
def list_memories(
    user_email: CurrentUser,
    brain: AITrainerBrainDep,
    qdrant: QdrantClientDep,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=10, ge=1, le=50, description="Items per page"),
) -> MemoryListResponse:
    """
    Retrieves paginated memories for the authenticated user.

    Args:
        user_email (str): The authenticated user's email.
        brain (AITrainerBrain): The AI trainer brain dependency.
        qdrant (QdrantClient): Qdrant client for direct memory access.
        page (int): Page number (1-indexed).
        page_size (int): Number of items per page (1-50).

    Returns:
        MemoryListResponse: Paginated list of user memories.
    """
    logger.info("=== Memory List Request (Paginated) ===")
    logger.info("User: %s, Page: %d, PageSize: %d", user_email, page, page_size)

    try:
        raw_memories, total = brain.get_memories_paginated(
            user_id=user_email,
            page=page,
            page_size=page_size,
            qdrant_client=qdrant,
            collection_name=settings.QDRANT_COLLECTION_NAME,
        )
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

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        logger.info(
            "Returning %d memories for user: %s (page %d/%d)",
            len(memories),
            user_email,
            page,
            total_pages,
        )
        return MemoryListResponse(
            memories=memories,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception as e:
        logger.error("Error listing memories for user %s: %s", user_email, e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve memories"
        ) from e


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
        # Validate ownership first
        memory = brain.get_memory_by_id(memory_id)
        if not memory:
            logger.warning("Memory not found: %s", memory_id)
            raise HTTPException(status_code=404, detail="Memory not found")

        if memory.get("user_id") != user_email:
            logger.warning(
                "Unauthorized delete attempt by %s for memory %s (owner: %s)",
                user_email,
                memory_id,
                memory.get("user_id"),
            )
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this memory"
            )

        brain.delete_memory(memory_id)
        logger.info("Memory %s deleted successfully by user %s", memory_id, user_email)
        return {"message": "Memory deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete memory %s for user %s: %s", memory_id, user_email, e
        )
        raise HTTPException(status_code=500, detail="Failed to delete memory") from e
