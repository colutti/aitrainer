"""
API endpoints for workout statistics.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from src.services.database import MongoDatabase
from src.api.models.workout_stats import WorkoutStats
from src.core.logs import logger

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
DatabaseDep = Annotated[MongoDatabase, Depends(get_mongo_database)]

@router.get("/stats", response_model=WorkoutStats)
def get_dashboard_stats(
    user_email: CurrentUser,
    db: DatabaseDep
) -> WorkoutStats:
    """
    Retrieves aggregated workout statistics for the dashboard.
    """
    logger.info("Fetching workout stats for user: %s", user_email)
    try:
        return db.get_workout_stats(user_email)
    except Exception as e:
        logger.error("Error fetching stats for user %s: %s", user_email, e)
        raise HTTPException(status_code=500, detail="Failed to retrieve workout stats") from e
