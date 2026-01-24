from typing import Annotated
from datetime import date
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from src.services.auth import verify_token
from src.core.deps import get_ai_trainer_brain, get_mongo_database
from src.services.trainer import AITrainerBrain
from src.services.database import MongoDatabase
from src.api.models.weight_log import WeightLog, WeightLogInput
from src.api.models.import_result import ImportResult
from src.services.zepp_life_import_service import import_zepp_life_data
from src.core.logs import logger

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
AITrainerBrainDep = Annotated[AITrainerBrain, Depends(get_ai_trainer_brain)]
DatabaseDep = Annotated[MongoDatabase, Depends(get_mongo_database)]


@router.post("")
def log_weight(
    log_input: WeightLogInput,
    user_email: CurrentUser,
    brain: AITrainerBrainDep,
    db: DatabaseDep,
) -> dict:
    """
    Logs a weight entry for the user.
    If an entry exists for the same date, it updates it.
    """
    from src.services.adaptive_tdee import AdaptiveTDEEService

    tdee_service = AdaptiveTDEEService(db)

    # 1. Get previous log to continue the EMA trend
    # We look for the most recent log BEFORE the current date
    recent_logs = db.weight.get_logs(user_email, limit=1)
    prev_trend = None
    if recent_logs:
        # If logging for today, the "limit=1" might be today's log (if updating)
        # or the previous day's log.
        # To be safe, let's just get the latest and check date.
        # But if it's an update, we should ideally look for the *actual* previous one.
        # For simplicity and performance, if we have a trend weight in the latest log, we use it.
        prev_trend = recent_logs[0].trend_weight

    # 2. Calculate new trend weight
    new_trend = tdee_service.calculate_ema_trend(log_input.weight_kg, prev_trend)

    # 3. Create full WeightLog
    log = WeightLog(user_email=user_email, trend_weight=new_trend, **log_input.model_dump())

    doc_id, is_new = db.weight.save_log(log)

    return {
        "message": "Weight logged successfully",
        "id": doc_id,
        "is_new": is_new,
        "date": log.date,
        "trend_weight": round(new_trend, 2) if new_trend else None,
    }


@router.delete("/{date_str}")
def delete_weight_log(date_str: str, user_email: CurrentUser, brain: AITrainerBrainDep):
    """
    Deletes a weight log for a specific date (YYYY-MM-DD).
    """
    try:
        log_date = date.fromisoformat(date_str)
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}

    success = brain._database.delete_weight_log(
        user_email=user_email, log_date=log_date
    )

    if not success:
        return {"message": "Log not found or could not be deleted", "deleted": False}

    return {"message": "Weight log deleted successfully", "deleted": True}


@router.get("")
def get_weight_logs(
    user_email: CurrentUser, brain: AITrainerBrainDep, limit: int = 30
) -> list[WeightLog]:
    """
    Retrieves recent weight logs for the user.
    """
    return brain._database.get_weight_logs(user_email=user_email, limit=limit)


@router.get("/stats")
def get_body_composition_stats(
    user_email: CurrentUser, brain: AITrainerBrainDep
) -> dict:
    """
    Returns latest body composition and trends for dashboard.
    """
    # Get last 30 logs for trends
    logs = brain._database.get_weight_logs(user_email, limit=30)

    if not logs:
        return {"latest": None, "weight_trend": [], "fat_trend": [], "muscle_trend": []}

    # Logs are returned in DESC order (latest first)
    logs_asc = sorted(logs, key=lambda x: x.date)

    # Serialize latest log to dict
    latest_dict = logs[0].model_dump()
    latest_dict["date"] = logs[0].date.isoformat()  # Convert date to string

    return {
        "latest": latest_dict,
        "weight_trend": [
            {"date": log_item.date.isoformat(), "value": log_item.weight_kg}
            for log_item in logs_asc
        ],
        "fat_trend": [
            {"date": log_item.date.isoformat(), "value": log_item.body_fat_pct}
            for log_item in logs_asc
            if log_item.body_fat_pct
        ],
        "muscle_trend": [
            {"date": log_item.date.isoformat(), "value": log_item.muscle_mass_pct}
            for log_item in logs_asc
            if log_item.muscle_mass_pct
        ],
    }


@router.post("/import/zepp-life", response_model=ImportResult)
async def import_zepp_life(
    user_email: CurrentUser, db: DatabaseDep, file: UploadFile = File(...)
) -> ImportResult:
    """
    Import weight/body composition data from Zepp Life CSV export.
    """
    logger.info("Importing Zepp Life data for user: %s", user_email)

    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="O arquivo deve ser um CSV.")

    try:
        content = await file.read()
        csv_content = content.decode("utf-8")

        result = import_zepp_life_data(user_email, csv_content, db)

        logger.info(
            "Import finished for %s. Created: %d, Updated: %d, Errors: %d",
            user_email,
            result.created,
            result.updated,
            result.errors,
        )
        return result

    except ValueError as e:
        logger.warning(
            "Validation error importing Zepp Life CSV for %s: %s", user_email, e
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error importing Zepp Life CSV for user %s: %s", user_email, e)
        raise HTTPException(status_code=500, detail="Falha ao importar dados.") from e
