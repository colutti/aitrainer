from pydantic import BaseModel, Field

class MetabolismResponse(BaseModel):
    """
    Response model for the Adaptive TDEE calculation.
    """
    tdee: int = Field(..., description="Calculated Total Daily Energy Expenditure")
    confidence: str = Field(..., description="Confidence level: 'high', 'medium', 'low', 'none'")
    avg_calories: int = Field(..., description="Average daily calories consumed in period")
    weight_change_per_week: float = Field(..., description="Average weekly weight change in kg")
    logs_count: int = Field(..., description="Number of nutrition logs used for calculation")
    startDate: str = Field(..., description="Start date of the analysis period (ISO)")
    endDate: str = Field(..., description="End date of the analysis period (ISO)")
    start_weight: float = Field(..., description="Starting weight (EMA smoothed)")
    end_weight: float = Field(..., description="Ending weight (EMA smoothed)")
    
    # New fields for UX
    daily_target: int | None = Field(None, description="Calculated daily calorie target")
    goal_weekly_rate: float | None = Field(None, description="User's goal weekly weight change rate")
    goal_type: str | None = Field(None, description="User's goal type (lose, gain, maintain)")
    message: str | None = Field(None, description="Optional informational message")
