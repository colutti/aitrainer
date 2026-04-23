"""Plan domain service helpers for master plan orchestration and prompt context."""

from datetime import datetime, timedelta

from src.api.models.plan import PlanPromptContext, PlanUpsertInput, UserPlan

REQUIRED_GOAL_FIELDS = ("primary", "objective_summary")
REQUIRED_TIMELINE_FIELDS = ("target_date", "review_cadence")
REQUIRED_STRATEGY_FIELDS = ("rationale", "adaptation_policy")
REQUIRED_SUMMARY_FIELDS = ("active_focus", "rationale")
REQUIRED_NUTRITION_TARGET_FIELDS = ("calories", "protein_g")
REQUIRED_PROGRAM_FIELDS = (
    "split_name",
    "frequency_per_week",
    "session_duration_min",
    "routines",
    "weekly_schedule",
)


def _missing_required_fields(payload: dict, required_fields: tuple[str, ...]) -> list[str]:
    missing: list[str] = []
    for field in required_fields:
        value = payload.get(field)
        if value is None:
            missing.append(field)
            continue
        if isinstance(value, str) and not value.strip():
            missing.append(field)
            continue
        if isinstance(value, list) and len(value) == 0:
            missing.append(field)
    return missing


def missing_master_plan_fields(payload: PlanUpsertInput) -> list[str]:
    """Validate required minimal fields for creation/update payload."""

    missing: list[str] = []
    missing.extend(
        [
            f"goal.{field}"
            for field in _missing_required_fields(payload.goal, REQUIRED_GOAL_FIELDS)
        ]
    )
    missing.extend(
        [
            f"timeline.{field}"
            for field in _missing_required_fields(
                payload.timeline, REQUIRED_TIMELINE_FIELDS
            )
        ]
    )
    missing.extend(
        [
            f"strategy.{field}"
            for field in _missing_required_fields(
                payload.strategy, REQUIRED_STRATEGY_FIELDS
            )
        ]
    )

    nutrition_targets = payload.nutrition_strategy.get("daily_targets", {})
    if not isinstance(nutrition_targets, dict):
        missing.append("nutrition_strategy.daily_targets")
    else:
        missing.extend(
            [
                f"nutrition_strategy.daily_targets.{field}"
                for field in _missing_required_fields(
                    nutrition_targets,
                    REQUIRED_NUTRITION_TARGET_FIELDS,
                )
            ]
        )

    missing.extend(
        [
            f"training_program.{field}"
            for field in _missing_required_fields(payload.training_program, REQUIRED_PROGRAM_FIELDS)
        ]
    )

    if isinstance(payload.training_program.get("routines"), list):
        for index, routine in enumerate(payload.training_program["routines"]):
            if not isinstance(routine, dict):
                missing.append(f"training_program.routines[{index}]")
                continue
            missing.extend(
                [
                    f"training_program.routines[{index}].{field}"
                    for field in _missing_required_fields(routine, ("id", "name", "exercises"))
                ]
            )
            exercises = routine.get("exercises", [])
            if isinstance(exercises, list):
                for ex_index, exercise in enumerate(exercises):
                    if not isinstance(exercise, dict):
                        missing.append(
                            f"training_program.routines[{index}].exercises[{ex_index}]"
                        )
                        continue
                    missing.extend(
                        [
                            f"training_program.routines[{index}].exercises[{ex_index}].{field}"
                            for field in _missing_required_fields(
                                exercise,
                                ("name", "sets", "reps", "load_guidance"),
                            )
                        ]
                    )

    missing.extend(
        [
            f"current_summary.{field}"
            for field in _missing_required_fields(payload.current_summary, REQUIRED_SUMMARY_FIELDS)
        ]
    )

    return sorted(set(missing))


def _merge_plan_sections(latest_plan: UserPlan | None, payload: PlanUpsertInput) -> dict:
    if latest_plan is None:
        return {
            "goal": payload.goal,
            "timeline": payload.timeline,
            "strategy": payload.strategy,
            "nutrition_strategy": payload.nutrition_strategy,
            "training_program": payload.training_program,
            "current_summary": payload.current_summary,
            "checkpoints": payload.checkpoints,
        }

    merged = {
        "goal": {**latest_plan.goal.model_dump(), **payload.goal},
        "timeline": {**latest_plan.timeline.model_dump(), **payload.timeline},
        "strategy": {**latest_plan.strategy.model_dump(), **payload.strategy},
        "nutrition_strategy": {
            **latest_plan.nutrition_strategy.model_dump(),
            **payload.nutrition_strategy,
        },
        "training_program": {
            **latest_plan.training_program.model_dump(),
            **payload.training_program,
        },
        "current_summary": {
            **latest_plan.current_summary.model_dump(),
            **payload.current_summary,
        },
        "checkpoints": payload.checkpoints if payload.checkpoints else latest_plan.checkpoints,
    }
    return merged


def build_plan_singleton(
    user_email: str,
    latest_plan: UserPlan | None,
    payload: PlanUpsertInput,
) -> UserPlan:
    """Build singleton master plan payload."""

    now = datetime.now()
    merged = _merge_plan_sections(latest_plan, payload)

    timeline_data = dict(merged["timeline"])
    start_date = latest_plan.timeline.start_date if latest_plan else now
    timeline_data["start_date"] = timeline_data.get("start_date", start_date)
    timeline_data.setdefault(
        "target_date",
        timeline_data["start_date"] + timedelta(days=84),
    )

    return UserPlan(
        user_email=user_email,
        title=payload.title,
        goal=merged["goal"],
        timeline=timeline_data,
        strategy=merged["strategy"],
        nutrition_strategy=merged["nutrition_strategy"],
        training_program=merged["training_program"],
        checkpoints=merged["checkpoints"],
        current_summary=merged["current_summary"],
        change_reason=payload.change_reason,
    )


def build_plan_prompt_snapshot(plan: UserPlan | None) -> PlanPromptContext | None:
    """Build structured full snapshot from active plan payload."""
    if plan is None:
        return None

    latest_checkpoint = plan.checkpoints[-1].model_dump() if plan.checkpoints else None

    return PlanPromptContext(
        title=plan.title,
        goal_primary=plan.goal.primary,
        objective_summary=plan.goal.objective_summary,
        timeline_window=(
            f"{plan.timeline.start_date.strftime('%Y-%m-%d')} a "
            f"{plan.timeline.target_date.strftime('%Y-%m-%d')}"
        ),
        review_cadence=plan.timeline.review_cadence,
        strategy_rationale=plan.strategy.rationale,
        constraints=plan.strategy.constraints,
        preferences=plan.strategy.preferences,
        nutrition_targets=plan.nutrition_strategy.daily_targets.model_dump(
            exclude_none=True
        ),
        training_split=plan.training_program.split_name,
        weekly_schedule=[item.model_dump() for item in plan.training_program.weekly_schedule],
        routines=[item.model_dump() for item in plan.training_program.routines],
        current_summary=plan.current_summary.model_dump(exclude_none=True),
        latest_checkpoint=latest_checkpoint,
    )


def format_plan_snapshot(snapshot: PlanPromptContext | None) -> str:
    """Format structured snapshot as readable prompt block."""
    if snapshot is None:
        return (
            "Nenhum plano mestre registrado.\n"
            "Acao obrigatoria imediata: inicie discovery e insista na criacao do plano "
            "mestre (objetivo, prazo, estrategia, nutricao e programa semanal)."
        )

    constraints = (
        ", ".join(snapshot.constraints) if snapshot.constraints else "sem restricoes"
    )
    preferences = (
        ", ".join(snapshot.preferences)
        if snapshot.preferences
        else "sem preferencias declaradas"
    )
    routines_count = len(snapshot.routines)
    schedule_count = len(snapshot.weekly_schedule)
    latest_checkpoint = snapshot.latest_checkpoint or {}

    return (
        "Plano mestre ativo (fonte primaria):\n"
        f"- Titulo: {snapshot.title}\n"
        f"- Objetivo principal: {snapshot.goal_primary}\n"
        f"- Objetivo resumido: {snapshot.objective_summary}\n"
        f"- Janela do plano: {snapshot.timeline_window}\n"
        f"- Cadencia de revisao: {snapshot.review_cadence}\n"
        f"- Racional estrategico: {snapshot.strategy_rationale}\n"
        f"- Restricoes: {constraints}\n"
        f"- Preferencias: {preferences}\n"
        f"- Metas nutricionais diarias: {snapshot.nutrition_targets}\n"
        f"- Split de treino: {snapshot.training_split}\n"
        f"- Rotinas no programa: {routines_count}\n"
        f"- Itens na agenda semanal: {schedule_count}\n"
        f"- Resumo atual: {snapshot.current_summary}\n"
        f"- Ultimo checkpoint: {latest_checkpoint}"
    )
