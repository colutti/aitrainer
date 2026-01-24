from pydantic import BaseModel, Field


class WeightTrendPoint(BaseModel):
    """
    Represents a single point in the weight history.
    """

    date: str
    weight: float
    trend: float | None = None


class MetabolismResponse(BaseModel):
    """
    Response model for the Adaptive TDEE calculation.
    """

    tdee: int = Field(..., description="Calculated Total Daily Energy Expenditure")
    confidence: str = Field(
        ..., description="Confidence level: 'high', 'medium', 'low', 'none'"
    )
    avg_calories: int = Field(
        ..., description="Average daily calories consumed in period"
    )
    weight_change_per_week: float = Field(
        ..., description="Average weekly weight change in kg"
    )
    logs_count: int = Field(
        ..., description="Number of nutrition logs used for calculation"
    )
    startDate: str = Field(..., description="Start date of the analysis period (ISO)")
    endDate: str = Field(..., description="End date of the analysis period (ISO)")
    start_weight: float = Field(..., description="Starting weight (trend estimation)")
    end_weight: float = Field(..., description="Ending weight (trend estimation)")

    # New fields for UX
    daily_target: int | None = Field(
        None, description="Calculated daily calorie target"
    )
    goal_weekly_rate: float | None = Field(
        None, description="User's goal weekly weight change rate"
    )
    goal_type: str | None = Field(
        None, description="User's goal type (lose, gain, maintain)"
    )
    status: str | None = Field(
        None, description="Semantic status (deficit, surplus, maintenance)"
    )
    energy_balance: float | None = Field(
        None, description="Difference between avg calories and TDEE"
    )
    is_stable: bool | None = Field(
        None, description="Whether the energy balance is within stability range"
    )

    latest_weight: float | None = Field(
        None, description="Latest actual weight recorded"
    )

    # Optional composition & details
    fat_change_kg: float | None = Field(None)
    muscle_change_kg: float | None = Field(
        None, description="Change in muscle mass (uses scale data)"
    )
    start_fat_pct: float | None = Field(None)
    end_fat_pct: float | None = Field(None)
    start_muscle_pct: float | None = Field(None)
    end_muscle_pct: float | None = Field(None)
    scale_bmr: int | None = Field(None)

    # New Trend Fields
    weight_trend: list[WeightTrendPoint] | None = Field(
        None, description="History of weights including trend values"
    )
    expenditure_trend: str | None = Field(
        None, description="Direction of TDEE change (up, down, stable)"
    )
    consistency_score: int | None = Field(
        None, description="Adherence score (0-100) based on logs"
    )

    message: str | None = Field(None, description="Optional informational message")
