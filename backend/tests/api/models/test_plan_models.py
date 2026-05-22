from datetime import date, timezone

import pytest
from pydantic import ValidationError

from src.api.models.plan import (
    IntensityPrescription,
    NutritionDailyTargets,
    PlanAlignment,
    PlanCreateInput,
    PlanGoal,
    PlanTimeline,
    PlanTracking,
    PlanUserContext,
    ProgressionRule,
    RepRange,
    SuccessMetric,
    TrainingExercise,
    TrainingRoutine,
    PlanTraining,
    WeeklyScheduleItem,
    ConflictRule,
    ProgressMarker,
    UserPlan,
)


def make_training() -> PlanTraining:
    return PlanTraining(
        split_name="upper_lower",
        frequency_per_week=1,
        session_duration_min=60,
        routines=[
            TrainingRoutine(
                id="upper_a",
                name="Upper A",
                exercises=[
                    TrainingExercise(
                        name="Supino Reto",
                        sets=4,
                        rep_range=RepRange(min_reps=6, max_reps=8),
                        intensity=IntensityPrescription(
                            prescription_type="rpe",
                            target="8",
                        ),
                        progression_rule=ProgressionRule(
                            method="double_progression",
                            increase_when="atingir 8 reps em todas as series",
                            hold_when="ficar entre 6 e 7 reps",
                            deload_when="duas semanas de regressao",
                        ),
                    ),
                ],
            ),
        ],
        weekly_schedule=[
            WeeklyScheduleItem(
                day="monday",
                routine_id="upper_a",
                focus="peito",
                type="training",
            ),
        ],
    )


def make_plan() -> UserPlan:
    return UserPlan(
        user_email="test@example.com",
        title="Plano Mestre",
        goal=PlanGoal(
            primary_goal="muscle_gain",
            outcome_summary="Ganhar massa com superavit controlado",
            success_metrics=[
                SuccessMetric(
                    metric_name="peso",
                    target_value=75,
                    unit="kg",
                    direction="increase",
                    deadline=date(2026, 8, 1),
                )
            ],
        ),
        timeline=PlanTimeline(
            start_date=date(2026, 5, 1),
            target_date=date(2026, 8, 1),
            review_cadence_days=7,
            current_phase="acumulacao",
        ),
        user_context=PlanUserContext(
            training_days_available=["monday", "wednesday", "friday"],
            session_duration_min=60,
            constraints=["nenhuma"],
            preferences=["academia"],
            available_equipment=["barra"],
        ),
        training=make_training(),
        nutrition={
            "daily_targets": NutritionDailyTargets(
                calories_kcal=2600,
                protein_g=160,
                carbs_g=315,
                fat_g=75,
            ),
            "strategy": "superavit leve",
            "adherence_target_pct": 85,
        },
        alignment=PlanAlignment(
            training_nutrition_rationale="Superavit leve para suportar hipertrofia.",
            energy_strategy="surplus",
            recovery_assumptions=["dormir 7h"],
            conflict_rules=[
                ConflictRule(
                    trigger="queda de performance por 2 semanas",
                    action="revisar volume e recuperacao",
                )
            ],
        ),
        tracking=PlanTracking(
            workout_adherence_target_pct=85,
            nutrition_adherence_target_pct=80,
            progress_markers=[
                ProgressMarker(
                    name="carga no supino",
                    source="workouts",
                    target_summary="subir reps ou carga semanalmente",
                )
            ],
            review_questions=["A recuperacao esta coerente com o volume?"],
        ),
    )


def test_plan_goal_requires_structured_success_metrics():
    goal = make_plan().goal
    assert goal.primary_goal == "muscle_gain"
    assert goal.success_metrics[0].metric_name == "peso"


def test_plan_timeline_rejects_target_before_start():
    with pytest.raises(ValidationError):
        PlanTimeline(
            start_date=date(2026, 8, 1),
            target_date=date(2026, 5, 1),
            review_cadence_days=7,
            current_phase="teste",
        )


def test_training_requires_progression_rule():
    with pytest.raises(ValidationError):
        TrainingExercise(
            name="Supino",
            sets=4,
            rep_range=RepRange(min_reps=6, max_reps=8),
            intensity=IntensityPrescription(prescription_type="rpe", target="8"),
        )


def test_weekly_schedule_rejects_unknown_routine():
    with pytest.raises(ValidationError):
        PlanTraining(
            split_name="upper_lower",
            frequency_per_week=1,
            session_duration_min=60,
            routines=[],
            weekly_schedule=[
                WeeklyScheduleItem(
                    day="monday",
                    routine_id="upper_a",
                    focus="peito",
                    type="training",
                )
            ],
        )


def test_plan_create_input_requires_full_typed_contract():
    payload = PlanCreateInput(
        title="Plano Mestre",
        goal=make_plan().goal,
        timeline=make_plan().timeline,
        user_context=make_plan().user_context,
        training=make_training(),
        nutrition=make_plan().nutrition,
        alignment=make_plan().alignment,
        tracking=make_plan().tracking,
    )
    assert payload.training.split_name == "upper_lower"


def test_user_plan_defaults_to_plan_v2():
    plan = make_plan()
    assert plan.schema_version == "plan_v2"
    assert plan.plan_status == "active"
    assert plan.created_at.tzinfo == timezone.utc
