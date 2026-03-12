"""
This module contains the models for Hevy routines and exercise templates.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from src.core.logs import logger


class HevyRepRange(BaseModel):
    """Range of repetitions for a set."""

    model_config = ConfigDict(extra="ignore")
    start: Optional[int] = None
    end: Optional[int] = None


class HevySet(BaseModel):
    """A single set within an exercise."""

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
        """Normalizes the set type string."""
        if isinstance(v, str):
            original = v
            v = v.lower().strip()
            if v == "warm_up":
                logger.debug(
                    "[normalize_type] Converted warm_up → warmup"
                )
                return "warmup"
            if v == "drop_set":
                logger.debug(
                    "[normalize_type] Converted drop_set → dropset"
                )
                return "dropset"
            if original != v:
                logger.debug(
                    "[normalize_type] Normalized type: %s → %s",
                    original,
                    v,
                )
        return v

    @field_validator("rep_range", mode="before")
    @classmethod
    def normalize_rep_range(cls, v):
        """
        Coerce common LLM mistakes for rep_range into HevyRepRange-compatible dict.
        Hevy API REQUIRES rep_range as {"start": int, "end": int}, never as int.
        """
        if v is None or isinstance(v, dict):
            return v

        res = None
        if isinstance(v, int):
            res = {"start": v, "end": v}
        elif isinstance(v, str):
            res = cls._parse_rep_range_str(v)
        elif isinstance(v, (list, tuple)) and len(v) >= 2:
            try:
                res = {"start": int(v[0]), "end": int(v[1])}
            except (ValueError, TypeError):
                logger.error("[normalize_rep_range] Failed to parse %s: %s", type(v).__name__, v)

        if res:
            logger.debug("[normalize_rep_range] Converted %s to dict: %s", type(v).__name__, res)
            return res

        logger.warning(
            "[normalize_rep_range] Unknown/Invalid type (Pydantic will handle): %s, %s",
            type(v).__name__, v
        )
        return None

    @staticmethod
    def _parse_rep_range_str(v: str) -> Optional[dict]:
        """Helper to parse rep range string."""
        try:
            if "-" in v:
                parts = v.split("-")
                return {"start": int(parts[0].strip()), "end": int(parts[1].strip())}
            n = int(v.strip())
            return {"start": n, "end": n}
        except (ValueError, IndexError):
            logger.error("[normalize_rep_range] Failed to parse string: %s", v)
            return None


class HevyRoutineExercise(BaseModel):
    """An exercise entry within a Hevy routine."""

    model_config = ConfigDict(extra="ignore")
    exercise_template_id: str
    superset_id: Optional[int] = None
    rest_seconds: Optional[int] = None
    notes: Optional[str] = None
    sets: List[HevySet] = []
    title: Optional[str] = None  # Returned by Hevy in GET responses


class HevyRoutine(BaseModel):
    """A complete Hevy workout routine."""

    model_config = ConfigDict(extra="ignore")
    id: Optional[str] = None
    title: str
    folder_id: Optional[int] = None
    notes: Optional[str] = None
    exercises: List[HevyRoutineExercise] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RoutineListResponse(BaseModel):
    """Paginated list of Hevy routines."""

    model_config = ConfigDict(extra="ignore")
    page: int
    page_count: int
    routines: List[HevyRoutine]


class HevyExerciseTemplate(BaseModel):
    """Template for a specific exercise in Hevy."""

    id: str
    title: str
    type: str
    primary_muscle_group: Optional[str] = None
    secondary_muscle_groups: List[str] = []
    is_custom: bool = False


class ExerciseTemplateListResponse(BaseModel):
    """Paginated list of Hevy exercise templates."""

    page: int
    page_count: int
    exercise_templates: List[HevyExerciseTemplate]
