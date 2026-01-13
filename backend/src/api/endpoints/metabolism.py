from typing import Annotated
from fastapi import APIRouter, Depends, Query

from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from src.services.database import MongoDatabase
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.api.models.metabolism import MetabolismResponse

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]

@router.get("/summary", response_model=MetabolismResponse)
def get_metabolism_summary(
    user_email: CurrentUser,
    db: MongoDatabase = Depends(get_mongo_database),
    weeks: int = Query(3, ge=2, le=8, description="Number of weeks to analyze (min 2, max 8)")
):
    """
    Retrieves the user's metabolic summary (TDEE, trends) based on recent logs.
    """
    service = AdaptiveTDEEService(db)
    result = service.calculate_tdee(user_email, lookback_weeks=weeks)
    
    # If no data, return a structured response with 0 TDEE (handled by service)
    # The service returns a dict that matches the model roughly, 
    # but 'reason' is not in model. let's check structure.
    # Service "insufficient_data" returns {tdee:0, confidence:none...}
    # It misses fields required by Pydantic model.
    # We should handle flexible response or ensure service fills dummy data.
    
    if result.get("tdee") == 0 and result.get("reason"):
        # Insufficient data case
        return {
             "tdee": 0,
             "confidence": "none",
             "avg_calories": 0,
             "weight_change_per_week": 0.0,
             "logs_count": 0,
             "startDate": "",
             "endDate": "",
             "start_weight": 0.0,
             "end_weight": 0.0,
             "daily_target": 0,
             "goal_weekly_rate": 0.0,
             "goal_type": "maintain",
             "message": result.get("reason")
        }
        
    return result
