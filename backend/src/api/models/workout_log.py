"""
Pydantic models for workout logging.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ExerciseLog(BaseModel):
    """
    Represents a single exercise entry within a workout session.

    Attributes:
        name: Exercise name (e.g., "Supino reto", "Agachamento").
        sets: Number of sets performed.
        reps: Number of repetitions per set.
        weight_kg: Weight used in kilograms (optional).
    """

    name: str = Field(..., description="Nome do exercício")
    sets: int = Field(..., ge=1, description="Número de séries")
    reps: int = Field(..., ge=1, description="Número de repetições")
    weight_kg: Optional[float] = Field(default=None, ge=0, description="Peso em kg")


class WorkoutLog(BaseModel):
    """
    Represents a complete workout session logged by the user.

    Attributes:
        user_email: Email of the user who performed the workout.
        date: Date and time of the workout.
        workout_type: Type of workout (e.g., "Legs", "Upper", "Push").
        exercises: List of exercises performed.
        duration_minutes: Total workout duration in minutes (optional).
    """

    user_email: str = Field(..., description="Email do usuário")
    date: datetime = Field(default_factory=datetime.now, description="Data do treino")
    workout_type: Optional[str] = Field(
        default=None, description="Tipo de treino (Legs, Upper, Push, etc.)"
    )
    exercises: list[ExerciseLog] = Field(..., description="Lista de exercícios")
    duration_minutes: Optional[int] = Field(
        default=None, ge=1, description="Duração em minutos"
    )
