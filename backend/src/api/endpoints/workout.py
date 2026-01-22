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
    page_size: int = Query(default=10, ge=1, le=50, description="Items per page"),
    workout_type: str | None = Query(
        default=None, description="Filter by workout type"
    ),
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
            page_size=page_size,
            workout_type=workout_type,
        )

        workouts = [WorkoutWithId(**w) for w in raw_workouts]
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        logger.info(
            "Returning %d workouts for user: %s (page %d/%d)",
            len(workouts),
            user_email,
            page,
            total_pages,
        )
        return WorkoutListResponse(
            workouts=workouts,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception as e:
        logger.error("Error listing workouts for user %s: %s", user_email, e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve workouts"
        ) from e


@router.get("/types", response_model=list[str])
def get_types(user_email: CurrentUser, db: DatabaseDep) -> list[str]:
    """Retrieves all distinct workout types for the user."""
    logger.info("Fetching workout types for user: %s", user_email)
    try:
        return db.get_workout_types(user_email)
    except Exception as e:
        logger.error("Error fetching workout types for user %s: %s", user_email, e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve workout types"
        ) from e


@router.delete("/{workout_id}")
def delete_workout(
    workout_id: str, user_email: CurrentUser, db: DatabaseDep
) -> dict:
    """
    Deletes a specific workout log for the authenticated user.
    """
    logger.info("=== Workout Delete Request ===")
    logger.info("User: %s, Workout ID: %s", user_email, workout_id)

    try:
        # Validate ownership first
        workout = db.get_workout_by_id(workout_id)
        if not workout:
            logger.warning("Workout not found: %s", workout_id)
            raise HTTPException(status_code=404, detail="Workout not found")

        if workout.get("user_email") != user_email:
            logger.warning(
                "Unauthorized delete attempt by %s for workout %s (owner: %s)",
                user_email,
                workout_id,
                workout.get("user_email"),
            )
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this workout"
            )

        deleted = db.delete_workout_log(workout_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Workout not found for deletion")

        logger.info("Workout %s deleted successfully by user %s", workout_id, user_email)
        return {"message": "Workout deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete workout %s for user %s: %s", workout_id, user_email, e
        )
        raise HTTPException(status_code=500, detail="Failed to delete workout") from e
