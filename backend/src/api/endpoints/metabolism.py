from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from src.core.deps import get_ai_trainer_brain, get_mongo_database
from src.services.trainer import AITrainerBrain
from src.services.auth import verify_token
from src.services.database import MongoDatabase
from src.services.adaptive_tdee import AdaptiveTDEEService

router = APIRouter()


@router.get("/summary")
async def get_metabolism_summary(
    weeks: int = 3,
    user_email: str = Depends(verify_token),
    db: MongoDatabase = Depends(get_mongo_database),
):
    """
    Returns a summary of the user's metabolism stats (TDEE, trend, confidence).
    """
    tdee_service = AdaptiveTDEEService(db)
    stats = tdee_service.calculate_tdee(user_email, lookback_weeks=weeks)
    return stats


@router.get("/insight")
async def get_metabolism_insight_stream(
    weeks: int = 3,
    user_email: str = Depends(verify_token),
    db: MongoDatabase = Depends(get_mongo_database),
    brain: AITrainerBrain = Depends(get_ai_trainer_brain),
):
    """
    Streams an AI-generated insight about the user's metabolism stats.
    """
    # Quick check for data availability using TDEE service (lightweight check)
    tdee_service = AdaptiveTDEEService(db)
    stats = tdee_service.calculate_tdee(user_email, lookback_weeks=weeks)

    # Check if there is absolutely no data or insufficient data
    if not stats or stats.get("confidence") == "none":

        async def empty_stream():
            yield "Dados insuficientes para análise no período."

        return StreamingResponse(empty_stream(), media_type="text/event-stream")

    return StreamingResponse(
        brain.generate_insight_stream(user_email, weeks=weeks),
        media_type="text/event-stream",
    )
