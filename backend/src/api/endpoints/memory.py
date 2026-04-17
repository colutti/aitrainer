"""Endpoints for managing user memories and insights."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from src.core.demo_access import WritableCurrentUser
from src.services.auth import verify_token
from src.core.deps import get_ai_trainer_brain
from src.core.logs import logger
from src.api.models.memory_item import MemoryItem, MemoryListResponse
from src.utils.pagination import calculate_total_pages

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
def _normalize_user_id(user_id: str) -> str:
    return user_id.strip().lower()


@router.post("", response_model=MemoryItem)
async def create_memory(
    user_email: WritableCurrentUser,
    brain: Annotated[Any, Depends(get_ai_trainer_brain)],
    memory_data: dict,
) -> MemoryItem:
    """
    Creates a new memory / insight for the user.
    Mainly for testing or manual overrides.
    """
    text = memory_data.get("memory")
    if not text:
        raise HTTPException(status_code=400, detail="Missing 'memory' text")

    memory_id = await brain.add_memory(text, user_email)

    # Return the newly created item
    return MemoryItem(
        id=memory_id,
        memory=text,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@router.get("/list", response_model=MemoryListResponse)
async def list_memories(
    user_email: CurrentUser,
    brain: Annotated[Any, Depends(get_ai_trainer_brain)],
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=10, ge=1, le=50, description="Items per page"),
) -> MemoryListResponse:
    """
    Retrieves paginated memories for the authenticated user.

    Args:
        user_email (str): The authenticated user's email.
        brain (AITrainerBrain): The AI trainer brain dependency.
        page (int): Page number (1-indexed).
        page_size (int): Number of items per page (1-50).

    Returns:
        MemoryListResponse: Paginated list of user memories.
    """
    logger.info("=== Memory List Request (Paginated) ===")
    logger.info("User: %s, Page: %d, PageSize: %d", user_email, page, page_size)

    try:
        raw_memories, total = await brain.get_memories_paginated(
            user_id=user_email,
            page=page,
            page_size=page_size,
        )

        logger.debug("Processing %d raw memories", len(raw_memories))

        memories = [
            MemoryItem(
                id=mem.get("id", ""),
                memory=mem.get("memory", ""),
                translations=mem.get("translations"),
                created_at=mem.get("created_at"),
                updated_at=mem.get("updated_at"),
            )
            for mem in raw_memories
        ]

        total_pages = calculate_total_pages(total, page_size)

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
    memory_id: str,
    user_email: WritableCurrentUser,
    brain: Annotated[Any, Depends(get_ai_trainer_brain)],
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

        memory_owner = _normalize_user_id(str(memory.get("user_id", "")))
        requester = _normalize_user_id(user_email)
        if memory_owner != requester:
            logger.warning(
                "Unauthorized delete attempt by %s for memory %s (owner: %s)",
                user_email,
                memory_id,
                memory.get("user_id"),
            )
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this memory"
            )

        brain.delete_memory(memory_id, user_email)
        logger.info("Memory %s deleted successfully by user %s", memory_id, user_email)
        return {"message": "Memory deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete memory %s for user %s: %s", memory_id, user_email, e
        )
        raise HTTPException(status_code=500, detail="Failed to delete memory") from e
