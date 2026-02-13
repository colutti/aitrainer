"""
Admin endpoints for token analytics and consumption tracking.
Requires admin role for access.
"""

from typing import Annotated
from fastapi import APIRouter, Query, Depends
from src.core.auth import AdminUser
from src.core.deps import get_mongo_database
from src.services.database import MongoDatabase
from src.core.logs import logger
from src.core.pricing import get_cost_usd

router = APIRouter(prefix="/admin/tokens", tags=["admin"])

MongoDBDep = Annotated[MongoDatabase, Depends(get_mongo_database)]


@router.get("/summary")
def get_token_summary(
    admin_email: AdminUser,
    db: MongoDBDep,
    days: int = Query(30, ge=1, le=365),
) -> dict:
    """
    Retrieves aggregated token consumption per user over the last N days.
    Includes total tokens (input/output), message count, and estimated cost.
    """
    logger.info(
        "Admin %s requesting token summary (days=%d)", admin_email, days
    )

    try:
        summary = db.prompts.get_token_summary(days=days)

        # Add cost calculation for each user
        for item in summary:
            model = item.get("model", "unknown")
            total_input = item.get("total_input", 0)
            total_output = item.get("total_output", 0)
            item["cost_usd"] = get_cost_usd(model, total_input, total_output)

        return {
            "data": summary,
            "days": days,
            "total_users_with_tokens": len(summary),
        }
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Error fetching token summary: %s", e)
        return {"data": [], "error": str(e)}


@router.get("/timeseries")
def get_token_timeseries(
    admin_email: AdminUser,
    db: MongoDBDep,
    days: int = Query(30, ge=1, le=365),
    user_email: str | None = Query(None),
) -> dict:
    """
    Retrieves daily token consumption for charting.
    If user_email is provided, returns data for that user only.
    Otherwise returns aggregated data for all users.
    """
    logger.info(
        "Admin %s requesting token timeseries (days=%d, user=%s)",
        admin_email,
        days,
        user_email or "all",
    )

    try:
        timeseries = db.prompts.get_token_timeseries(
            days=days, user_email=user_email
        )

        return {
            "data": timeseries,
            "days": days,
            "user_email": user_email,
            "data_points": len(timeseries),
        }
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Error fetching token timeseries: %s", e)
        return {"data": [], "error": str(e)}
