from pydantic import BaseModel, Field, ConfigDict
from datetime import date as DateType


class WeightLogInput(BaseModel):
    """
    Represents a daily weight log entry for input (without user identification).
    """

    date: DateType = Field(..., description="The date of the weight log")
    weight_kg: float = Field(..., gt=0, lt=500, description="The weight in kilograms")

    # Body Composition (optional)
    body_fat_pct: float | None = Field(
        None, ge=0, le=100, description="Body fat percentage"
    )
    muscle_mass_pct: float | None = Field(
        None, ge=0, le=100, description="Muscle mass percentage"
    )
    bone_mass_kg: float | None = Field(None, ge=0, lt=20, description="Bone mass in kg")
    body_water_pct: float | None = Field(
        None, ge=0, le=100, description="Body water percentage"
    )
    visceral_fat: float | None = Field(
        None, ge=0, le=50, description="Visceral fat level"
    )
    bmr: int | None = Field(None, ge=500, le=5000, description="Basal Metabolic Rate")
    bmi: float | None = Field(None, ge=10, le=60, description="Body Mass Index")

    # Body Measurements (optional, in cm)
    neck_cm: float | None = Field(None, ge=20, le=100, description="Neck circumference")
    chest_cm: float | None = Field(None, ge=40, le=200, description="Chest circumference")
    waist_cm: float | None = Field(None, ge=40, le=200, description="Waist circumference")
    hips_cm: float | None = Field(None, ge=40, le=200, description="Hips circumference")
    bicep_r_cm: float | None = Field(None, ge=10, le=100, description="Right bicep circumference")
    bicep_l_cm: float | None = Field(None, ge=10, le=100, description="Left bicep circumference")
    thigh_r_cm: float | None = Field(None, ge=20, le=150, description="Right thigh circumference")
    thigh_l_cm: float | None = Field(None, ge=20, le=150, description="Left thigh circumference")
    calf_r_cm: float | None = Field(None, ge=10, le=100, description="Right calf circumference")
    calf_l_cm: float | None = Field(None, ge=10, le=100, description="Left calf circumference")

    # Metadata
    source: str | None = Field(
        "manual", description="Data source: manual, scale_import, chat"
    )
    notes: str | None = Field(None, description="Optional notes for the weight log")


class WeightLog(WeightLogInput):
    """
    Represents a daily weight log entry stored in the database.
    """

    user_email: str = Field(
        ..., description="The email of the user who logged the weight"
    )
    trend_weight: float | None = Field(
        None, description="Calculated trend weight using EMA smoothing"
    )



class WeightWithId(WeightLog):
    """Weight log with MongoDB ID for API responses."""
    
    id: str = Field(..., alias="_id", description="ID do log no MongoDB")

    model_config = ConfigDict(populate_by_name=True)
