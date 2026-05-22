import json
from datetime import date
from unittest.mock import MagicMock

from src.api.models.plan import (
    ConflictRule,
    ExternalRoutineBinding,
    IntensityPrescription,
    NutritionDailyTargets,
    PlanAlignment,
    PlanCreateInput,
    PlanDiscoveryState,
    PlanGoal,
    PlanNutrition,
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
from src.services.plan_service import build_plan_from_create_input
from src.services.plan_tools import (
    create_create_plan_from_discovery_tool,
    create_get_plan_status_tool,
    create_record_plan_review_tool,
    create_update_plan_discovery_tool,
    create_update_plan_section_tool,
)


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
            available_equipment=["barra", "halteres"],
        ),
        training=PlanTraining(
            split_name="upper_lower",
            frequency_per_week=2,
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
                                increase_when="bater topo da faixa",
                                hold_when="ficar no meio da faixa",
                                deload_when="regredir por 2 semanas",
                            ),
                        )
                    ],
                ),
                TrainingRoutine(
                    id="lower_a",
                    name="Lower A",
                    exercises=[
                        TrainingExercise(
                            name="Agachamento",
                            sets=4,
                            rep_range=RepRange(min_reps=5, max_reps=8),
                            intensity=IntensityPrescription(
                                prescription_type="rpe",
                                target="8",
                            ),
                            progression_rule=ProgressionRule(
                                method="linear_load",
                                increase_when="completar volume com tecnica boa",
                                hold_when="tecnica instavel",
                                deload_when="fadiga acumulada por 2 semanas",
                            ),
                        )
                    ],
                ),
            ],
            weekly_schedule=[
                WeeklyScheduleItem(
                    day="monday",
                    routine_id="upper_a",
                    focus="upper",
                    type="training",
                ),
                WeeklyScheduleItem(
                    day="thursday",
                    routine_id="lower_a",
                    focus="lower",
                    type="training",
                ),
            ],
        ),
        nutrition=PlanNutrition(
            daily_targets=NutritionDailyTargets(
                calories_kcal=2600,
                protein_g=160,
                carbs_g=315,
                fat_g=75,
            ),
            strategy="superavit leve",
            adherence_target_pct=85,
        ),
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


def test_get_plan_status_reports_missing_fields_without_plan():
    db = MagicMock()
    db.get_plan.return_value = None
    db.get_plan_discovery.return_value = None

    result = json.loads(create_get_plan_status_tool(db, "user@test.com").invoke({}))

    assert result["status"] == "NO_PLAN"
    assert "goal_primary" in result["missing_fields"]


def test_update_plan_discovery_persists_partial_state():
    db = MagicMock()
    db.get_plan_discovery.return_value = None
    db.save_plan_discovery.return_value = "discovery_1"

    result = json.loads(
        create_update_plan_discovery_tool(db, "user@test.com").invoke(
            {"goal_primary": "muscle_gain", "goal_summary": "Ganhar massa"}
        )
    )

    assert result["status"] == "discovery_updated"
    assert result["saved"] is True
    assert "target_date" in result["missing_fields"]
    db.save_plan_discovery.assert_called_once()


def test_create_plan_from_discovery_requires_complete_discovery():
    db = MagicMock()
    db.get_plan_discovery.return_value = PlanDiscoveryState(
        user_email="user@test.com",
        goal_primary="muscle_gain",
        missing_fields=["target_date"],
    )

    result = json.loads(
        create_create_plan_from_discovery_tool(db, "user@test.com").invoke(
            make_create_input().model_dump(mode="json")
        )
    )

    assert result["status"] == "discovery_needed"
    assert result["saved"] is False
    db.save_plan.assert_not_called()


def test_create_plan_from_discovery_saves_and_clears_state():
    db = MagicMock()
    db.get_plan_discovery.return_value = PlanDiscoveryState(
        user_email="user@test.com",
        goal_primary="muscle_gain",
        goal_summary="Ganhar massa",
        target_date=date(2026, 8, 1),
        training_days_available=["monday", "thursday"],
        session_duration_min=60,
        constraints=["nenhuma"],
        preferences=["academia"],
        available_equipment=["barra"],
        metabolism_confirmed=True,
        missing_fields=[],
    )
    db.save_plan.return_value = "plan_1"

    result = json.loads(
        create_create_plan_from_discovery_tool(db, "user@test.com").invoke(
            make_create_input().model_dump(mode="json")
        )
    )

    assert result["status"] == "success"
    assert result["saved"] is True
    db.save_plan.assert_called_once()
    db.clear_plan_discovery.assert_called_once_with("user@test.com")


def test_update_plan_section_updates_existing_plan():
    db = MagicMock()
    db.get_plan.return_value = build_plan_from_create_input("user@test.com", make_create_input())
    db.save_plan.return_value = "plan_2"

    result = json.loads(
        create_update_plan_section_tool(db, "user@test.com").invoke(
            PlanSectionUpdateInput(
                section="nutrition",
                nutrition=PlanNutrition(
                    daily_targets=NutritionDailyTargets(
                        calories_kcal=2800,
                        protein_g=170,
                        carbs_g=330,
                        fat_g=80,
                    ),
                    strategy="superavit moderado",
                    adherence_target_pct=85,
                ),
            ).model_dump(mode="json")
        ),
    )

    assert result["status"] == "success"
    assert result["saved"] is True
    assert result["changed_sections"] == ["nutrition"]
    db.save_plan.assert_called_once()


def test_record_plan_review_appends_review_to_active_plan():
    db = MagicMock()
    db.get_plan.return_value = build_plan_from_create_input("user@test.com", make_create_input())
    db.save_plan.return_value = "plan_1"

    result = json.loads(
        create_record_plan_review_tool(db, "user@test.com").invoke(
            PlanReviewInput(
                summary="Aderencia forte",
                decision="manter estrategia",
                evidence_summary=["3 treinos completos"],
            ).model_dump(mode="json")
        )
    )

    assert result["status"] == "success"
    assert result["saved"] is True
    db.save_plan.assert_called_once()


def test_update_plan_section_blocks_save_when_hevy_sync_fails():
    db = MagicMock()
    base_plan = build_plan_from_create_input("user@test.com", make_create_input())
    bound_routine = base_plan.training.routines[0].model_copy(
        update={
            "external_bindings": [
                ExternalRoutineBinding(
                    provider="hevy",
                    external_routine_id="hevy_routine_1",
                )
            ]
        }
    )
    db.get_plan.return_value = base_plan.model_copy(
        update={
            "training": base_plan.training.model_copy(
                update={
                    "routines": [
                        bound_routine,
                        base_plan.training.routines[1],
                    ]
                }
            )
        }
    )
    db.get_user_profile.return_value = MagicMock(
        hevy_enabled=True,
        hevy_api_key="key",
    )
    db.workouts_repo = MagicMock()

    result = json.loads(
        create_update_plan_section_tool(db, "user@test.com").invoke(
            {
                "section": "training",
                "training": {
                    "split_name": "upper_lower",
                    "frequency_per_week": 1,
                    "session_duration_min": 60,
                    "routines": [
                        {
                            "id": "lower_a",
                            "name": "Lower A",
                            "exercises": [
                                {
                                    "name": "Agachamento",
                                    "sets": 4,
                                    "rep_range": {"min_reps": 5, "max_reps": 8},
                                    "intensity": {
                                        "prescription_type": "rpe",
                                        "target": "8",
                                    },
                                    "progression_rule": {
                                        "method": "linear_load",
                                        "increase_when": "completar volume com tecnica boa",
                                        "hold_when": "tecnica instavel",
                                        "deload_when": "fadiga acumulada por 2 semanas",
                                    },
                                }
                            ],
                        }
                    ],
                    "weekly_schedule": [
                        {
                            "day": "thursday",
                            "routine_id": "lower_a",
                            "focus": "lower",
                            "type": "training",
                        }
                    ],
                },
            }
        )
    )

    assert result["status"] == "external_sync_failed"
    assert result["saved"] is False
    assert result["external_sync_failed"] is True
    db.save_plan.assert_not_called()
