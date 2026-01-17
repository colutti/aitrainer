from typing import List, Optional
from pydantic import BaseModel, Field

class HevyRepRange(BaseModel):
    start: Optional[int] = None
    end: Optional[int] = None

class HevySet(BaseModel):
    type: str = Field(..., description="e.g., normal, warm_up, drop_set, failure")
    weight_kg: Optional[float] = None
    reps: Optional[int] = None
    distance_meters: Optional[float] = None
    duration_seconds: Optional[int] = None
    rep_range: Optional[HevyRepRange] = None

class HevyRoutineExercise(BaseModel):
    exercise_template_id: str
    superset_id: Optional[int] = None
    rest_seconds: Optional[int] = None
    notes: Optional[str] = None
    sets: List[HevySet]

class HevyRoutine(BaseModel):
    id: Optional[str] = None
    title: str
    folder_id: Optional[int] = None
    notes: Optional[str] = None
    exercises: List[HevyRoutineExercise]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class RoutineListResponse(BaseModel):
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
