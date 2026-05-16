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


def _prefixed_missing_fields(
    section_name: str, payload: dict, required_fields: tuple[str, ...]
) -> list[str]:
    return [
        f"{section_name}.{field}"
        for field in _missing_required_fields(payload, required_fields)
    ]


def _existing_daily_targets(latest_plan: UserPlan | None) -> dict:
    if not latest_plan or not latest_plan.nutrition_strategy:
        return {}
    daily_targets = latest_plan.nutrition_strategy.daily_targets
    if not daily_targets:
        return {}
    return daily_targets.model_dump(exclude_none=True)


def _merge_missing_values(base: dict, existing: dict) -> dict:
    merged = dict(base)
    for key, value in existing.items():
        if key not in merged or merged.get(key) is None:
            merged[key] = value
    return merged


def _existing_routine_map(latest_plan: UserPlan | None) -> dict:
    if not latest_plan or not latest_plan.training_program:
        return {}
    routines = latest_plan.training_program.routines or []
    return {routine.id: routine.model_dump() for routine in routines}


def _missing_exercise_fields(
    exercises: list, routine_index: int,
) -> list[str]:
    missing: list[str] = []
    for ex_index, exercise in enumerate(exercises):
        if not isinstance(exercise, dict):
            missing.append(f"training_program.routines[{routine_index}].exercises[{ex_index}]")
            continue
        missing.extend(
            [
                f"training_program.routines[{routine_index}].exercises[{ex_index}].{field}"
                for field in _missing_required_fields(exercise, ("name", "sets", "reps"))
            ]
        )
    return missing


def _missing_routine_fields(routines: list, existing_routines: dict) -> list[str]:
    missing: list[str] = []
    for index, routine in enumerate(routines):
        if not isinstance(routine, dict):
            missing.append(f"training_program.routines[{index}]")
            continue

        merged_routine = _merge_missing_values(
            routine,
            existing_routines.get(routine.get("id"), {}),
        )
        missing.extend(
            [
                f"training_program.routines[{index}].{field}"
                for field in _missing_required_fields(
                    merged_routine, ("id", "name", "exercises")
                )
            ]
        )
        exercises = merged_routine.get("exercises", [])
        if isinstance(exercises, list):
            missing.extend(_missing_exercise_fields(exercises, index))
    return missing


def missing_master_plan_fields(
    payload: PlanUpsertInput, latest_plan: UserPlan | None = None
) -> list[str]:
    """Validate required minimal fields for creation/update payload.

    When a latest_plan exists, fields missing from the payload
    are filled from the existing plan so that partial updates are accepted.
    """

    existing_goal = (
        latest_plan.goal.model_dump() if latest_plan and latest_plan.goal else {}
    )
    existing_timeline = (
        latest_plan.timeline.model_dump() if latest_plan and latest_plan.timeline else {}
    )
    existing_strategy = (
        latest_plan.strategy.model_dump() if latest_plan and latest_plan.strategy else {}
    )
    existing_summary = (
        latest_plan.current_summary.model_dump()
        if latest_plan and latest_plan.current_summary
        else {}
    )
    existing_program = (
        latest_plan.training_program.model_dump()
        if latest_plan and latest_plan.training_program
        else {}
    )

    missing: list[str] = []
    missing.extend(
        _prefixed_missing_fields(
            "goal",
            _merge_missing_values(payload.goal or {}, existing_goal),
            REQUIRED_GOAL_FIELDS,
        )
    )
    missing.extend(
        _prefixed_missing_fields(
            "timeline",
            _merge_missing_values(payload.timeline or {}, existing_timeline),
            REQUIRED_TIMELINE_FIELDS,
        )
    )
    missing.extend(
        _prefixed_missing_fields(
            "strategy",
            _merge_missing_values(payload.strategy or {}, existing_strategy),
            REQUIRED_STRATEGY_FIELDS,
        )
    )

    nutrition_targets = payload.nutrition_strategy.get("daily_targets", {})
    if not isinstance(nutrition_targets, dict):
        missing.append("nutrition_strategy.daily_targets")
    else:
        merged_targets = _merge_missing_values(
            nutrition_targets, _existing_daily_targets(latest_plan)
        )
        missing.extend(
            _prefixed_missing_fields(
                "nutrition_strategy.daily_targets",
                merged_targets,
                REQUIRED_NUTRITION_TARGET_FIELDS,
            )
        )

    existing_routines = _existing_routine_map(latest_plan)

    merged_program = _merge_missing_values(
        payload.training_program or {}, existing_program
    )
    missing.extend(
        _prefixed_missing_fields(
            "training_program", merged_program, REQUIRED_PROGRAM_FIELDS
        )
    )

    if isinstance(merged_program.get("routines"), list):
        missing.extend(
            _missing_routine_fields(merged_program["routines"], existing_routines)
        )

    missing.extend(
        _prefixed_missing_fields(
            "current_summary",
            _merge_missing_values(payload.current_summary or {}, existing_summary),
            REQUIRED_SUMMARY_FIELDS,
        )
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


def _merge_routines(latest_dict: dict, payload_routines: list) -> list:
    latest_routines = {r["id"]: r for r in latest_dict.get("routines", [])}
    merged_routines = []
    seen_routine_ids: set[str] = set()

    for payload_routine in payload_routines:
        routine_id = payload_routine.get("id") if isinstance(payload_routine, dict) else None
        if routine_id in latest_routines:
            full = dict(latest_routines[routine_id])
            full.update({k: v for k, v in payload_routine.items() if v is not None})
            merged_routines.append(full)
            seen_routine_ids.add(routine_id)
            continue
        merged_routines.append(payload_routine)
        if routine_id:
            seen_routine_ids.add(routine_id)

    for existing in latest_dict.get("routines", []):
        routine_id = existing.get("id")
        if routine_id and routine_id not in seen_routine_ids:
            merged_routines.append(existing)

    return merged_routines


def _merge_weekly_schedule(latest_dict: dict, payload_schedule: list) -> list:
    merged_schedule = []
    seen_schedule_keys = set()

    for item in payload_schedule:
        if isinstance(item, dict):
            seen_schedule_keys.add((item.get("day"), item.get("type", "training")))
        merged_schedule.append(item)

    for existing in latest_dict.get("weekly_schedule", []):
        key = (existing.get("day"), existing.get("type", "training"))
        if key not in seen_schedule_keys:
            merged_schedule.append(existing)

    return merged_schedule


def _normalize_training_program_ids(program: dict) -> dict:
    """Coerce routine identifiers from LLM/tool payloads to strings."""
    normalized = dict(program)
    routines = normalized.get("routines")
    if isinstance(routines, list):
        normalized["routines"] = [
            {
                **routine,
                "id": str(routine["id"]) if routine.get("id") is not None else routine.get("id"),
            }
            if isinstance(routine, dict)
            else routine
            for routine in routines
        ]

    schedule = normalized.get("weekly_schedule")
    if isinstance(schedule, list):
        normalized["weekly_schedule"] = [
            {
                **item,
                "routine_id": (
                    str(item["routine_id"])
                    if item.get("routine_id") is not None
                    else item.get("routine_id")
                ),
            }
            if isinstance(item, dict)
            else item
            for item in schedule
        ]
    return normalized


def _merge_training_program(latest, payload: dict) -> dict:
    """Deep-merge training program while preserving omitted routines and schedule items."""
    payload = _normalize_training_program_ids(payload)
    latest_dict = latest.model_dump()
    merged = {**latest_dict, **payload}

    payload_routines = payload.get("routines", [])
    if isinstance(payload_routines, list):
        merged["routines"] = _merge_routines(latest_dict, payload_routines)

    payload_schedule = payload.get("weekly_schedule", [])
    if isinstance(payload_schedule, list):
        merged["weekly_schedule"] = _merge_weekly_schedule(latest_dict, payload_schedule)

    return _normalize_training_program_ids(merged)


def _merge_plan_sections(latest_plan: UserPlan | None, payload: PlanUpsertInput) -> dict:
    if latest_plan is None:
        return {
            "goal": payload.goal,
            "timeline": payload.timeline,
            "strategy": payload.strategy,
            "nutrition_strategy": payload.nutrition_strategy,
            "training_program": _normalize_training_program_ids(payload.training_program),
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
    """Normalize timeline values to UTC-aware datetimes."""
    if isinstance(value, str):
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            return result.replace(tzinfo=timezone.utc)
        return result.astimezone(timezone.utc)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    raise TypeError(f"invalid datetime value type: {type(value).__name__}")


def _aware_now() -> datetime:
    """Return current UTC time as an offset-aware datetime."""
    return datetime.now(timezone.utc)


def build_plan_singleton(
    user_email: str,
    latest_plan: UserPlan | None,
    payload: PlanUpsertInput,
) -> UserPlan:
    """Build singleton master plan payload."""

    now = _aware_now()
    merged = _merge_plan_sections(latest_plan, payload)

    timeline_data = dict(merged["timeline"])
    if latest_plan is None:
        start = now
    else:
        start = _coerce_datetime(latest_plan.timeline.start_date)
    timeline_data["start_date"] = start
    if "target_date" in timeline_data and timeline_data["target_date"] is not None:
        target = _coerce_datetime(timeline_data["target_date"])
        timeline_data["target_date"] = max(target, start)
    else:
        timeline_data["target_date"] = start + timedelta(days=84)

    plan = UserPlan(
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
    if latest_plan is not None:
        plan.created_at = latest_plan.created_at
    return plan


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
