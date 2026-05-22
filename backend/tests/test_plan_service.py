from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.api.models.plan import (
    ConflictRule,
    ExternalRoutineBinding,
    IntensityPrescription,
    NutritionDailyTargets,
    PlanAlignment,
    PlanCreateInput,
    PlanDiscoveryUpdateInput,
    PlanGoal,
    PlanReviewInput,
    PlanSectionUpdateInput,
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
    apply_discovery_update,
    build_plan_from_create_input,
    build_plan_prompt_snapshot,
    build_plan_view_model,
    build_progress_snapshot,
    build_review_record,
    format_plan_snapshot,
    merge_plan_section,
    missing_discovery_fields,
)
from src.api.models.routine import HevyRoutine, HevyRoutineExercise
from src.services.plan_hevy_sync import HevySyncError, sync_training_with_hevy_if_needed


def make_create_input() -> PlanCreateInput:
    return PlanCreateInput(
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
        training=PlanTraining(
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
                                increase_when="bater o topo da faixa",
                                hold_when="ficar no meio da faixa",
                                deload_when="regredir por 2 semanas",
                            ),
                        ),
                    ],
                )
            ],
            weekly_schedule=[
                WeeklyScheduleItem(
                    day="monday",
                    routine_id="upper_a",
                    focus="peito",
                    type="training",
                )
            ],
        ),
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
            training_nutrition_rationale="Superavit leve para hipertrofia.",
            energy_strategy="surplus",
            recovery_assumptions=["dormir 7h"],
            conflict_rules=[
                ConflictRule(
                    trigger="queda de performance",
                    action="revisar recuperacao",
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
                    target_summary="subir carga ou reps",
                )
            ],
            review_questions=["A recuperacao esta coerente?"],
        ),
    )


def test_discovery_update_tracks_missing_fields():
    discovery = apply_discovery_update(
        "user@test.com",
        None,
        PlanDiscoveryUpdateInput(goal_primary="muscle_gain", goal_summary="Ganhar massa"),
    )

    assert "target_date" in discovery.missing_fields
    assert "goal_primary" not in discovery.missing_fields


def test_build_plan_from_create_input_sets_active_contract():
    plan = build_plan_from_create_input("user@test.com", make_create_input())

    assert plan.schema_version == "plan_v2"
    assert plan.training.split_name == "upper_lower"


def test_merge_plan_section_updates_typed_section():
    plan = build_plan_from_create_input("user@test.com", make_create_input())
    updated = merge_plan_section(
        plan,
        PlanSectionUpdateInput(
            section="nutrition",
            nutrition={
                "daily_targets": {
                    "calories_kcal": 2800,
                    "protein_g": 160,
                    "carbs_g": 340,
                    "fat_g": 80,
                },
                "strategy": "superavit moderado",
                "adherence_target_pct": 85,
            },
        ),
    )

    assert updated.nutrition.daily_targets.calories_kcal == 2800


def test_build_plan_prompt_snapshot_handles_no_plan():
    snapshot = build_plan_prompt_snapshot(None, None, None)
    text = format_plan_snapshot(snapshot)

    assert snapshot.status == "NO_PLAN"
    assert "START_OR_CONTINUE_DISCOVERY" in text


def test_build_progress_snapshot_marks_missing_execution_data():
    plan = build_plan_from_create_input("user@test.com", make_create_input())
    database = MagicMock()
    database.get_workout_logs.return_value = []
    database.get_nutrition_stats.return_value = MagicMock(total_logs=0)
    database.get_weight_logs.return_value = []

    progress = build_progress_snapshot(plan, database)

    assert progress.training_adherence.status == "insufficient_data"
    assert progress.nutrition_adherence.status == "insufficient_data"


def test_build_plan_view_model_returns_discovery_view():
    discovery = apply_discovery_update(
        "user@test.com",
        None,
        PlanDiscoveryUpdateInput(goal_primary="muscle_gain"),
    )

    view = build_plan_view_model(None, discovery, None)

    assert view.status == "DISCOVERY_IN_PROGRESS"
    assert view.discovery is not None


def test_build_plan_view_model_includes_weekly_schedule_for_active_plan():
    plan = build_plan_from_create_input("user@test.com", make_create_input())
    view = build_plan_view_model(plan, None, None)

    assert view.status == "ACTIVE_PLAN"
    assert view.active_plan is not None
    assert len(view.active_plan.weekly_schedule) == 7
    assert any(item.is_today for item in view.active_plan.weekly_schedule)
    assert {item.day for item in view.active_plan.weekly_schedule} == {
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    }
    assert view.active_plan.weekly_schedule[0].exercise_names == ["Supino Reto"]


def test_build_review_record_preserves_evidence():
    review = build_review_record(
        PlanReviewInput(
            summary="Aderencia forte",
            decision="manter estrategia",
            evidence_summary=["3 treinos completos"],
        )
    )

    assert review.evidence_summary == ["3 treinos completos"]


def test_missing_discovery_fields_when_all_data_absent():
    assert "goal_primary" in missing_discovery_fields(None)


def test_sync_training_with_hevy_updates_bound_routine_and_enriches_exercise_ids(monkeypatch):
    current_plan = build_plan_from_create_input("user@test.com", make_create_input())
    base_routine = current_plan.training.routines[0]
    bound_routine = base_routine.model_copy(
        update={
            "external_bindings": [
                ExternalRoutineBinding(
                    provider="hevy",
                    external_routine_id="hevy_routine_1",
                    external_routine_name="Upper A",
                )
            ]
        }
    )
    current_plan = current_plan.model_copy(
        update={
            "training": current_plan.training.model_copy(update={"routines": [bound_routine]})
        }
    )
    updated_plan = current_plan.model_copy(
        update={
            "training": current_plan.training.model_copy(
                update={
                    "routines": [
                        bound_routine.model_copy(
                            update={
                                "exercises": [
                                    bound_routine.exercises[0].model_copy(
                                        update={"rest_seconds": 120}
                                    )
                                ]
                            }
                        )
                    ]
                }
            )
        }
    )

    database = MagicMock()
    database.get_user_profile.return_value = MagicMock(
        hevy_enabled=True,
        hevy_api_key="key",
    )
    database.workouts_repo = MagicMock()

    current_hevy_routine = HevyRoutine(
        id="hevy_routine_1",
        title="Upper A",
        exercises=[
            HevyRoutineExercise(
                exercise_template_id="tpl_supino",
                title="Supino Reto",
                sets=[],
            )
        ],
    )
    synced_hevy_routine = HevyRoutine(
        id="hevy_routine_1",
        title="Upper A",
        exercises=current_hevy_routine.exercises,
    )

    hevy_service = MagicMock()
    hevy_service.get_routine_by_id = AsyncMock(return_value=current_hevy_routine)
    hevy_service.update_routine = AsyncMock(return_value=synced_hevy_routine)
    monkeypatch.setattr(
        "src.services.plan_hevy_sync.HevyService",
        MagicMock(return_value=hevy_service),
    )

    synced_plan = sync_training_with_hevy_if_needed(
        database=database,
        user_email="user@test.com",
        current_plan=current_plan,
        updated_plan=updated_plan,
    )

    synced_exercise = synced_plan.training.routines[0].exercises[0]
    assert synced_exercise.external_exercise_template_id == "tpl_supino"
    assert (
        synced_plan.training.routines[0].external_bindings[0].external_routine_name
        == "Upper A"
    )


def test_sync_training_with_hevy_raises_when_bound_routine_removed():
    current_plan = build_plan_from_create_input("user@test.com", make_create_input())
    base_routine = current_plan.training.routines[0]
    bound_routine = base_routine.model_copy(
        update={
            "external_bindings": [
                ExternalRoutineBinding(
                    provider="hevy",
                    external_routine_id="hevy_routine_1",
                )
            ]
        }
    )
    current_plan = current_plan.model_copy(
        update={
            "training": current_plan.training.model_copy(update={"routines": [bound_routine]})
        }
    )
    updated_plan = current_plan.model_copy(
        update={
            "training": current_plan.training.model_copy(
                update={
                    "routines": []
                }
            )
        }
    )

    database = MagicMock()
    database.get_user_profile.return_value = MagicMock(
        hevy_enabled=True,
        hevy_api_key="key",
    )
    database.workouts_repo = MagicMock()

    with pytest.raises(HevySyncError):
        sync_training_with_hevy_if_needed(
            database=database,
            user_email="user@test.com",
            current_plan=current_plan,
            updated_plan=updated_plan,
        )
