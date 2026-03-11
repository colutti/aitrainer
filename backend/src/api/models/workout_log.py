"""
Pydantic models for workout logging.
"""

from datetime import datetime, date as py_date
from typing import Annotated, Any

from bson import ObjectId
from pydantic import BaseModel, Field, model_validator, ConfigDict, BeforeValidator


class ExerciseLog(BaseModel):
    """
    Represents a single exercise entry within a workout session.

    Attributes:
        name: Exercise name (e.g., "Supino reto", "Agachamento").
        sets: Number of sets performed.
        reps_per_set: List of repetitions for each set.
        weights_per_set: List of weights in kg for each set (optional).
        distance_meters_per_set: List of distances in meters for each set (cardio, optional).
        duration_seconds_per_set: List of durations in seconds for each set (cardio, optional).
    """

    name: str = Field(..., description="Nome do exercício")
    sets: int = Field(..., ge=1, description="Número de séries")
    reps_per_set: list[int] = Field(..., description="Repetições por série")
    weights_per_set: list[float] = Field(
        default_factory=list, description="Pesos em kg por série"
    )
    distance_meters_per_set: list[float] = Field(
        default_factory=list, description="Distância em metros por série (cardio)"
    )
    duration_seconds_per_set: list[int] = Field(
        default_factory=list, description="Duração em segundos por série (cardio)"
    )

    @model_validator(mode="after")
    def validate_lists_match_sets(self) -> "ExerciseLog":
        """Valida que as listas têm o tamanho correto."""
        if len(self.reps_per_set) != self.sets:
            raise ValueError(
                f"reps_per_set deve ter {self.sets} elementos, tem {len(self.reps_per_set)}"
            )
        if self.weights_per_set and len(self.weights_per_set) != self.sets:
            raise ValueError(
                f"weights_per_set deve ter {self.sets} elementos, tem {len(self.weights_per_set)}"
            )
        if self.distance_meters_per_set and len(self.distance_meters_per_set) != self.sets:
            raise ValueError(
                f"distance_meters_per_set deve ter {self.sets} elementos, tem {len(self.distance_meters_per_set)}"
            )
        if self.duration_seconds_per_set and len(self.duration_seconds_per_set) != self.sets:
            raise ValueError(
                f"duration_seconds_per_set deve ter {self.sets} elementos, tem {len(self.duration_seconds_per_set)}"
            )
        return self


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
    date: datetime | py_date = Field(default_factory=datetime.now, description="Data do treino")
    workout_type: str | None = Field(
        default=None, description="Tipo de treino (Legs, Upper, Push, etc.)"
    )
    exercises: list[ExerciseLog] = Field(..., description="Lista de exercícios")
    duration_minutes: int | None = Field(
        default=None, ge=1, description="Duração em minutos"
    )
    source: str | None = Field(
        default=None, description="Fonte do dado (ex: hevy, manual)"
    )
    external_id: str | None = Field(
        default=None, description="ID externo do treino (ex: Hevy Workout ID)"
    )


def validate_object_id(v: Any) -> str:
    """Valida e converte ObjectId para string."""
    if isinstance(v, ObjectId):
        return str(v)
    return str(v)


class WorkoutWithId(WorkoutLog):
    """Workout log with MongoDB ID for API responses."""

    id: Annotated[str, BeforeValidator(validate_object_id)] = Field(
        ..., validation_alias="_id", description="ID do treino no MongoDB"
    )

    model_config = ConfigDict(populate_by_name=True)


class WorkoutListResponse(BaseModel):
    """Paginated response for workout list API."""

    workouts: list[WorkoutWithId]
    total: int
    page: int
    page_size: int
    total_pages: int
