"""Plan domain service helpers for master plan orchestration and prompt context."""

from datetime import datetime, timezone, timedelta

from src.api.models.plan import (
    NutritionStrategy,
    PlanPromptContext,
    PlanUpsertInput,
    UserPlan,
)

REQUIRED_GOAL_FIELDS = ("primary", "objective_summary")
REQUIRED_TIMELINE_FIELDS = ("target_date", "review_cadence")
REQUIRED_STRATEGY_FIELDS = ("rationale", "adaptation_policy")
REQUIRED_SUMMARY_FIELDS = ("active_focus", "rationale", "next_review")
REQUIRED_NUTRITION_TARGET_FIELDS = ("calories", "protein_g", "carbs_g", "fat_g")
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


def missing_master_plan_fields(
    payload: PlanUpsertInput, latest_plan: UserPlan | None = None
) -> list[str]:
    """Validate required minimal fields for creation/update payload.

    When a latest_plan exists, fields missing from the payload
    are filled from the existing plan so that partial updates are accepted.
    """

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
        # Merge with existing plan targets so partial updates are valid
        merged_targets: dict = dict(nutrition_targets)
        if (
            latest_plan
            and latest_plan.nutrition_strategy
            and latest_plan.nutrition_strategy.daily_targets
        ):
            existing = latest_plan.nutrition_strategy.daily_targets.model_dump(
                exclude_none=True
            )
            for key, value in existing.items():
                if key not in merged_targets or merged_targets.get(key) is None:
                    merged_targets[key] = value

        missing.extend(
            [
                f"nutrition_strategy.daily_targets.{field}"
                for field in _missing_required_fields(
                    merged_targets,
                    REQUIRED_NUTRITION_TARGET_FIELDS,
                )
            ]
        )

    # training_program validation: fill missing from existing plan
    existing_routines: dict = {}
    if (
        latest_plan
        and latest_plan.training_program
        and latest_plan.training_program.routines
    ):
        existing_routines = {
            r.id: r.model_dump() for r in latest_plan.training_program.routines
        }

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

            # Fill missing fields from existing plan
            merged_routine = dict(routine)
            if routine.get("id") in existing_routines:
                for key, value in existing_routines[routine["id"]].items():
                    if key not in merged_routine or merged_routine.get(key) is None:
                        merged_routine[key] = value

            missing.extend(
                [
                    f"training_program.routines[{index}].{field}"
                    for field in _missing_required_fields(merged_routine, ("id", "name", "exercises"))
                ]
            )
            exercises = merged_routine.get("exercises", [])
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


def _merge_nutrition_strategy(
    latest: NutritionStrategy, payload: dict
) -> dict:
    """Deep-merge nutrition strategy, preserving existing daily_target fields."""
    latest_dict = latest.model_dump()
    merged = {**latest_dict, **payload}
    # Deep merge daily_targets so partial updates keep existing carbs_g/fat_g
    latest_targets = latest_dict.get("daily_targets") or {}
    payload_targets = payload.get("daily_targets") or {}
    if isinstance(latest_targets, dict) and isinstance(payload_targets, dict):
        merged["daily_targets"] = {**latest_targets, **payload_targets}
    return merged


def _merge_training_program(latest, payload: dict) -> dict:
    """Deep-merge training program, preserving existing routine exercises."""
    latest_dict = latest.model_dump()
    merged = {**latest_dict, **payload}

    # Deep merge routines: preserve exercises from existing routines
    latest_routines = {r["id"]: r for r in latest_dict.get("routines", [])}
    payload_routines = payload.get("routines", [])
    if isinstance(payload_routines, list):
        merged_routines = []
        for pr in payload_routines:
            if isinstance(pr, dict) and pr.get("id") in latest_routines:
                full = dict(latest_routines[pr["id"]])
                full.update({k: v for k, v in pr.items() if v is not None})
                merged_routines.append(full)
            else:
                merged_routines.append(pr)
        merged["routines"] = merged_routines

    return merged


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
        "nutrition_strategy": _merge_nutrition_strategy(
            latest_plan.nutrition_strategy, payload.nutrition_strategy
        ),
        "training_program": _merge_training_program(
            latest_plan.training_program, payload.training_program
        ),
        "current_summary": {
            **latest_plan.current_summary.model_dump(),
            **payload.current_summary,
        },
        "checkpoints": payload.checkpoints if payload.checkpoints else latest_plan.checkpoints,
    }
    return merged


def _coerce_datetime(value: datetime | str) -> datetime:
    """Normalize timeline values that may arrive as ISO strings."""
    if isinstance(value, str):
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            result = result.astimezone()
        return result
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.astimezone()
        return value
    raise TypeError(f"invalid datetime value type: {type(value).__name__}")


def _aware_now() -> datetime:
    """Return current UTC time as an offset-aware datetime."""
    return datetime.now(timezone.utc)


def validate_training_program_quality(program: dict) -> list[str]:
    """Validate that a training program proposal meets minimum quality standards.

    Returns a list of quality issues (empty = pass).
    Evaluates completeness and coherence, not arbitrary exercise counts.
    """
    issues: list[str] = []
    routines = program.get("routines", [])
    if not isinstance(routines, list) or len(routines) == 0:
        issues.append("training_program must have at least one routine")
        return issues

    frequency = program.get("frequency_per_week", 0)
    has_schedule = bool(program.get("weekly_schedule"))

    for idx, routine in enumerate(routines):
        if not isinstance(routine, dict):
            continue
        exercises = routine.get("exercises", [])
        if not isinstance(exercises, list) or len(exercises) == 0:
            issues.append(f"routine[{idx}] has no exercises")
            continue
        all_minimal = all(
            not ex.get("load_guidance")
            or not ex.get("reps")
            or not ex.get("sets")
            for ex in exercises
        )
        if all_minimal:
            issues.append(
                f"routine[{idx}] '{routine.get('name', '')}' has exercises "
                f"missing load_guidance, reps, or sets"
            )
        if frequency >= 4 and len(exercises) <= 2:
            issues.append(
                f"routine[{idx}] '{routine.get('name', '')}' has only "
                f"{len(exercises)} exercise(s) for a {frequency}x/week program — "
                f"high-frequency programs need at least 3 substantive exercises per session"
            )
    if not has_schedule:
        issues.append("training_program missing weekly_schedule")
    return issues


def build_plan_singleton(
    user_email: str,
    latest_plan: UserPlan | None,
    payload: PlanUpsertInput,
) -> UserPlan:
    """Build singleton master plan payload."""

    now = _aware_now()
    merged = _merge_plan_sections(latest_plan, payload)

    timeline_data = dict(merged["timeline"])
    timeline_data["start_date"] = now
    if "target_date" in timeline_data and timeline_data["target_date"] is not None:
        target = _coerce_datetime(timeline_data["target_date"])
        timeline_data["target_date"] = max(target, now)
    else:
        timeline_data["target_date"] = timeline_data["start_date"] + timedelta(days=84)

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

    nt = snapshot.nutrition_targets
    nutrition_str = (
        f"{nt.get('calories', '?')} kcal, "
        f"{nt.get('protein_g', '?')}g proteina, "
        f"{nt.get('carbs_g', '?')}g carboidratos, "
        f"{nt.get('fat_g', '?')}g gordura"
        if nt
        else "nao definidas"
    )

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
        f"- Metas nutricionais diarias (FONTES PRIMARIAS, sobrepoe algoritmo): {nutrition_str}\n"
        f"- Split de treino: {snapshot.training_split}\n"
        f"- Rotinas no programa: {routines_count}\n"
        f"- Itens na agenda semanal: {schedule_count}\n"
        f"- Resumo atual: {snapshot.current_summary}\n"
        f"- Ultimo checkpoint: {latest_checkpoint}"
    )
