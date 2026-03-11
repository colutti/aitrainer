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
        if v is None:
            return v
        if isinstance(v, dict):
            logger.debug(
                "[normalize_rep_range] rep_range already in dict format: %s", v
            )
            return v  # Already correct format
        if isinstance(v, int):
            # LLM sent: rep_range: 12 → interpret as {"start": 12, "end": 12}
            result = {"start": v, "end": v}
            logger.warning(
                "[normalize_rep_range] Converted int rep_range to dict: %s → %s",
                v,
                result,
            )
            return result
        if isinstance(v, str):
            # LLM sent: rep_range: "8-12" or "8 - 12" or "12"
            if "-" in v:
                parts = v.split("-")
                try:
                    result = {
                        "start": int(parts[0].strip()),
                        "end": int(parts[1].strip()),
                    }
                    logger.warning(
                        "[normalize_rep_range] Converted string rep_range (hyphen) to dict: %s → %s",
                        v,
                        result,
                    )
                    return result
                except (ValueError, IndexError):
                    logger.error(
                        "[normalize_rep_range] Failed to parse string rep_range with hyphen: %s",
                        v,
                    )
                    return None
            # Single number as string: "12"
            try:
                n = int(v.strip())
                result = {"start": n, "end": n}
                logger.warning(
                    "[normalize_rep_range] Converted string rep_range (single) to dict: %s → %s",
                    v,
                    result,
                )
                return result
            except ValueError:
                logger.error(
                    "[normalize_rep_range] Failed to parse string rep_range: %s", v
                )
                return None
        if isinstance(v, (list, tuple)):
            # LLM sent: rep_range: [8, 12] or (8, 12)
            if len(v) >= 2:
                try:
                    result = {"start": int(v[0]), "end": int(v[1])}
                    logger.warning(
                        "[normalize_rep_range] Converted %s rep_range to dict: %s → %s",
                        type(v).__name__,
                        v,
                        result,
                    )
                    return result
                except (ValueError, TypeError):
                    logger.error(
                        "[normalize_rep_range] Failed to parse %s rep_range: %s",
                        type(v).__name__,
                        v,
                    )
                    return None
            # Empty or incomplete list/tuple - return None (invalid)
            logger.debug(
                "[normalize_rep_range] Empty or incomplete %s rep_range, returning None: %s",
                type(v).__name__,
                v,
            )
            return None
        logger.warning(
            "[normalize_rep_range] Unknown type for rep_range (will let Pydantic handle): type=%s, value=%s",
            type(v).__name__,
            v,
        )
        return v  # Let Pydantic handle/reject unknown types


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
