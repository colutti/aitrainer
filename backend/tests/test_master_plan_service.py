from datetime import date

from src.api.models.plan import (
    ConflictRule,
    IntensityPrescription,
    NutritionDailyTargets,
    PlanAlignment,
    PlanCreateInput,
    PlanGoal,
    PlanNutrition,
    PlanTimeline,
    PlanTracking,
    PlanUserContext,
    ProgressMarker,
    ProgressionRule,
    RepRange,
    SuccessMetric,
    TrainingExercise,
    PlanTraining,
    TrainingRoutine,
    WeeklyScheduleItem,
)
from src.services.plan_service import (
    build_plan_from_create_input,
    build_plan_prompt_snapshot,
    format_plan_snapshot,
)


def make_payload() -> PlanCreateInput:
    return PlanCreateInput(
        title="Plano Mestre Teste",
        goal=PlanGoal(
            primary_goal="fat_loss",
            outcome_summary="Chegar a 15% de gordura corporal",
            success_metrics=[
                SuccessMetric(
                    metric_name="body_fat_pct",
                    target_value=15,
                    unit="%",
                    direction="decrease",
                    deadline=date(2026, 9, 1),
                )
            ],
        ),
        timeline=PlanTimeline(
            start_date=date(2026, 4, 23),
            target_date=date(2026, 9, 1),
            review_cadence_days=14,
            current_phase="deficit",
        ),
        user_context=PlanUserContext(
            training_days_available=["monday"],
            session_duration_min=60,
            constraints=["dor no ombro"],
            preferences=["treino matinal"],
            available_equipment=["barra"],
        ),
        training=PlanTraining(
            split_name="push_pull_legs",
            frequency_per_week=1,
            session_duration_min=60,
            routines=[
                TrainingRoutine(
                    id="push_a",
                    name="Push A",
                    exercises=[
                        TrainingExercise(
                            name="Supino Reto",
                            sets=4,
                            rep_range=RepRange(min_reps=6, max_reps=8),
                            intensity=IntensityPrescription(prescription_type="rpe", target="8"),
                            progression_rule=ProgressionRule(
                                method="double_progression",
                                increase_when="bater topo da faixa",
                                hold_when="meio da faixa",
                                deload_when="regredir por 2 semanas",
                            ),
                        )
                    ],
                )
            ],
            weekly_schedule=[
                WeeklyScheduleItem(day="monday", routine_id="push_a", focus="push", type="training")
            ],
        ),
        nutrition=PlanNutrition(
            daily_targets=NutritionDailyTargets(
                calories_kcal=2200,
                protein_g=180,
                carbs_g=200,
                fat_g=70,
            ),
            strategy="deficit moderado",
            adherence_target_pct=80,
        ),
        alignment=PlanAlignment(
            training_nutrition_rationale="Deficit moderado e progressao de forca",
            energy_strategy="deficit",
            recovery_assumptions=["sono regular"],
            conflict_rules=[ConflictRule(trigger="fadiga alta", action="revisar volume")],
        ),
        tracking=PlanTracking(
            workout_adherence_target_pct=80,
            nutrition_adherence_target_pct=80,
            progress_markers=[ProgressMarker(name="aderencia", source="manual", target_summary="80%+")],
            review_questions=["A recuperacao esta adequada?"],
        ),
    )


def test_build_plan_from_create_input_builds_master_plan_structure():
    plan = build_plan_from_create_input("user@test.com", make_payload())

    assert plan.goal.primary_goal == "fat_loss"
    assert plan.timeline.review_cadence_days == 14
    assert plan.nutrition.daily_targets.protein_g == 180
    assert plan.training.routines[0].name == "Push A"


def test_plan_snapshot_contains_full_master_context():
    plan = build_plan_from_create_input("user@test.com", make_payload())
    snapshot = build_plan_prompt_snapshot(plan)
    text = format_plan_snapshot(snapshot)

    assert snapshot.status == "ACTIVE_PLAN"
    assert snapshot.active_plan["goal"]["primary_goal"] == "fat_loss"
    assert snapshot.active_plan["training"]["split_name"] == "push_pull_legs"
    assert "PLAN_CONTEXT" in text
    assert "ACTIVE_PLAN" in text
