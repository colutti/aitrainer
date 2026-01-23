from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class HevyRepRange(BaseModel):
    model_config = ConfigDict(extra="ignore")
    start: Optional[int] = None
    end: Optional[int] = None


class HevySet(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: str = Field(..., description="e.g., normal, warmup, dropset, failure")
    weight_kg: Optional[float] = None
    reps: Optional[int] = None
    distance_meters: Optional[float] = None
    duration_seconds: Optional[int] = None
    rep_range: Optional[HevyRepRange] = None

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.lower().strip()
            if v == "warm_up":
                return "warmup"
            if v == "drop_set":
                return "dropset"
        return v


class HevyRoutineExercise(BaseModel):
    model_config = ConfigDict(extra="ignore")
    exercise_template_id: str
    superset_id: Optional[int] = None
    rest_seconds: Optional[int] = None
    notes: Optional[str] = None
    sets: List[HevySet]
    title: Optional[str] = None  # Returned by Hevy in GET responses


class HevyRoutine(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: Optional[str] = None
    title: str
    folder_id: Optional[int] = None
    notes: Optional[str] = None
    exercises: List[HevyRoutineExercise]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RoutineListResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    page: int
    page_count: int
    routines: List[HevyRoutine]


class HevyExerciseTemplate(BaseModel):
    id: str
    title: str
    type: str
    primary_muscle_group: Optional[str] = None
    secondary_muscle_groups: List[str] = []
    is_custom: bool = False


class ExerciseTemplateListResponse(BaseModel):
    page: int
    page_count: int
    exercise_templates: List[HevyExerciseTemplate]
