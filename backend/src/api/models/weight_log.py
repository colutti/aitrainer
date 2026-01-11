from pydantic import BaseModel, Field
from datetime import date as DateType

class WeightLog(BaseModel):
    """
    Represents a daily weight log entry.
    """
    user_email: str = Field(..., description="The email of the user who logged the weight")
    date: DateType = Field(..., description="The date of the weight log")
    weight_kg: float = Field(..., gt=0, lt=500, description="The weight in kilograms")
    notes: str | None = Field(None, description="Optional notes for the weight log")
