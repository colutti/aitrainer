"""
API endpoints for nutrition management.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, HTTPException, File, UploadFile

from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from src.core.logs import logger
from src.api.models.nutrition_log import NutritionWithId
from src.api.models.nutrition_stats import NutritionStats
from src.services.database import MongoDatabase
from src.api.models.import_result import ImportResult
from src.services.myfitnesspal_import_service import import_nutrition_from_csv
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
    days: int | None = Query(default=None, description="Filter by last N days"),
) -> NutritionListResponse:
    """
    Retrieves paginated nutrition logs for the authenticated user.
    """
    logger.info("=== Nutrition List Request ===")
    logger.info("User: %s, Page: %d, PageSize: %d", user_email, page, page_size)

    try:
        raw_logs, total = db.get_nutrition_paginated(
            user_email=user_email, page=page, page_size=page_size, days=days
        )

        logs = [NutritionWithId(**log) for log in raw_logs]
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        logger.info(
            "Returning %d logs for user: %s (page %d/%d)",
            len(logs),
            user_email,
            page,
            total_pages,
        )
        return NutritionListResponse(
            logs=logs,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception as e:
        logger.error("Error listing nutrition logs for user %s: %s", user_email, e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve nutrition logs"
        ) from e


@router.get("/stats", response_model=NutritionStats)
def get_nutrition_stats(user_email: CurrentUser, db: DatabaseDep) -> NutritionStats:
    """
    Retrieves nutrition stats for the dashboard.
    """
    logger.info("Fetching nutrition stats for user: %s", user_email)
    try:
        return db.get_nutrition_stats(user_email)
    except Exception as e:
        logger.error("Error fetching nutrition stats for user %s: %s", user_email, e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve nutrition stats"
        ) from e


@router.get("/today", response_model=NutritionWithId | None)
def get_today_nutrition(
    user_email: CurrentUser, db: DatabaseDep
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
        raise HTTPException(
            status_code=500, detail="Failed to retrieve today's nutrition"
        ) from e


class CreateNutritionLogRequest(BaseModel):
    """Request model for creating a nutrition log."""
    date: str  # ISO format date string
    source: str = "manual"
    calories: int
    protein_grams: float
    carbs_grams: float
    fat_grams: float
    fiber_grams: float | None = None
    sodium_mg: float | None = None


@router.post("/log", response_model=NutritionWithId)
def create_nutrition_log(
    user_email: CurrentUser,
    db: DatabaseDep,
    log_data: CreateNutritionLogRequest,
) -> NutritionWithId:
    """
    Creates a new nutrition log for the authenticated user.
    """
    logger.info("Creating nutrition log for user: %s", user_email)
    try:
        from src.api.models.nutrition_log import NutritionLog
        from datetime import datetime

        # Parse date string to datetime
        date_obj = datetime.fromisoformat(log_data.date)

        # Create nutrition log with user_email
        nutrition_log = NutritionLog(
            user_email=user_email,
            date=date_obj,
            calories=log_data.calories,
            protein_grams=log_data.protein_grams,
            carbs_grams=log_data.carbs_grams,
            fat_grams=log_data.fat_grams,
            fiber_grams=log_data.fiber_grams,
            sodium_mg=log_data.sodium_mg,
            source=log_data.source,
        )

        log_id, _ = db.save_nutrition_log(nutrition_log)

        # Retrieve the saved log to return it
        saved_log = db.get_nutrition_by_id(log_id)
        if not saved_log:
            raise HTTPException(status_code=500, detail="Failed to retrieve saved log")

        # Convert ObjectId to string for Pydantic model
        if "_id" in saved_log:
            saved_log["_id"] = str(saved_log["_id"])

        return NutritionWithId(**saved_log)
    except ValueError as e:
        logger.warning("Validation error creating nutrition log for %s: %s", user_email, e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error creating nutrition log for user %s: %s", user_email, e)
        raise HTTPException(status_code=500, detail="Failed to create nutrition log") from e


@router.post("/import/myfitnesspal", response_model=ImportResult)
async def import_myfitnesspal(
    user_email: CurrentUser, db: DatabaseDep, file: UploadFile = File(...)
) -> ImportResult:
    """
    Import nutrition data from MyFitnessPal CSV export.
    Expects a CSV file with Portuguese headers.
    """
    logger.info("Importing MyFitnessPal data for user: %s", user_email)

    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="O arquivo deve ser um CSV.")

    try:
        content = await file.read()
        csv_content = content.decode("utf-8")

        result = import_nutrition_from_csv(user_email, csv_content, db)

        logger.info(
            "Import finished for %s. Created: %d, Updated: %d, Errors: %d",
            user_email,
            result.created,
            result.updated,
            result.errors,
        )
        return result

    except ValueError as e:
        logger.warning("Validation error importing CSV for %s: %s", user_email, e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error importing CSV for user %s: %s", user_email, e)
        raise HTTPException(status_code=500, detail="Falha ao importar dados.") from e


@router.delete("/{log_id}")
def delete_nutrition(
    log_id: str, user_email: CurrentUser, db: DatabaseDep
) -> dict:
    """
    Deletes a specific nutrition log for the authenticated user.
    """
    logger.info("=== Nutrition Delete Request ===")
    logger.info("User: %s, Log ID: %s", user_email, log_id)

    try:
        # Validate ownership first
        log = db.get_nutrition_by_id(log_id)
        if not log:
            logger.warning("Nutrition log not found: %s", log_id)
            raise HTTPException(status_code=404, detail="Nutrition log not found")

        if log.get("user_email") != user_email:
            logger.warning(
                "Unauthorized delete attempt by %s for log %s (owner: %s)",
                user_email,
                log_id,
                log.get("user_email"),
            )
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this nutrition log"
            )

        deleted = db.delete_nutrition_log(log_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Nutrition log not found for deletion")

        logger.info("Nutrition log %s deleted successfully by user %s", log_id, user_email)
        return {"message": "Nutrition log deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete nutrition log %s for user %s: %s", log_id, user_email, e
        )
        raise HTTPException(status_code=500, detail="Failed to delete nutrition log") from e
