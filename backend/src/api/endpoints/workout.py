"""
API endpoints for workout log management.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, HTTPException

from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from src.core.logs import logger
from src.api.models.workout_log import WorkoutListResponse, WorkoutWithId
from src.services.database import MongoDatabase

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
DatabaseDep = Annotated[MongoDatabase, Depends(get_mongo_database)]


@router.get("/list", response_model=WorkoutListResponse)
def list_workouts(
    user_email: CurrentUser,
    db: DatabaseDep,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=10, ge=1, le=50, description="Items per page")
) -> WorkoutListResponse:
    """
    Retrieves paginated workout logs for the authenticated user.

    Args:
        user_email (str): The authenticated user's email.
        db (MongoDatabase): The database dependency.
        page (int): Page number (1-indexed).
        page_size (int): Number of items per page (1-50).

    Returns:
        WorkoutListResponse: Paginated list of user workout logs.
    """
    logger.info("=== Workout List Request ===")
    logger.info("User: %s, Page: %d, PageSize: %d", user_email, page, page_size)

    try:
        raw_workouts, total = db.get_workouts_paginated(
            user_email=user_email,
            page=page,
            page_size=page_size
        )
        
        workouts = [WorkoutWithId(**w) for w in raw_workouts]
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        logger.info(
            "Returning %d workouts for user: %s (page %d/%d)",
            len(workouts), user_email, page, total_pages
        )
        return WorkoutListResponse(
            workouts=workouts,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception as e:
        logger.error("Error listing workouts for user %s: %s", user_email, e)
        raise HTTPException(status_code=500, detail="Failed to retrieve workouts") from e
