"""Pydantic models for the singleton master plan domain."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PlanGoal(BaseModel):
    """Goal contract for the active master plan."""

    class MetricTargets(BaseModel):
        """Optional metric targets used by metabolism/projection logic."""

        direction: str | None = None
        target_weight_kg: float | None = Field(default=None, gt=0)
        weekly_weight_change_kg: float | None = Field(default=None, gt=0)
        target_body_fat_pct: float | None = Field(default=None, gt=0, le=100)

    primary: str = Field(..., min_length=1)
    objective_summary: str = Field(..., min_length=1)
    success_criteria: list[str] = Field(default_factory=list)
    metric_targets: MetricTargets | None = None


class PlanTimeline(BaseModel):
    """Explicit timeline for plan execution."""

    start_date: datetime
    target_date: datetime
    review_cadence: str = Field(..., min_length=1)

    @field_validator("target_date")
    @classmethod
    def validate_dates(cls, target_date: datetime, info):
        """Ensure timeline target date is not before start date."""
        start_date = info.data.get("start_date")
        if start_date and target_date < start_date:
            raise ValueError("target_date must be greater than or equal to start_date")
        return target_date


class PlanStrategy(BaseModel):
    """Strategic rationale and constraints."""

    rationale: str = Field(..., min_length=1)
    adaptation_policy: str = Field(..., min_length=1)
    constraints: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    current_risks: list[str] = Field(default_factory=list)


class NutritionDailyTargets(BaseModel):
    """Daily nutrition targets used by the plan."""

    calories: int = Field(..., gt=0)
    protein_g: int = Field(..., gt=0)
    carbs_g: int = Field(..., gt=0)
    fat_g: int = Field(..., gt=0)
    fiber_g: int | None = Field(default=None, gt=0)


class NutritionStrategy(BaseModel):
    """Nutrition strategy block."""

    daily_targets: NutritionDailyTargets
    adherence_notes: list[str] = Field(default_factory=list)


class TrainingExercise(BaseModel):
    """Exercise prescription for one routine."""

    name: str = Field(..., min_length=1)
    sets: int = Field(..., gt=0)
    reps: str = Field(..., min_length=1)
    load_guidance: str = Field(default="RPE 7-8")
    rest_seconds: int | None = Field(default=None, gt=0)
    notes: str | None = None


class TrainingRoutine(BaseModel):
    """Reusable routine definition."""

    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    objective: str | None = None
    exercises: list[TrainingExercise] = Field(..., min_length=1)


class WeeklyScheduleItem(BaseModel):
    """Weekly schedule assignment that references routines."""

    day: str = Field(..., min_length=1)
    routine_id: str | None = None
    focus: str = Field(..., min_length=1)
    type: str = Field(default="training", min_length=1)

    @model_validator(mode="after")
    def validate_training_assignment(self):
        """Training days must point to a concrete routine."""
        if self.type == "training" and not self.routine_id:
            raise ValueError("routine_id is required when type is 'training'")
        return self


class TrainingProgram(BaseModel):
    """Master training program with reusable routines and weekly schedule."""

    split_name: str = Field(..., min_length=1)
    frequency_per_week: int = Field(..., gt=0)
    session_duration_min: int = Field(..., gt=0)
    routines: list[TrainingRoutine] = Field(..., min_length=1)
    weekly_schedule: list[WeeklyScheduleItem] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_schedule_references(self):
        """Every training day must reference an existing routine id."""
        routine_ids = {routine.id for routine in self.routines}
        training_day_keys: set[tuple[str, str]] = set()
        training_days = 0
        for item in self.weekly_schedule:
            if item.type == "training" and item.routine_id not in routine_ids:
                raise ValueError(
                    f"weekly_schedule references unknown routine_id '{item.routine_id}'"
                )
            if item.type == "training":
                training_days += 1
                key = (item.day, item.type)
                if key in training_day_keys:
                    raise ValueError(
                        "weekly_schedule contains duplicate training assignment "
                        f"for day '{item.day}'"
                    )
                training_day_keys.add(key)
        if training_days != self.frequency_per_week:
            raise ValueError(
                "frequency_per_week must match the number of training items in weekly_schedule"
            )
        return self


class PlanCheckpoint(BaseModel):
    """Structured checkpoint record for review history."""

    checkpoint_at: datetime = Field(default_factory=datetime.now)
    summary: str = Field(..., min_length=1)
    evidence: list[str] = Field(default_factory=list)
    decision: str = Field(..., min_length=1)
    next_focus: str = Field(..., min_length=1)


class PlanCurrentSummary(BaseModel):
    """Current operating summary for quick prompt/UI consumption."""

    active_focus: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)
    key_risks: list[str] = Field(default_factory=list)
    last_review: str | None = None
    next_review: str = Field(..., min_length=1)


class PlanUpsertInput(BaseModel):
    """Payload generated by AI to create or update singleton master plan."""

    title: str = Field(
        ..., min_length=1,
        description="Titulo do plano (ex: Plano Mestre Recomp)",
    )
    change_reason: str = Field(
        default="initial_plan", min_length=1,
        description="Motivo: initial_plan, goal_change, quarterly_review",
    )
    goal: dict[str, Any] = Field(
        ...,
        description=(
            "Obrigatorio: 'primary' (lose_fat, build_muscle, recomposition, performance), "
            "'objective_summary' (resumo especifico com criterio de sucesso). "
            "Opcional: 'success_criteria' (lista de criterios mensuraveis)."
        ),
    )
    timeline: dict[str, Any] = Field(
        ...,
        description=(
            "Obrigatorio: 'target_date' (data alvo ISO 8601, ex: 2026-09-01T00:00:00), "
            "'review_cadence' (ex: semanal, quinzenal, mensal). "
            "Opcional: 'start_date' (preenchido automaticamente se omitido)."
        ),
    )
    strategy: dict[str, Any] = Field(
        ...,
        description=(
            "Obrigatorio: 'rationale' (justificativa estrategica), "
            "'adaptation_policy' (como o plano se adapta). "
            "Opcional: 'constraints', 'preferences', 'current_risks' (listas)."
        ),
    )
    nutrition_strategy: dict[str, Any] = Field(
        ...,
        description=(
            "Obrigatorio: 'daily_targets' com 'calories', 'protein_g', 'carbs_g', 'fat_g' "
            "(todos > 0). Chame get_metabolism_data ANTES de definir estes valores. "
            "Opcional: 'adherence_notes' (lista)."
        ),
    )
    training_program: dict[str, Any] = Field(
        ...,
        description=(
            "Obrigatorio: 'split_name', 'frequency_per_week'(>0), 'session_duration_min'(>0), "
            "'routines' (lista de objetos com 'id', 'name' e 'exercises' contendo "
            "'name', 'sets', 'reps', 'load_guidance'), "
            "'weekly_schedule' (lista com 'day', 'routine_id', 'focus', 'type')."
        ),
    )
    current_summary: dict[str, Any] = Field(
        ...,
        description=(
            "Obrigatorio: 'active_focus' (foco atual), 'rationale' (justificativa), "
            "'next_review' (data da proxima revisao ISO 8601). "
            "Opcional: 'key_risks' (lista), 'last_review'."
        ),
    )
    checkpoints: list[PlanCheckpoint] = Field(
        default_factory=list,
        description="Lista de checkpoints de revisao do plano.",
    )


class UserPlan(BaseModel):
    """Full persisted singleton plan payload."""

    id: str | None = Field(default=None)
    user_email: str = Field(..., min_length=3)
    title: str = Field(..., min_length=1)
    goal: PlanGoal
    timeline: PlanTimeline
    strategy: PlanStrategy
    nutrition_strategy: NutritionStrategy
    training_program: TrainingProgram
    checkpoints: list[PlanCheckpoint] = Field(default_factory=list)
    current_summary: PlanCurrentSummary
    change_reason: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class PlanPromptContext(BaseModel):
    """Prompt-safe full snapshot always injected in context."""

    title: str = Field(..., min_length=1)
    goal_primary: str = Field(..., min_length=1)
    objective_summary: str = Field(..., min_length=1)
    timeline_window: str = Field(..., min_length=1)
    review_cadence: str = Field(..., min_length=1)
    strategy_rationale: str = Field(..., min_length=1)
    constraints: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    nutrition_targets: dict[str, Any] = Field(default_factory=dict)
    training_split: str = Field(..., min_length=1)
    weekly_schedule: list[dict[str, Any]] = Field(default_factory=list)
    routines: list[dict[str, Any]] = Field(default_factory=list)
    current_summary: dict[str, Any] = Field(default_factory=dict)
    latest_checkpoint: dict[str, Any] | None = None
    metric_targets: dict[str, Any] = Field(default_factory=dict)


class UserPlanWithId(UserPlan):
    """Active plan with MongoDB id alias."""

    id: str = Field(..., validation_alias="_id")

    model_config = ConfigDict(populate_by_name=True)
