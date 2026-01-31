from fastapi import APIRouter, Depends, BackgroundTasks
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



