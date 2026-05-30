"""Pydantic models for the plan V2 domain."""

from datetime import date, datetime, timezone
from typing import Annotated, Any, Literal

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, BeforeValidator, model_validator


CANONICAL_WEEKDAYS = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)

CANONICAL_PLAN_SECTIONS = (
    "goal",
    "timeline",
    "user_context",
    "training",
    "nutrition",
    "alignment",
    "tracking",
)

Weekday = Literal[
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

PrimaryGoal = Literal[
    "fat_loss",
    "muscle_gain",
    "recomposition",
    "performance",
    "health",
]

PlanLifecycleStatus = Literal[
    "NO_PLAN",
    "DISCOVERY_IN_PROGRESS",
    "ACTIVE_PLAN",
]

PlanSectionName = Literal[
    "goal",
    "timeline",
    "user_context",
    "training",
    "nutrition",
    "alignment",
    "tracking",
]


def validate_object_id(value: Any) -> str:
    """Convert ObjectId-like values into strings for API responses."""
    if isinstance(value, ObjectId):
        return str(value)
    return str(value)


class SuccessMetric(BaseModel):
    """Structured success metric for the active plan."""

    metric_name: str = Field(..., min_length=1)
    target_value: float | int | str
    unit: str = Field(..., min_length=1)
    direction: Literal["increase", "decrease", "maintain", "complete"]
    deadline: date | None = None


class PlanGoal(BaseModel):
    """High-level user goal and how success is measured."""

    primary_goal: PrimaryGoal
    outcome_summary: str = Field(..., min_length=1)
    success_metrics: list[SuccessMetric] = Field(..., min_length=1)


class PlanTimeline(BaseModel):
    """Plan execution window and review cadence."""

    start_date: date
    target_date: date
    review_cadence_days: int = Field(..., gt=0)
    current_phase: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_date_order(self):
        """Target date cannot be before the plan start date."""
        if self.target_date < self.start_date:
            raise ValueError("target_date must be greater than or equal to start_date")
        return self


class PlanUserContext(BaseModel):
    """Known constraints and preferences needed for personalization."""

    training_days_available: list[Weekday] = Field(..., min_length=1)
    session_duration_min: int = Field(..., gt=0)
    constraints: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    available_equipment: list[str] = Field(default_factory=list)
    training_level: Literal["beginner", "intermediate", "advanced", "unknown"] = (
        "unknown"
    )
    nutrition_preferences: list[str] = Field(default_factory=list)


class RepRange(BaseModel):
    """Prescription for a repetition range."""

    min_reps: int = Field(..., gt=0)
    max_reps: int = Field(..., gt=0)

    @model_validator(mode="after")
    def validate_range(self):
        """The max value cannot be smaller than the min value."""
        if self.max_reps < self.min_reps:
            raise ValueError("max_reps must be greater than or equal to min_reps")
        return self


class IntensityPrescription(BaseModel):
    """How hard the set should feel or be loaded."""

    prescription_type: Literal["rpe", "rir", "percent_1rm", "guidance"]
    target: str = Field(..., min_length=1)


class ProgressionRule(BaseModel):
    """Rule the AI must follow when progressing the exercise."""

    method: Literal[
        "double_progression",
        "linear_load",
        "volume_progression",
        "maintenance",
    ]
    increase_when: str = Field(..., min_length=1)
    hold_when: str = Field(..., min_length=1)
    deload_when: str = Field(..., min_length=1)


class ExternalRoutineBinding(BaseModel):
    """External provider binding for a plan routine."""

    provider: Literal["hevy"]
    external_routine_id: str = Field(..., min_length=1)
    external_routine_name: str | None = None
    last_synced_at: datetime | None = None
    last_sync_error: str | None = None


class TrainingExercise(BaseModel):
    """Exercise prescription inside a routine."""

    name: str = Field(..., min_length=1)
    external_exercise_template_id: str | None = None
    sets: int = Field(..., gt=0)
    rep_range: RepRange
    intensity: IntensityPrescription
    rest_seconds: int | None = Field(default=None, gt=0)
    progression_rule: ProgressionRule
    notes: str | None = None


class TrainingRoutine(BaseModel):
    """Reusable training routine."""

    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    objective: str | None = None
    exercises: list[TrainingExercise] = Field(..., min_length=1)
    external_bindings: list[ExternalRoutineBinding] = Field(default_factory=list)


class WeeklyScheduleItem(BaseModel):
    """Weekly training assignment."""

    day: Weekday
    routine_id: str | None = None
    focus: str = Field(..., min_length=1)
    type: Literal["training", "off"] = "training"

    @model_validator(mode="after")
    def validate_training_item(self):
        """Training rows must reference a routine and off rows must not."""
        if self.type == "training" and not self.routine_id:
            raise ValueError("routine_id is required when type is 'training'")
        if self.type == "off" and self.routine_id is not None:
            raise ValueError("routine_id must be null when type is 'off'")
        return self


class PlanTraining(BaseModel):
    """Structured training prescription."""

    split_name: str = Field(..., min_length=1)
    frequency_per_week: int = Field(..., gt=0)
    session_duration_min: int = Field(..., gt=0)
    routines: list[TrainingRoutine] = Field(..., min_length=1)
    weekly_schedule: list[WeeklyScheduleItem] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_training_program(self):
        """Validate references and schedule coherence."""
        routine_ids = {routine.id for routine in self.routines}
        scheduled_training_days = 0
        seen_days: set[str] = set()

        for item in self.weekly_schedule:
            if item.day in seen_days:
                raise ValueError(
                    f"weekly_schedule contains duplicate assignment for day '{item.day}'"
                )
            seen_days.add(item.day)

            if item.type == "training":
                scheduled_training_days += 1
                if item.routine_id not in routine_ids:
                    raise ValueError(
                        f"weekly_schedule references unknown routine_id '{item.routine_id}'"
                    )

        if scheduled_training_days != self.frequency_per_week:
            raise ValueError(
                "frequency_per_week must match the number of training items in weekly_schedule"
            )
        return self


class NutritionDailyTargets(BaseModel):
    """Daily calories and macro targets."""

    calories_kcal: int = Field(..., gt=0)
    protein_g: int = Field(..., gt=0)
    carbs_g: int = Field(..., gt=0)
    fat_g: int = Field(..., gt=0)
    fiber_g: int | None = Field(default=None, gt=0)


class PlanNutrition(BaseModel):
    """Structured nutrition strategy for the plan."""

    daily_targets: NutritionDailyTargets
    strategy: str = Field(..., min_length=1)
    adherence_target_pct: int = Field(..., ge=0, le=100)


class ConflictRule(BaseModel):
    """A situation that should block or force a plan adjustment."""

    trigger: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)


class PlanAlignment(BaseModel):
    """How training, nutrition and recovery fit the user's goal."""

    training_nutrition_rationale: str = Field(..., min_length=1)
    energy_strategy: Literal["deficit", "maintenance", "surplus", "recomposition"]
    recovery_assumptions: list[str] = Field(default_factory=list)
    conflict_rules: list[ConflictRule] = Field(..., min_length=1)


class ProgressMarker(BaseModel):
    """Signal the AI should monitor over time."""

    name: str = Field(..., min_length=1)
    source: Literal["workouts", "nutrition", "body", "metabolism", "manual"]
    target_summary: str = Field(..., min_length=1)


class PlanTracking(BaseModel):
    """Tracking targets and review prompts used by the AI."""

    workout_adherence_target_pct: int = Field(..., ge=0, le=100)
    nutrition_adherence_target_pct: int = Field(..., ge=0, le=100)
    progress_markers: list[ProgressMarker] = Field(..., min_length=1)
    review_questions: list[str] = Field(..., min_length=1)


class PlanReview(BaseModel):
    """Evidence-backed review of the active plan."""

    reviewed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    summary: str = Field(..., min_length=1)
    decision: str = Field(..., min_length=1)
    changes_made: list[str] = Field(default_factory=list)
    next_review_at: date | None = None
    evidence_summary: list[str] = Field(default_factory=list)


class UserPlan(BaseModel):
    """Persisted plan contract used across prompt, UI and tools."""

    id: str | None = None
    schema_version: Literal["plan_v2"] = "plan_v2"
    plan_status: Literal["active"] = "active"
    user_email: str = Field(..., min_length=3)
    title: str = Field(..., min_length=1)
    goal: PlanGoal
    timeline: PlanTimeline
    user_context: PlanUserContext
    training: PlanTraining
    nutrition: PlanNutrition
    alignment: PlanAlignment
    tracking: PlanTracking
    latest_review: PlanReview | None = None
    review_history: list[PlanReview] = Field(default_factory=list)
    created_from: Literal["discovery", "migration", "admin"] = "discovery"
    last_material_change_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    review_reason: str | None = None
    data_confidence: Literal["low", "medium", "high"] = "medium"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PlanDiscoveryState(BaseModel):
    """Persisted discovery draft while the user still has no active plan."""

    id: str | None = None
    user_email: str = Field(..., min_length=3)
    goal_primary: PrimaryGoal | None = None
    goal_summary: str | None = None
    target_date: date | None = None
    training_days_available: list[Weekday] = Field(default_factory=list)
    session_duration_min: int | None = Field(default=None, gt=0)
    constraints: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    available_equipment: list[str] = Field(default_factory=list)
    training_level: Literal["beginner", "intermediate", "advanced", "unknown"] = (
        "unknown"
    )
    nutrition_preferences: list[str] = Field(default_factory=list)
    metabolism_confirmed: bool = False
    missing_fields: list[str] = Field(default_factory=list)
    confidence: dict[str, Literal["user_provided", "system_inferred", "missing"]] = (
        Field(default_factory=dict)
    )
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PlanCreateInput(BaseModel):
    """Payload to create a new active plan."""

    title: str = Field(..., min_length=1)
    goal: PlanGoal
    timeline: PlanTimeline
    user_context: PlanUserContext
    training: PlanTraining
    nutrition: PlanNutrition
    alignment: PlanAlignment
    tracking: PlanTracking
    review_reason: str | None = None
    data_confidence: Literal["low", "medium", "high"] = "medium"


class PlanDiscoveryUpdateInput(BaseModel):
    """Partial update for discovery state."""

    goal_primary: PrimaryGoal | None = None
    goal_summary: str | None = None
    target_date: date | None = None
    training_days_available: list[Weekday] | None = None
    session_duration_min: int | None = Field(default=None, gt=0)
    constraints: list[str] | None = None
    preferences: list[str] | None = None
    available_equipment: list[str] | None = None
    training_level: Literal["beginner", "intermediate", "advanced", "unknown"] | None = (
        None
    )
    nutrition_preferences: list[str] | None = None
    metabolism_confirmed: bool | None = None


class PlanSectionUpdateInput(BaseModel):
    """Typed section update for the active plan."""

    section: PlanSectionName
    goal: PlanGoal | None = None
    timeline: PlanTimeline | None = None
    user_context: PlanUserContext | None = None
    training: PlanTraining | None = None
    nutrition: PlanNutrition | None = None
    alignment: PlanAlignment | None = None
    tracking: PlanTracking | None = None
    review_reason: str | None = None

    @model_validator(mode="after")
    def validate_section_payload(self):
        """At least one payload must be present and include the section name."""
        payloads = {
            "goal": self.goal,
            "timeline": self.timeline,
            "user_context": self.user_context,
            "training": self.training,
            "nutrition": self.nutrition,
            "alignment": self.alignment,
            "tracking": self.tracking,
        }
        provided = [name for name, value in payloads.items() if value is not None]
        if not provided or self.section not in provided:
            raise ValueError(
                "section must match at least one provided payload in the same request"
            )
        return self


class PlanReviewInput(BaseModel):
    """Tool/API payload to register a plan review."""

    summary: str = Field(..., min_length=1)
    decision: str = Field(..., min_length=1)
    changes_made: list[str] = Field(default_factory=list)
    next_review_at: date | None = None
    evidence_summary: list[str] = Field(default_factory=list)


class ProgressMetric(BaseModel):
    """One computed progress dimension."""

    status: Literal["on_track", "off_track", "insufficient_data"]
    details: str = Field(..., min_length=1)


class PlanConflict(BaseModel):
    """Detected conflict between the plan and current data."""

    kind: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class PlanProgressSnapshot(BaseModel):
    """Computed progress summary shown to the user and the AI."""

    plan_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    training_adherence: ProgressMetric
    nutrition_adherence: ProgressMetric
    progression_status: Literal[
        "progressing",
        "maintaining",
        "stalled",
        "regressing",
        "insufficient_data",
    ]
    body_trend_status: Literal["aligned", "misaligned", "insufficient_data"]
    conflicts: list[PlanConflict] = Field(default_factory=list)
    recommended_review: bool = False
    evidence_summary: list[str] = Field(default_factory=list)


class PlanPromptContext(BaseModel):
    """Prompt-safe structured context injected into the chat runtime."""

    status: PlanLifecycleStatus
    schema_version: str | None = None
    active_plan: dict[str, Any] = Field(default_factory=dict)
    discovery: dict[str, Any] = Field(default_factory=dict)
    progress_summary: dict[str, Any] = Field(default_factory=dict)


class DiscoveryView(BaseModel):
    """Frontend-friendly discovery summary."""

    missing_fields: list[str] = Field(default_factory=list)
    collected_fields: list[str] = Field(default_factory=list)
    next_prompt: str = Field(..., min_length=1)


class TodayTrainingView(BaseModel):
    """Frontend summary of the current day's training."""

    day: Weekday
    routine_name: str | None = None
    focus: str = Field(..., min_length=1)
    exercise_names: list[str] = Field(default_factory=list)
    is_rest_day: bool = False


class WeeklyScheduleView(BaseModel):
    """Frontend summary of one scheduled training day."""

    day: Weekday
    routine_name: str | None = None
    focus: str = Field(..., min_length=1)
    exercise_names: list[str] = Field(default_factory=list)
    is_rest_day: bool = False
    is_today: bool = False


class ActivePlanView(BaseModel):
    """Frontend view model for the active plan."""

    title: str = Field(..., min_length=1)
    goal_summary: str = Field(..., min_length=1)
    success_metrics: list[str] = Field(default_factory=list)
    training_split: str = Field(..., min_length=1)
    weekly_schedule: list[WeeklyScheduleView] = Field(default_factory=list)
    today_training: TodayTrainingView
    nutrition_targets: NutritionDailyTargets
    current_risks: list[str] = Field(default_factory=list)
    next_review_at: date | None = None
    latest_review_summary: str | None = None


class PlanViewModel(BaseModel):
    """Complete view model consumed by the plan tab."""

    status: PlanLifecycleStatus
    generic_response_notice: str = Field(..., min_length=1)
    discovery: DiscoveryView | None = None
    active_plan: ActivePlanView | None = None
    progress: PlanProgressSnapshot | None = None


class UserPlanWithId(UserPlan):
    """Active plan with MongoDB id alias."""

    id: Annotated[str, BeforeValidator(validate_object_id)] = Field(
        ..., validation_alias="_id"
    )

    model_config = ConfigDict(populate_by_name=True)


class PlanDiscoveryStateWithId(PlanDiscoveryState):
    """Discovery draft with MongoDB id alias."""

    id: Annotated[str, BeforeValidator(validate_object_id)] = Field(
        ..., validation_alias="_id"
    )

    model_config = ConfigDict(populate_by_name=True)
