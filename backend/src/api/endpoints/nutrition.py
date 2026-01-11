"""
API endpoints for nutrition management.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, HTTPException

from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from src.core.logs import logger
from src.api.models.nutrition_log import NutritionWithId
from src.api.models.nutrition_stats import NutritionStats
from src.services.database import MongoDatabase
from pydantic import BaseModel

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
DatabaseDep = Annotated[MongoDatabase, Depends(get_mongo_database)]


class NutritionListResponse(BaseModel):
    """Paginated response for nutrition list API."""
    logs: list[NutritionWithId]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get("/list", response_model=NutritionListResponse)
def list_nutrition(
    user_email: CurrentUser,
    db: DatabaseDep,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=10, ge=1, le=50, description="Items per page"),
    days: int | None = Query(default=None, description="Filter by last N days")
) -> NutritionListResponse:
    """
    Retrieves paginated nutrition logs for the authenticated user.
    """
    logger.info("=== Nutrition List Request ===")
    logger.info("User: %s, Page: %d, PageSize: %d", user_email, page, page_size)

    try:
        raw_logs, total = db.get_nutrition_paginated(
            user_email=user_email,
            page=page,
            page_size=page_size,
            days=days
        )
        
        logs = [NutritionWithId(**log) for log in raw_logs]
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        logger.info(
            "Returning %d logs for user: %s (page %d/%d)",
            len(logs), user_email, page, total_pages
        )
        return NutritionListResponse(
            logs=logs,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception as e:
        logger.error("Error listing nutrition logs for user %s: %s", user_email, e)
        raise HTTPException(status_code=500, detail="Failed to retrieve nutrition logs") from e


@router.get("/stats", response_model=NutritionStats)
def get_nutrition_stats(
    user_email: CurrentUser,
    db: DatabaseDep
) -> NutritionStats:
    """
    Retrieves nutrition stats for the dashboard.
    """
    logger.info("Fetching nutrition stats for user: %s", user_email)
    try:
        return db.get_nutrition_stats(user_email)
    except Exception as e:
        logger.error("Error fetching nutrition stats for user %s: %s", user_email, e)
        raise HTTPException(status_code=500, detail="Failed to retrieve nutrition stats") from e


@router.get("/today", response_model=NutritionWithId | None)
def get_today_nutrition(
    user_email: CurrentUser,
    db: DatabaseDep
) -> NutritionWithId | None:
    """
    Retrieves today's nutrition log if exists by reusing stats logic.
    """
    logger.info("Fetching today's nutrition for user: %s", user_email)
    try:
        stats = db.get_nutrition_stats(user_email)
        return stats.today
    except Exception as e:
        logger.error("Error fetching today's nutrition for user %s: %s", user_email, e)
        raise HTTPException(status_code=500, detail="Failed to retrieve today's nutrition") from e
