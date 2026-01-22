from datetime import date
from typing import List
from pydantic import BaseModel, Field
from src.api.models.weight_log import WeightLog
from src.api.models.nutrition_log import NutritionLog
from src.api.models.user_profile import UserProfile


class AnalysisPeriod(BaseModel):
    """
    Represents the time period for data analysis.
    """

    start_date: date
    end_date: date


class RawMetabolismData(BaseModel):
    """
    Collection of raw data required for metabolism analysis.
    """

    weight_logs: List[WeightLog] = Field(..., description="List of recorded weight logs")
    nutrition_logs: List[NutritionLog] = Field(
        ..., description="List of recorded nutrition logs"
    )
    user_profile: UserProfile | None = Field(..., description="The user's profile data")
    period: AnalysisPeriod = Field(..., description="The analyzed time period")
