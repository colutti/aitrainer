from datetime import datetime, timezone

from src.api.models.plan import (
    NutritionDailyTargets,
    NutritionStrategy,
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
    WeeklyScheduleItem,
)
from src.services.plan_service import (
    build_plan_singleton,
    build_plan_prompt_snapshot,
    format_plan_snapshot,
    missing_master_plan_fields,
)

now = datetime.now(timezone.utc)


def make_plan() -> UserPlan:
    return UserPlan(
        user_email="user@test.com",
        title="Plano Atual",
        goal=PlanGoal(
            primary="build_muscle",
            objective_summary="Ganhar massa com controle de gordura",
            success_criteria=["volume em alta"],
        ),
        timeline=PlanTimeline(
            start_date=datetime(2026, 4, 19, tzinfo=timezone.utc),
            target_date=datetime(2026, 6, 19, tzinfo=timezone.utc),
            review_cadence="quinzenal",
        ),
        strategy=PlanStrategy(
            rationale="superavit leve com progressao de carga",
            adaptation_policy="ajustar macros por evidencia semanal",
            constraints=["viagem quinta"],
            preferences=["academia"],
            current_risks=["sono irregular"],
        ),
        nutrition_strategy=NutritionStrategy(
            daily_targets=NutritionDailyTargets(
                calories=3000, protein_g=180, carbs_g=300, fat_g=90,
            ),
        ),
        training_program=TrainingProgram(
            split_name="push_pull_legs",
            frequency_per_week=2,
            session_duration_min=60,
            routines=[
                TrainingRoutine(
                    id="push_a",
                    name="Push A",
                    exercises=[
                        TrainingExercise(
                            name="Supino Reto", sets=4, reps="6-8", load_guidance="RPE 8",
                        ),
                    ],
                ),
                TrainingRoutine(
                    id="pull_a",
                    name="Pull A",
                    exercises=[
                        TrainingExercise(
                            name="Remada Curvada", sets=4, reps="8-10", load_guidance="RPE 8",
                        ),
                    ],
                ),
            ],
            weekly_schedule=[
                WeeklyScheduleItem(day="monday", routine_id="push_a", focus="push"),
                WeeklyScheduleItem(day="tuesday", routine_id="pull_a", focus="pull"),
            ],
        ),
        current_summary=PlanCurrentSummary(
            active_focus="consistencia",
            rationale="executar bloco base por 2 semanas",
            next_review="2026-05-15",
        ),
        checkpoints=[],
    )


def test_build_plan_prompt_snapshot_returns_none_when_missing_plan():
    assert build_plan_prompt_snapshot(None) is None


def test_build_plan_prompt_snapshot_compacts_active_plan():
    snapshot = build_plan_prompt_snapshot(make_plan())

    assert snapshot is not None
    assert snapshot.title == "Plano Atual"
    assert snapshot.goal_primary == "build_muscle"
    assert snapshot.objective_summary == "Ganhar massa com controle de gordura"
    assert "2026-04-19" in snapshot.timeline_window
    assert "2026-06-19" in snapshot.timeline_window
    assert snapshot.review_cadence == "quinzenal"
    assert snapshot.strategy_rationale == "superavit leve com progressao de carga"
    assert snapshot.constraints == ["viagem quinta"]
    assert snapshot.preferences == ["academia"]
    assert snapshot.nutrition_targets["calories"] == 3000
    assert snapshot.training_split == "push_pull_legs"
    assert len(snapshot.weekly_schedule) == 2
    assert len(snapshot.routines) == 2


def test_format_plan_snapshot_creates_prompt_ready_block():
    snapshot = build_plan_prompt_snapshot(make_plan())
    content = format_plan_snapshot(snapshot)

    assert "Plano mestre ativo" in content
    assert "build_muscle" in content
    assert "Ganhar massa com controle de gordura" in content
    assert "push_pull_legs" in content
    assert "3000 kcal" in content
    assert "viagem quinta" in content


def test_format_plan_snapshot_handles_none():
    content = format_plan_snapshot(None)
    assert "Nenhum plano mestre registrado" in content


def test_format_plan_snapshot_handles_empty_constraints():
    snapshot = PlanPromptContext(
        title="Plano Simples",
        goal_primary="lose_fat",
        objective_summary="Definir",
        timeline_window="2026-04 a 2026-07",
        review_cadence="semanal",
        strategy_rationale="deficit",
        training_split="full_body",
    )
    content = format_plan_snapshot(snapshot)
    assert "sem restricoes" in content


def test_format_plan_snapshot_handles_missing_nutrition_targets():
    snapshot = PlanPromptContext(
        title="Plano sem Nutri",
        goal_primary="build_muscle",
        objective_summary="Crescer",
        timeline_window="2026-04 a 2026-07",
        review_cadence="semanal",
        strategy_rationale="superavit",
        nutrition_targets={},
        training_split="upper_lower",
    )
    content = format_plan_snapshot(snapshot)
    assert "nao definidas" in content


def test_build_plan_singleton_creates_valid_plan_from_upsert_input():
    payload = PlanUpsertInput(
        title="Plano Inicial",
        change_reason="initial_plan",
        goal={"primary": "lose_fat", "objective_summary": "Recomposicao corporal"},
        timeline={
            "target_date": "2026-09-01T00:00:00+00:00",
            "review_cadence": "quinzenal",
        },
        strategy={
            "rationale": "Deficit moderado com foco em forca",
            "adaptation_policy": "ajustar por evidencia semanal",
            "constraints": ["rotina corrida"],
            "preferences": ["academia"],
            "current_risks": [],
        },
        nutrition_strategy={
            "daily_targets": {
                "calories": 2400,
                "protein_g": 180,
                "carbs_g": 200,
                "fat_g": 70,
            },
        },
        training_program={
            "split_name": "full_body",
            "frequency_per_week": 1,
            "session_duration_min": 45,
            "routines": [
                {
                    "id": "fb_a",
                    "name": "Full Body A",
                    "exercises": [
                        {
                            "name": "Agachamento",
                            "sets": 4,
                            "reps": "6-8",
                            "load_guidance": "RPE 8",
                        },
                    ],
                }
            ],
            "weekly_schedule": [
                {"day": "monday", "routine_id": "fb_a", "focus": "full_body"},
            ],
        },
        current_summary={
            "active_focus": "consistencia",
            "rationale": "executar bloco inicial",
            "next_review": "2026-05-15",
        },
    )

    plan = build_plan_singleton("user@test.com", None, payload)

    assert plan.user_email == "user@test.com"
    assert plan.title == "Plano Inicial"
    assert plan.goal.primary == "lose_fat"
    assert plan.change_reason == "initial_plan"
    assert plan.timeline.target_date >= datetime.now(timezone.utc)
    assert plan.nutrition_strategy.daily_targets.calories == 2400
    assert plan.training_program.routines[0].id == "fb_a"


def test_missing_master_plan_fields_returns_all_when_empty_payload():
    payload = PlanUpsertInput(
        title="Plano Vazio",
        goal={},
        timeline={},
        strategy={},
        nutrition_strategy={},
        training_program={},
        current_summary={},
    )
    missing = missing_master_plan_fields(payload)
    assert len(missing) > 0
    assert "goal.primary" in missing
    assert "timeline.target_date" in missing
    assert "strategy.rationale" in missing
    assert "current_summary.active_focus" in missing


def test_missing_master_plan_fields_merges_from_existing_plan():
    payload = PlanUpsertInput(
        title="Plano Parcial",
        goal={"primary": "lose_fat"},
        timeline={"target_date": "2026-09-01T00:00:00+00:00"},
        strategy={"rationale": "ok"},
        nutrition_strategy={
            "daily_targets": {
                "calories": 2000,
                "protein_g": 150,
            },
        },
        training_program={
            "split_name": "full_body",
            "routines": [
                {
                    "id": "fb_a",
                    "name": "Full Body A",
                    "exercises": [
                        {"name": "Supino", "sets": 3, "reps": "8-10", "load_guidance": "RPE 7"},
                    ],
                },
            ],
        },
        current_summary={
            "active_focus": "inicio",
        },
    )

    existing_plan = make_plan()
    missing = missing_master_plan_fields(payload, existing_plan)

    assert missing == []


def test_build_plan_singleton_merges_with_existing_plan():
    payload = PlanUpsertInput(
        title="Plano Atualizado",
        change_reason="review",
        goal={"primary": "lose_fat", "objective_summary": "Definir mais"},
        timeline={
            "target_date": "2026-12-01T00:00:00+00:00",
            "review_cadence": "mensal",
        },
        strategy={
            "rationale": "Deficit agressivo",
            "adaptation_policy": "ajustar quinzenal",
        },
        nutrition_strategy={
            "daily_targets": {
                "calories": 2200,
            },
        },
        training_program={
            "split_name": "upper_lower",
            "frequency_per_week": 2,
            "session_duration_min": 50,
            "routines": [
                {
                    "id": "push_a",
                    "name": "Push A",
                    "exercises": [
                        {"name": "Desenvolvimento", "sets": 4, "reps": "8-10", "load_guidance": "RPE 8"},
                    ],
                },
            ],
            "weekly_schedule": [
                {"day": "monday", "routine_id": "push_a", "focus": "push"},
            ],
        },
        current_summary={
            "active_focus": "intensidade",
            "rationale": "aumentar volume",
            "next_review": "2026-07-01",
        },
    )

    existing = make_plan()
    plan = build_plan_singleton("user@test.com", existing, payload)

    assert plan.title == "Plano Atualizado"
    assert plan.goal.primary == "lose_fat"
    assert plan.goal.objective_summary == "Definir mais"

    assert plan.strategy.rationale == "Deficit agressivo"

    assert plan.nutrition_strategy.daily_targets.calories == 2200

    assert plan.training_program.split_name == "upper_lower"
    assert plan.training_program.frequency_per_week == 2

    assert plan.current_summary.active_focus == "intensidade"


def test_build_plan_singleton_preserves_omitted_routines_and_schedule_on_update():
    payload = PlanUpsertInput(
        title="Plano Atualizado",
        change_reason="review",
        goal={"primary": "build_muscle", "objective_summary": "Ganhar massa com mais foco"},
        timeline={
            "target_date": "2026-12-01T00:00:00+00:00",
            "review_cadence": "mensal",
        },
        strategy={
            "rationale": "superavit com foco no treino A",
            "adaptation_policy": "ajustar quinzenal",
        },
        nutrition_strategy={
            "daily_targets": {
                "calories": 3050,
            },
        },
        training_program={
            "split_name": "push_pull_legs",
            "frequency_per_week": 2,
            "session_duration_min": 60,
            "routines": [
                {
                    "id": "push_a",
                    "name": "Push A",
                    "exercises": [
                        {
                            "name": "Supino Inclinado",
                            "sets": 4,
                            "reps": "8-10",
                            "load_guidance": "RPE 8",
                        },
                    ],
                },
            ],
            "weekly_schedule": [
                {"day": "monday", "routine_id": "push_a", "focus": "push"},
            ],
        },
        current_summary={
            "active_focus": "intensidade",
            "rationale": "aumentar volume",
            "next_review": "2026-07-01",
        },
    )

    existing = make_plan()
    plan = build_plan_singleton("user@test.com", existing, payload)

    assert [routine.id for routine in plan.training_program.routines] == [
        "push_a",
        "pull_a",
    ]
    assert plan.training_program.routines[0].exercises[0].name == "Supino Inclinado"
    assert plan.training_program.routines[1].exercises[0].name == "Remada Curvada"
    assert [(item.day, item.routine_id) for item in plan.training_program.weekly_schedule] == [
        ("monday", "push_a"),
        ("tuesday", "pull_a"),
    ]


def test_build_plan_singleton_coerces_numeric_routine_ids_from_llm_payload():
    payload = PlanUpsertInput(
        title="Plano Atualizado",
        change_reason="exercise_swap",
        goal={"primary": "build_muscle", "objective_summary": "Ganhar massa com mais foco"},
        timeline={
            "target_date": "2026-12-01T00:00:00+00:00",
            "review_cadence": "mensal",
        },
        strategy={
            "rationale": "substituir exercicio de costas",
            "adaptation_policy": "ajustar por evidencia semanal",
        },
        nutrition_strategy={
            "daily_targets": {
                "calories": 3050,
            },
        },
        training_program={
            "split_name": "push_pull_legs",
            "frequency_per_week": 2,
            "session_duration_min": 60,
            "routines": [
                {
                    "id": 1,
                    "name": "Pull A",
                    "exercises": [
                        {
                            "name": "Barra Fixa",
                            "sets": 4,
                            "reps": "6-10",
                            "load_guidance": "RPE 8",
                        },
                    ],
                },
            ],
            "weekly_schedule": [
                {"day": "tuesday", "routine_id": 1, "focus": "pull"},
            ],
        },
        current_summary={
            "active_focus": "costas",
            "rationale": "substituir puxada alta por barra fixa",
            "next_review": "2026-07-01",
        },
    )

    plan = build_plan_singleton("user@test.com", make_plan(), payload)

    assert plan.training_program.routines[0].id == "1"
    assert plan.training_program.weekly_schedule[0].routine_id == "1"


def test_build_plan_singleton_preserves_created_at_and_start_date_on_update():
    payload = PlanUpsertInput(
        title="Plano Atualizado",
        change_reason="review",
        goal={"primary": "build_muscle", "objective_summary": "Ganhar massa com mais foco"},
        timeline={
            "target_date": "2026-12-01T00:00:00+00:00",
            "review_cadence": "mensal",
        },
        strategy={
            "rationale": "superavit com foco no treino A",
            "adaptation_policy": "ajustar quinzenal",
        },
        nutrition_strategy={
            "daily_targets": {
                "calories": 3050,
            },
        },
        training_program={
            "split_name": "push_pull_legs",
            "frequency_per_week": 2,
            "session_duration_min": 60,
            "routines": [
                {
                    "id": "push_a",
                    "name": "Push A",
                    "exercises": [
                        {
                            "name": "Supino Inclinado",
                            "sets": 4,
                            "reps": "8-10",
                            "load_guidance": "RPE 8",
                        },
                    ],
                },
            ],
            "weekly_schedule": [
                {"day": "monday", "routine_id": "push_a", "focus": "push"},
            ],
        },
        current_summary={
            "active_focus": "intensidade",
            "rationale": "aumentar volume",
            "next_review": "2026-07-01",
        },
    )

    existing = make_plan()
    original_created_at = existing.created_at
    original_start_date = existing.timeline.start_date

    plan = build_plan_singleton("user@test.com", existing, payload)

    assert plan.created_at == original_created_at
    assert plan.timeline.start_date == original_start_date
