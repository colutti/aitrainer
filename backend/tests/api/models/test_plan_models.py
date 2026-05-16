from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.api.models.plan import (
    NutritionDailyTargets,
    NutritionStrategy,
    PlanCheckpoint,
    PlanCurrentSummary,
    PlanGoal,
    PlanPromptContext,
    PlanStrategy,
    PlanTimeline,
    PlanUpsertInput,
    TrainingExercise,
    TrainingProgram,
    TrainingRoutine,
    UserPlan,
    UserPlanWithId,
    WeeklyScheduleItem,
)


def test_plan_goal_requires_primary_and_objective_summary():
    goal = PlanGoal(
        primary="build_muscle",
        objective_summary="Ganhar 5kg de massa magra em 12 semanas",
    )
    assert goal.primary == "build_muscle"
    assert goal.success_criteria == []


def test_plan_goal_accepts_success_criteria():
    goal = PlanGoal(
        primary="lose_fat",
        objective_summary="Chegar a 12% BF",
        success_criteria=["peso medio em queda", "circunferencia abdominal reduzindo"],
    )
    assert len(goal.success_criteria) == 2


def test_plan_goal_rejects_empty_primary():
    with pytest.raises(ValidationError):
        PlanGoal(primary="", objective_summary="ok")


def test_plan_timeline_validates_target_after_start():
    start = datetime(2026, 4, 1, tzinfo=timezone.utc)
    target = datetime(2026, 7, 1, tzinfo=timezone.utc)
    timeline = PlanTimeline(
        start_date=start,
        target_date=target,
        review_cadence="quinzenal",
    )
    assert timeline.target_date == target


def test_plan_timeline_rejects_target_before_start():
    start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    target = datetime(2026, 4, 1, tzinfo=timezone.utc)
    with pytest.raises(ValidationError):
        PlanTimeline(
            start_date=start,
            target_date=target,
            review_cadence="quinzenal",
        )


def test_plan_strategy_requires_rationale_and_adaptation():
    strategy = PlanStrategy(
        rationale="Deficit moderado",
        adaptation_policy="ajustar macros por evidencia semanal",
    )
    assert strategy.constraints == []
    assert strategy.preferences == []
    assert strategy.current_risks == []


def test_nutrition_daily_targets_require_positive_ints():
    targets = NutritionDailyTargets(
        calories=2200,
        protein_g=180,
        carbs_g=200,
        fat_g=70,
    )
    assert targets.calories == 2200


def test_nutrition_daily_targets_rejects_zero_calories():
    with pytest.raises(ValidationError):
        NutritionDailyTargets(calories=0, protein_g=100, carbs_g=100, fat_g=50)


def test_nutrition_strategy_requires_daily_targets():
    targets = NutritionDailyTargets(calories=2500, protein_g=160, carbs_g=250, fat_g=80)
    strategy = NutritionStrategy(daily_targets=targets)
    assert strategy.daily_targets.calories == 2500


def test_training_exercise_requires_name_sets_reps_load():
    exercise = TrainingExercise(
        name="Supino Reto",
        sets=4,
        reps="6-8",
        load_guidance="RPE 8",
    )
    assert exercise.name == "Supino Reto"


def test_training_routine_requires_id_name_and_exercises():
    exercises = [
        TrainingExercise(name="Supino Reto", sets=4, reps="6-8", load_guidance="RPE 8"),
    ]
    routine = TrainingRoutine(id="push_a", name="Push A", exercises=exercises)
    assert routine.id == "push_a"
    assert len(routine.exercises) == 1


def test_training_routine_rejects_empty_exercises():
    with pytest.raises(ValidationError):
        TrainingRoutine(id="push_a", name="Push A", exercises=[])


def test_weekly_schedule_item_requires_routine_id_when_training():
    item = WeeklyScheduleItem(day="monday", routine_id="push_a", focus="push", type="training")
    assert item.routine_id == "push_a"


def test_weekly_schedule_item_rejects_training_without_routine_id():
    with pytest.raises(ValidationError):
        WeeklyScheduleItem(day="monday", routine_id=None, focus="push", type="training")


def test_training_program_requires_routines_and_schedule():
    exercises = [TrainingExercise(name="Supino Reto", sets=4, reps="6-8", load_guidance="RPE 8")]
    routines = [TrainingRoutine(id="push_a", name="Push A", exercises=exercises)]
    schedule = [WeeklyScheduleItem(day="monday", routine_id="push_a", focus="push")]
    program = TrainingProgram(
        split_name="push_pull_legs",
        frequency_per_week=1,
        session_duration_min=60,
        routines=routines,
        weekly_schedule=schedule,
    )
    assert program.split_name == "push_pull_legs"


def test_training_program_rejects_unknown_routine_id_in_schedule():
    exercises = [TrainingExercise(name="Supino", sets=3, reps="8-10", load_guidance="RPE 7")]
    routines = [TrainingRoutine(id="push_a", name="Push A", exercises=exercises)]
    schedule = [WeeklyScheduleItem(day="monday", routine_id="pull_a", focus="pull")]
    with pytest.raises(ValidationError):
        TrainingProgram(
            split_name="push_pull_legs",
            frequency_per_week=4,
            session_duration_min=60,
            routines=routines,
            weekly_schedule=schedule,
        )


def test_training_program_rejects_duplicate_training_day_assignments():
    exercises = [TrainingExercise(name="Supino", sets=3, reps="8-10", load_guidance="RPE 7")]
    routines = [TrainingRoutine(id="push_a", name="Push A", exercises=exercises)]
    schedule = [
        WeeklyScheduleItem(day="monday", routine_id="push_a", focus="push"),
        WeeklyScheduleItem(day="monday", routine_id="push_a", focus="push"),
    ]
    with pytest.raises(ValidationError):
        TrainingProgram(
            split_name="push_pull_legs",
            frequency_per_week=1,
            session_duration_min=60,
            routines=routines,
            weekly_schedule=schedule,
        )


def test_training_program_rejects_frequency_mismatch_with_training_days():
    exercises = [TrainingExercise(name="Supino", sets=3, reps="8-10", load_guidance="RPE 7")]
    routines = [TrainingRoutine(id="push_a", name="Push A", exercises=exercises)]
    schedule = [
        WeeklyScheduleItem(day="monday", routine_id="push_a", focus="push"),
        WeeklyScheduleItem(day="wednesday", routine_id="push_a", focus="push"),
    ]
    with pytest.raises(ValidationError):
        TrainingProgram(
            split_name="push_pull_legs",
            frequency_per_week=1,
            session_duration_min=60,
            routines=routines,
            weekly_schedule=schedule,
        )


def test_plan_checkpoint_requires_summary_decision_next_focus():
    checkpoint = PlanCheckpoint(
        summary="Aderencia de 90% na ultima semana",
        decision="Manter estrategia atual",
        next_focus="Progressao de carga no supino",
    )
    assert "90%" in checkpoint.summary


def test_plan_current_summary_requires_active_focus_rationale_next_review():
    summary = PlanCurrentSummary(
        active_focus="consistencia",
        rationale="executar bloco base por 2 semanas",
        next_review="2026-09-15",
    )
    assert summary.active_focus == "consistencia"


def test_plan_upsert_input_requires_all_top_level_fields():
    payload = PlanUpsertInput(
        title="Plano Mestre Recomp",
        goal={"primary": "lose_fat", "objective_summary": "Chegar a 15% BF"},
        timeline={
            "target_date": "2026-09-01T00:00:00",
            "review_cadence": "quinzenal",
        },
        strategy={
            "rationale": "Deficit moderado",
            "adaptation_policy": "ajustar por evidencia",
        },
        nutrition_strategy={
            "daily_targets": {
                "calories": 2200,
                "protein_g": 180,
                "carbs_g": 200,
                "fat_g": 70,
            },
        },
        training_program={
            "split_name": "push_pull_legs",
            "frequency_per_week": 1,
            "session_duration_min": 60,
            "routines": [
                {
                    "id": "push_a",
                    "name": "Push A",
                    "exercises": [
                        {"name": "Supino", "sets": 4, "reps": "6-8", "load_guidance": "RPE 8"},
                    ],
                }
            ],
            "weekly_schedule": [
                {"day": "monday", "routine_id": "push_a", "focus": "push"},
            ],
        },
        current_summary={
            "active_focus": "consistencia",
            "rationale": "executar bloco base",
            "next_review": "2026-09-15",
        },
    )
    assert payload.title == "Plano Mestre Recomp"


def test_user_plan_constructs_full_singleton_payload():
    now = datetime.now(timezone.utc)
    plan = UserPlan(
        user_email="user@test.com",
        title="Plano Mestre",
        goal=PlanGoal(primary="build_muscle", objective_summary="Ganhar massa"),
        timeline=PlanTimeline(
            start_date=now,
            target_date=now,
            review_cadence="semanal",
        ),
        strategy=PlanStrategy(rationale="Superavit", adaptation_policy="ajustar macros"),
        nutrition_strategy=NutritionStrategy(
            daily_targets=NutritionDailyTargets(
                calories=3000, protein_g=180, carbs_g=300, fat_g=90
            ),
        ),
            training_program=TrainingProgram(
                split_name="upper_lower",
                frequency_per_week=1,
            session_duration_min=60,
            routines=[
                TrainingRoutine(
                    id="upper_a",
                    name="Upper A",
                    exercises=[
                        TrainingExercise(
                            name="Supino", sets=4, reps="6-8", load_guidance="RPE 8",
                        ),
                    ],
                ),
            ],
            weekly_schedule=[
                WeeklyScheduleItem(day="monday", routine_id="upper_a", focus="upper"),
            ],
        ),
        current_summary=PlanCurrentSummary(
            active_focus="consistencia",
            rationale="executar bloco base",
            next_review="2026-07-01",
        ),
    )
    assert plan.user_email == "user@test.com"
    assert plan.goal.primary == "build_muscle"
    assert plan.created_at is not None
    assert plan.updated_at is not None


def test_plan_prompt_context_constructs_from_model():
    context = PlanPromptContext(
        title="Plano Mestre",
        goal_primary="lose_fat",
        objective_summary="Chegar a 15% BF",
        timeline_window="2026-04-01 a 2026-09-01",
        review_cadence="quinzenal",
        strategy_rationale="Deficit moderado",
        nutrition_targets={"calories": 2200, "protein_g": 180, "carbs_g": 200, "fat_g": 70},
        training_split="push_pull_legs",
        current_summary={"active_focus": "consistencia"},
        latest_checkpoint={"summary": "aderencia boa"},
    )
    assert context.goal_primary == "lose_fat"
    assert context.weekly_schedule == []
    assert context.routines == []


def test_user_plan_with_id_uses_validation_alias():
    plan = UserPlanWithId(
        _id="abc123",
        user_email="user@test.com",
        title="Plano Mestre",
        goal=PlanGoal(primary="lose_fat", objective_summary="Definir"),
        timeline=PlanTimeline(
            start_date=datetime.now(timezone.utc),
            target_date=datetime.now(timezone.utc),
            review_cadence="semanal",
        ),
        strategy=PlanStrategy(rationale="ok", adaptation_policy="ok"),
        nutrition_strategy=NutritionStrategy(
            daily_targets=NutritionDailyTargets(
                calories=2000, protein_g=150, carbs_g=150, fat_g=60,
            ),
        ),
            training_program=TrainingProgram(
                split_name="full_body",
                frequency_per_week=1,
            session_duration_min=45,
            routines=[
                TrainingRoutine(
                    id="fb_a",
                    name="Full Body A",
                    exercises=[
                        TrainingExercise(
                            name="Agachamento", sets=3, reps="8-10", load_guidance="RPE 7",
                        ),
                    ],
                ),
            ],
            weekly_schedule=[
                WeeklyScheduleItem(day="monday", routine_id="fb_a", focus="full_body"),
            ],
        ),
        current_summary=PlanCurrentSummary(
            active_focus="base",
            rationale="inicio",
            next_review="2026-05-01",
        ),
    )
    assert plan.id == "abc123"
