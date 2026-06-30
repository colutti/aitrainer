"""Plan V2 service helpers for discovery, prompt context and view models."""

from datetime import date, datetime, timezone
import re

from src.api.models.plan import (
    ActivePlanView,
    CANONICAL_PLAN_SECTIONS,
    CANONICAL_WEEKDAYS,
    DiscoveryView,
    PlanConflict,
    PlanCreateInput,
    PlanDiscoveryState,
    PlanProgressSnapshot,
    PlanPromptContext,
    PlanReview,
    PlanReviewInput,
    PlanSectionUpdateInput,
    PlanViewModel,
    ProgressMetric,
    WeeklyScheduleView,
    TodayTrainingView,
    UserPlan,
)


DISCOVERY_FIELD_LABELS = {
    "goal_primary": "objetivo principal",
    "goal_summary": "resumo do objetivo",
    "target_date": "data alvo",
    "training_days_available": "dias disponiveis para treino",
    "session_duration_min": "duracao da sessao",
    "constraints": "restricoes ou limitacoes",
    "preferences": "preferencias relevantes",
    "available_equipment": "equipamentos disponiveis",
    "metabolism_confirmed": "dados metabolicos oficiais",
}

_PHASE_KEYWORDS = {
    "muscle_gain": ("bulk", "bulking", "hipertrof", "ganho de massa", "massa muscular"),
    "fat_loss": ("cut", "cutting", "defini", "perda de gordura", "emagrec"),
    "recomposition": ("recomp", "manuten", "defini", "reduzir gordura"),
    "performance": ("performance", "desempenho", "forca", "potencia"),
}

_OUTCOME_FORBIDDEN_TERMS = {
    "muscle_gain": ("deficit", "déficit", "manuten"),
    "fat_loss": ("surplus", "superavit", "superávit", "bulking"),
}


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    normalized = text.lower()
    return any(term in normalized for term in keywords)


def validate_plan_semantic_consistency(plan: UserPlan) -> list[str]:
    """Return semantic consistency violations for a fully-typed plan."""
    issues: list[str] = []

    goal = plan.goal.primary_goal
    energy = plan.alignment.energy_strategy
    allowed_energy_by_goal = {
        "muscle_gain": {"surplus"},
        "fat_loss": {"deficit", "recomposition"},
        "recomposition": {"maintenance", "deficit", "recomposition"},
        "performance": {"maintenance", "surplus", "recomposition"},
        "health": {"maintenance", "deficit", "surplus", "recomposition"},
    }

    if energy not in allowed_energy_by_goal[goal]:
        issues.append(
            f"goal '{goal}' is inconsistent with energy_strategy '{energy}'"
        )

    summary = plan.goal.outcome_summary.strip().lower()
    forbidden_terms = _OUTCOME_FORBIDDEN_TERMS.get(goal, ())
    matched_forbidden = [term for term in forbidden_terms if term in summary]
    if matched_forbidden:
        issues.append(
            "goal.outcome_summary contradicts primary_goal "
            f"('{goal}') via terms: {', '.join(matched_forbidden)}"
        )

    phase = plan.timeline.current_phase.strip().lower()
    opposite_keywords = set()
    for goal_key, keywords in _PHASE_KEYWORDS.items():
        if goal_key != goal:
            opposite_keywords.update(keywords)
    keyword_regex = "|".join(re.escape(term) for term in opposite_keywords)
    if keyword_regex and re.search(keyword_regex, phase):
        issues.append(
            "timeline.current_phase contains goal-opposite terms for "
            f"primary_goal '{goal}'"
        )

    return issues


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_date(value: date | datetime | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    return value


def missing_discovery_fields(discovery: PlanDiscoveryState | None) -> list[str]:
    """Return the required discovery fields that are still missing."""
    if discovery is None:
        return list(DISCOVERY_FIELD_LABELS)

    missing: list[str] = []
    if discovery.goal_primary is None:
        missing.append("goal_primary")
    if not discovery.goal_summary:
        missing.append("goal_summary")
    if discovery.target_date is None:
        missing.append("target_date")
    if not discovery.training_days_available:
        missing.append("training_days_available")
    if discovery.session_duration_min is None:
        missing.append("session_duration_min")
    if discovery.constraints == []:
        missing.append("constraints")
    if discovery.preferences == []:
        missing.append("preferences")
    if discovery.available_equipment == []:
        missing.append("available_equipment")
    if not discovery.metabolism_confirmed:
        missing.append("metabolism_confirmed")
    return missing


def apply_discovery_update(
    user_email: str,
    current: PlanDiscoveryState | None,
    payload,
) -> PlanDiscoveryState:
    """Merge a discovery update into the persisted draft."""
    base = current.model_dump() if current is not None else {"user_email": user_email}
    updates = payload.model_dump(exclude_none=True)
    merged = {**base, **updates, "user_email": user_email}
    discovery = PlanDiscoveryState(**merged)
    discovery.updated_at = _utc_now()
    discovery.missing_fields = missing_discovery_fields(discovery)
    discovery.confidence = {
        field: (
            "missing"
            if field in discovery.missing_fields
            else "user_provided"
        )
        for field in DISCOVERY_FIELD_LABELS
    }
    return discovery


def build_plan_from_create_input(
    user_email: str,
    payload: PlanCreateInput,
    created_from: str = "discovery",
) -> UserPlan:
    """Build a fresh active plan from a validated create payload."""
    now = _utc_now()
    plan = UserPlan(
        user_email=user_email,
        title=payload.title,
        goal=payload.goal,
        timeline=payload.timeline,
        user_context=payload.user_context,
        training=payload.training,
        nutrition=payload.nutrition,
        alignment=payload.alignment,
        tracking=payload.tracking,
        created_from=created_from,  # type: ignore[arg-type]
        review_reason=payload.review_reason,
        data_confidence=payload.data_confidence,
        last_material_change_at=now,
        created_at=now,
        updated_at=now,
    )
    consistency_issues = validate_plan_semantic_consistency(plan)
    if consistency_issues:
        raise ValueError(
            "Plan semantic consistency validation failed: "
            + "; ".join(consistency_issues)
        )
    return plan


def merge_plan_section(plan: UserPlan, payload: PlanSectionUpdateInput) -> UserPlan:
    """Apply one or more typed section updates and return a fresh validated plan."""
    plan_dict = plan.model_dump()
    candidate_sections = CANONICAL_PLAN_SECTIONS
    updated_sections: list[str] = []
    for section in candidate_sections:
        section_payload = getattr(payload, section)
        if section_payload is None:
            continue
        plan_dict[section] = section_payload.model_dump()
        updated_sections.append(section)

    if not updated_sections:
        raise ValueError("missing section payload")

    plan_dict["updated_at"] = _utc_now()
    plan_dict["last_material_change_at"] = _utc_now()
    if payload.review_reason is not None:
        plan_dict["review_reason"] = payload.review_reason
    updated_plan = UserPlan(**plan_dict)
    consistency_issues = validate_plan_semantic_consistency(updated_plan)
    if consistency_issues:
        raise ValueError(
            "Plan semantic consistency validation failed: "
            + "; ".join(consistency_issues)
        )
    return updated_plan


def build_review_record(payload: PlanReviewInput) -> PlanReview:
    """Convert review input into a stored review object."""
    return PlanReview(
        summary=payload.summary,
        decision=payload.decision,
        changes_made=payload.changes_made,
        next_review_at=payload.next_review_at,
        evidence_summary=payload.evidence_summary,
    )


def attach_review(plan: UserPlan, review: PlanReview) -> UserPlan:
    """Append a review to the plan history and promote it to latest review."""
    plan_dict = plan.model_dump()
    history = plan.review_history + [review]
    plan_dict["review_history"] = [item.model_dump() for item in history]
    plan_dict["latest_review"] = review.model_dump()
    plan_dict["updated_at"] = _utc_now()
    return UserPlan(**plan_dict)


def build_plan_prompt_snapshot(
    plan: UserPlan | None,
    discovery: PlanDiscoveryState | None = None,
    progress: PlanProgressSnapshot | None = None,
) -> PlanPromptContext:
    """Build structured prompt context from active plan or discovery."""
    if plan is None:
        missing = missing_discovery_fields(discovery)
        return PlanPromptContext(
            status="DISCOVERY_IN_PROGRESS" if discovery else "NO_PLAN",
            discovery={
                "missing_fields": missing,
                "collected_fields": [
                    field
                    for field in DISCOVERY_FIELD_LABELS
                    if field not in missing
                ],
            },
        )

    active_plan = {
        "title": plan.title,
        "goal": plan.goal.model_dump(),
        "timeline": plan.timeline.model_dump(),
        "user_context": plan.user_context.model_dump(),
        "training": plan.training.model_dump(),
        "nutrition": plan.nutrition.model_dump(),
        "alignment": plan.alignment.model_dump(),
        "tracking": plan.tracking.model_dump(),
        "latest_review": (
            plan.latest_review.model_dump(exclude_none=True)
            if plan.latest_review
            else None
        ),
    }
    return PlanPromptContext(
        status="ACTIVE_PLAN",
        schema_version=plan.schema_version,
        active_plan=active_plan,
        progress_summary=progress.model_dump(exclude_none=True) if progress else {},
    )


def format_plan_snapshot(snapshot: PlanPromptContext) -> str:
    """Render a prompt-safe plan context block."""
    if snapshot.status != "ACTIVE_PLAN":
        missing = snapshot.discovery.get("missing_fields", [])
        missing_label = ", ".join(
            DISCOVERY_FIELD_LABELS.get(field, field) for field in missing
        )
        return (
            "PLAN_CONTEXT:\n"
            f"status: {snapshot.status}\n"
            "required_action: START_OR_CONTINUE_DISCOVERY\n"
            f"missing_fields: {missing_label or 'nenhum'}"
        )

    plan = snapshot.active_plan
    return (
        "PLAN_CONTEXT:\n"
        f"status: {snapshot.status}\n"
        f"schema_version: {snapshot.schema_version}\n"
        f"title: {plan.get('title')}\n"
        f"goal: {plan.get('goal', {}).get('outcome_summary')}\n"
        f"timeline: {plan.get('timeline', {}).get('start_date')} -> "
        f"{plan.get('timeline', {}).get('target_date')}\n"
        f"training_split: {plan.get('training', {}).get('split_name')}\n"
        f"nutrition_targets: {plan.get('nutrition', {}).get('daily_targets')}\n"
        f"latest_review: {plan.get('latest_review')}"
    )


def _derive_next_discovery_prompt(missing_fields: list[str]) -> str:
    if not missing_fields:
        return "Discovery completo. O proximo passo e criar o plano."
    next_field = missing_fields[0]
    return f"Coletar: {DISCOVERY_FIELD_LABELS.get(next_field, next_field)}."


def _find_today_training(plan: UserPlan) -> TodayTrainingView:
    today_index = datetime.now().weekday()
    today = CANONICAL_WEEKDAYS[today_index]
    item = next((entry for entry in plan.training.weekly_schedule if entry.day == today), None)
    if item is None or item.type == "off":
        return TodayTrainingView(
            day=today,
            focus="recuperacao",
            exercise_names=[],
            is_rest_day=True,
        )

    routine = next(
        (candidate for candidate in plan.training.routines if candidate.id == item.routine_id),
        None,
    )
    return TodayTrainingView(
        day=today,
        routine_name=routine.name if routine else None,
        focus=item.focus,
        exercise_names=[exercise.name for exercise in routine.exercises] if routine else [],
        is_rest_day=False,
    )


def _build_weekly_schedule(plan: UserPlan) -> list[WeeklyScheduleView]:
    today_index = datetime.now().weekday()
    today = CANONICAL_WEEKDAYS[today_index]
    routines_by_id = {routine.id: routine for routine in plan.training.routines}

    schedule_by_day = {entry.day: entry for entry in plan.training.weekly_schedule}
    schedule: list[WeeklyScheduleView] = []
    for day in CANONICAL_WEEKDAYS:
        item = schedule_by_day.get(day)
        if item is None:
            schedule.append(
                WeeklyScheduleView(
                    day=day,
                    focus="recuperacao",
                    exercise_names=[],
                    is_rest_day=True,
                    is_today=day == today,
                )
            )
            continue

        routine = routines_by_id.get(item.routine_id) if item.routine_id else None
        schedule.append(
                WeeklyScheduleView(
                    day=day,
                    routine_name=routine.name if routine else None,
                    focus=item.focus,
                    exercise_names=(
                        [exercise.name for exercise in routine.exercises]
                        if routine
                        else []
                    ),
                    is_rest_day=item.type == "off" or routine is None,
                    is_today=day == today,
                )
            )

    return schedule


def build_progress_snapshot(plan: UserPlan, database) -> PlanProgressSnapshot:
    """Compute a pragmatic progress snapshot from the data already stored."""
    workouts = database.get_workout_logs(plan.user_email, limit=30)
    nutrition_stats = database.get_nutrition_stats(plan.user_email)
    weight_logs = database.get_weight_logs(plan.user_email, limit=30)

    if workouts:
        training_metric = ProgressMetric(
            status="on_track" if len(workouts) >= 1 else "insufficient_data",
            details=f"{len(workouts)} treino(s) registrado(s) recentemente.",
        )
        progression_status = "maintaining"
    else:
        training_metric = ProgressMetric(
            status="insufficient_data",
            details="Sem treinos registrados recentemente.",
        )
        progression_status = "insufficient_data"

    if nutrition_stats.total_logs > 0:
        nutrition_metric = ProgressMetric(
            status="on_track",
            details=f"{nutrition_stats.total_logs} log(s) nutricionais registrados.",
        )
    else:
        nutrition_metric = ProgressMetric(
            status="insufficient_data",
            details="Sem logs nutricionais suficientes.",
        )

    body_trend_status = "aligned" if len(weight_logs) >= 2 else "insufficient_data"

    conflicts: list[PlanConflict] = []
    if plan.goal.primary_goal == "muscle_gain" and plan.alignment.energy_strategy == "deficit":
        conflicts.append(
            PlanConflict(
                kind="goal_energy_mismatch",
                message="Objetivo de ganho muscular conflita com estrategia energetica em deficit.",
            )
        )
    if (
        plan.goal.primary_goal == "fat_loss"
        and plan.alignment.energy_strategy == "surplus"
    ):
        conflicts.append(
            PlanConflict(
                kind="goal_energy_mismatch",
                message=(
                    "Objetivo de perda de gordura conflita com estrategia "
                    "energetica em superavit."
                ),
            )
        )

    evidence_summary = [training_metric.details, nutrition_metric.details]
    if len(weight_logs) < 2:
        evidence_summary.append("Sem historico corporal suficiente para avaliar tendencia.")

    return PlanProgressSnapshot(
        plan_id=plan.id or "active-plan",
        training_adherence=training_metric,
        nutrition_adherence=nutrition_metric,
        progression_status=progression_status,
        body_trend_status=body_trend_status,  # type: ignore[arg-type]
        conflicts=conflicts,
        recommended_review=bool(conflicts),
        evidence_summary=evidence_summary,
    )


def build_plan_view_model(
    plan: UserPlan | None,
    discovery: PlanDiscoveryState | None,
    progress: PlanProgressSnapshot | None = None,
) -> PlanViewModel:
    """Build the view model consumed by the plan tab."""
    if plan is None:
        missing = missing_discovery_fields(discovery)
        collected = [
            field for field in DISCOVERY_FIELD_LABELS if field not in missing
        ]
        return PlanViewModel(
            status="DISCOVERY_IN_PROGRESS" if discovery else "NO_PLAN",
            generic_response_notice=(
                "Sem plano ativo, a IA deve tratar qualquer orientacao como generica "
                "e conduzir discovery ate conseguir criar um plano real."
            ),
            discovery=DiscoveryView(
                missing_fields=missing,
                collected_fields=collected,
                next_prompt=_derive_next_discovery_prompt(missing),
            ),
            progress=None,
            active_plan=None,
        )

    latest_review_summary = plan.latest_review.summary if plan.latest_review else None
    success_metrics = [
        f"{metric.metric_name}: {metric.target_value} {metric.unit}".strip()
        for metric in plan.goal.success_metrics
    ]
    next_review_at = (
        plan.latest_review.next_review_at
        if plan.latest_review and plan.latest_review.next_review_at
        else _ensure_date(plan.created_at)
    )
    return PlanViewModel(
        status="ACTIVE_PLAN",
        generic_response_notice=(
            "Plano ativo no sistema. Use este plano como fonte primaria."
        ),
        active_plan=ActivePlanView(
            title=plan.title,
            goal_summary=plan.goal.outcome_summary,
            success_metrics=success_metrics,
            training_split=plan.training.split_name,
            weekly_schedule=_build_weekly_schedule(plan),
            today_training=_find_today_training(plan),
            nutrition_targets=plan.nutrition.daily_targets,
            current_risks=plan.alignment.recovery_assumptions,
            next_review_at=next_review_at,
            latest_review_summary=latest_review_summary,
        ),
        discovery=None,
        progress=progress,
    )
