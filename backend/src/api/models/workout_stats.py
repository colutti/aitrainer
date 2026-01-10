"""
Pydantic models for workout statistics.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from src.api.models.workout_log import WorkoutWithId


class PersonalRecord(BaseModel):
    """Represents a personal record (max weight) for an exercise."""
    exercise_name: str
    weight: float
    reps: int
    date: datetime
    workout_id: str


class VolumeStat(BaseModel):
    """Volume statistic for a category (e.g. 'Pernas')."""
    category: str
    volume: float


class WorkoutStats(BaseModel):
    """Aggregated workout statistics for the dashboard."""
    current_streak_weeks: int = Field(..., description="Consecutive weeks with >= 3 workouts")
    weekly_frequency: list[bool] = Field(..., description="List of 7 bools indicating workout days (Sun-Sat or Mon-Sun)")
    weekly_volume: list[VolumeStat] = Field(..., description="Volume per category for the current week")
    recent_prs: list[PersonalRecord] = Field(..., description="Recent personal records")
    total_workouts: int = Field(..., description="Total number of workouts")
    last_workout: Optional[WorkoutWithId] = Field(None, description="The most recent workout logged")
