"""Plan domain service helpers for prompt context and orchestration."""

from datetime import datetime, timedelta

from src.api.models.plan import (
    ActivePlan,
    PlanProposalInput,
    PlanSnapshot,
    PlanSnapshotAdherence7D,
    PlanSnapshotExerciseContext,
    PlanSnapshotWeightTrend,
    PlanStatus,
)

REQUIRED_INTAKE_FIELDS = (
    "dias_disponiveis_treino",
    "frequencia_treino_semana",
    "nivel_treinamento",
    "restricoes_lesoes",
    "tempo_por_sessao_min",
    "preferencia_ambiente",
)


def missing_intake_fields(strategy: dict) -> list[str]:
    """Return missing mandatory discovery fields required for plan creation."""
    return [field for field in REQUIRED_INTAKE_FIELDS if field not in strategy]


def missing_execution_fields(execution: dict) -> list[str]:
    """Return missing mandatory execution blocks required for an actionable plan."""
    def has_exercises(training_payload: object) -> bool:
        if not isinstance(training_payload, dict):
            return False
        session = training_payload.get("session")
        if isinstance(session, dict) and isinstance(session.get("exercises"), list):
            return len(session["exercises"]) > 0
        if isinstance(training_payload.get("exercises"), list):
            return len(training_payload["exercises"]) > 0
        return False

    missing: list[str] = []
    if not execution.get("today_training"):
        missing.append("today_training")
    if not execution.get("today_nutrition"):
        missing.append("today_nutrition")
    upcoming_days = execution.get("upcoming_days")
    if not upcoming_days:
        missing.append("upcoming_days")
    today_training = execution.get("today_training")
    if not has_exercises(today_training):
        missing.append("training_exercises")
    planned_days_missing_details = False
    if isinstance(upcoming_days, list):
        for day in upcoming_days:
            if not isinstance(day, dict):
                planned_days_missing_details = True
                break
            status = day.get("status")
            if status == "rest":
                continue
            if not has_exercises(day.get("training")):
                planned_days_missing_details = True
                break
    if planned_days_missing_details:
        missing.append("upcoming_training_exercises")
    return missing


def _normalize_execution_defaults(execution_data: dict) -> tuple[dict, dict, list]:
    """Guarantee minimum operational payload for mission-first UI."""
    today_training = execution_data.get("today_training")
    if not today_training:
        today_training = {"title": "Definir treino de hoje no chat"}

    today_nutrition = execution_data.get("today_nutrition")
    if not today_nutrition:
        today_nutrition = {"summary": "Definir metas de nutricao de hoje no chat"}

    upcoming_days = execution_data.get("upcoming_days")
    if not upcoming_days:
        upcoming_days = [
            "Amanha: revisar missao com a IA",
            "Dia 2: manter consistencia de treino e proteina",
            "Dia 3: novo check-in rapido no chat",
        ]

    return today_training, today_nutrition, upcoming_days


def _merge_plan_sections(
    latest_plan: ActivePlan | None,
    payload: PlanProposalInput,
) -> tuple[dict, dict, dict]:
    base_strategy = latest_plan.strategy.model_dump() if latest_plan else {}
    base_execution = latest_plan.execution.model_dump() if latest_plan else {}
    base_tracking = latest_plan.tracking.model_dump() if latest_plan else {}
    strategy_data = {**base_strategy, **payload.strategy}
    execution_data = {**base_execution, **payload.execution}
    tracking_data = {**base_tracking, **payload.tracking}
    return strategy_data, execution_data, tracking_data


def build_next_plan_version(
    user_email: str,
    latest_plan: ActivePlan | None,
    payload: PlanProposalInput,
) -> ActivePlan:
    """Builds the next active plan version payload."""
    now = datetime.now()
    version = 1
    strategy_data, execution_data, tracking_data = _merge_plan_sections(
        latest_plan, payload
    )

    start_date = latest_plan.start_date if latest_plan else now
    if latest_plan and latest_plan.end_date > latest_plan.start_date:
        end_date = latest_plan.end_date
    else:
        end_date = start_date + timedelta(days=27)

    today_training, today_nutrition, upcoming_days = _normalize_execution_defaults(
        execution_data
    )

    return ActivePlan(
        user_email=user_email,
        status=PlanStatus.ACTIVE,
        title=payload.title,
        objective_summary=payload.objective_summary,
        start_date=start_date,
        end_date=end_date,
        version=version,
        strategy={
            "primary_goal": strategy_data.get("primary_goal", "unspecified"),
            "success_criteria": strategy_data.get("success_criteria", []),
            "constraints": strategy_data.get("constraints", []),
            "coaching_rationale": strategy_data.get(
                "coaching_rationale", "generated by ai"
            ),
            "adaptation_policy": strategy_data.get(
                "adaptation_policy", "ai_managed_continuous"
            ),
        },
        execution={
            "today_training": today_training,
            "today_nutrition": today_nutrition,
            "upcoming_days": upcoming_days,
            "active_focus": execution_data.get("active_focus", "consistencia"),
            "current_risks": execution_data.get("current_risks", []),
            "pending_changes": execution_data.get("pending_changes", []),
        },
        tracking={
            "checkpoints": tracking_data.get("checkpoints", []),
            "adherence_snapshot": tracking_data.get("adherence_snapshot", {}),
            "progress_snapshot": tracking_data.get("progress_snapshot", {}),
            "last_ai_assessment": tracking_data.get("last_ai_assessment"),
            "last_user_acknowledgement": tracking_data.get(
                "last_user_acknowledgement"
            ),
        },
        governance={
            "change_reason": payload.change_reason,
            "approval_request": None,
        },
    )


def _extract_today_training(execution: dict) -> str:
    training = execution.get("today_training", {})
    if isinstance(training, dict):
        return str(training.get("title") or training.get("summary") or "Nao definido")
    return str(training) if training else "Nao definido"


def _extract_today_nutrition(execution: dict) -> str:
    nutrition = execution.get("today_nutrition", {})
    if isinstance(nutrition, dict):
        calories = nutrition.get("calories")
        protein = nutrition.get("protein_target")
        if calories is not None or protein is not None:
            return f"{calories or '-'} kcal / {protein or '-'}g proteina"
    return str(nutrition) if nutrition else "Nao definido"


def build_plan_prompt_snapshot(
    plan: ActivePlan | None,
    *,
    today_training_context: list[PlanSnapshotExerciseContext] | None = None,
    adherence_7d: PlanSnapshotAdherence7D | None = None,
    weight_trend_weekly: PlanSnapshotWeightTrend | None = None,
) -> PlanSnapshot | None:
    """Builds a compact snapshot from active plan payload."""
    if plan is None:
        return None

    checkpoints = plan.tracking.checkpoints
    last_checkpoint = checkpoints[-1].summary if checkpoints else None
    pending_adjustment = None
    if plan.governance.approval_request is not None:
        pending_adjustment = plan.governance.approval_request.summary

    return PlanSnapshot(
        title=plan.title,
        objective_summary=plan.objective_summary,
        plan_period=(
            f"{plan.start_date.strftime('%Y-%m-%d')} a "
            f"{plan.end_date.strftime('%Y-%m-%d')}"
        ),
        status=plan.status.value,
        active_focus=plan.execution.active_focus,
        today_training=_extract_today_training(plan.execution.model_dump()),
        today_nutrition=_extract_today_nutrition(plan.execution.model_dump()),
        upcoming_days=[str(item) for item in plan.execution.upcoming_days],
        today_training_context=today_training_context or [],
        adherence_7d=adherence_7d,
        weight_trend_weekly=weight_trend_weekly,
        last_checkpoint_summary=last_checkpoint,
        critical_constraints=plan.strategy.constraints,
        pending_adjustment=pending_adjustment,
    )


def format_plan_snapshot(snapshot: PlanSnapshot | None) -> str:
    """Formats plan snapshot as a readable prompt block."""
    if snapshot is None:
        return (
            "Nenhum plano ativo registrado.\n"
            "Acao obrigatoria: conduza discovery com o aluno e insista na coleta dos "
            "dados faltantes ate conseguir criar um plano completo de treino e nutricao."
        )

    upcoming = ", ".join(snapshot.upcoming_days) if snapshot.upcoming_days else "sem previsao"
    constraints = (
        ", ".join(snapshot.critical_constraints)
        if snapshot.critical_constraints
        else "sem restricoes criticas"
    )
    checkpoint = snapshot.last_checkpoint_summary or "sem checkpoint recente"
    pending = snapshot.pending_adjustment or "nenhum"
    training_context_lines: list[str] = []
    if snapshot.today_training_context:
        training_context_lines.append("Contexto do treino de hoje:")
        for item in snapshot.today_training_context:
            prescription = f"{item.prescribed_sets or '-'}x{item.prescribed_reps or '-'}"
            if item.last_load_kg is not None and item.last_performed_at:
                training_context_lines.append(
                    f"- {item.exercise_name}: {prescription} | ultima carga registrada "
                    f"{item.last_load_kg:.0f} kg em {item.last_performed_at}"
                )
            else:
                training_context_lines.append(
                    f"- {item.exercise_name}: {prescription} | ultima carga registrada: indisponivel"
                )

    adherence_line = ""
    if snapshot.adherence_7d is not None:
        training_pct = (
            "indisponivel"
            if snapshot.adherence_7d.training_percent is None
            else f"{snapshot.adherence_7d.training_percent}%"
        )
        nutrition_pct = (
            "indisponivel"
            if snapshot.adherence_7d.nutrition_percent is None
            else f"{snapshot.adherence_7d.nutrition_percent}%"
        )
        adherence_line = f"Aderencia 7d: treino {training_pct} | nutricao {nutrition_pct}"

    trend_line = ""
    if snapshot.weight_trend_weekly is not None:
        trend_line = (
            "Tendencia de peso: "
            f"{snapshot.weight_trend_weekly.value_kg_per_week:+.2f} kg/semana"
        )

    enriched_sections = ""
    if training_context_lines:
        enriched_sections += "\\n".join(training_context_lines)
    if adherence_line:
        enriched_sections += f"\\n{adherence_line}"
    if trend_line:
        enriched_sections += f"\\n{trend_line}"

    return (
        f"Plano ativo: {snapshot.title}\\n"
        f"Objetivo: {snapshot.objective_summary}\\n"
        f"Periodo do plano: {snapshot.plan_period}\\n"
        f"Status: {snapshot.status}\\n"
        f"Foco atual: {snapshot.active_focus}\\n"
        f"Treino de hoje: {snapshot.today_training}\\n"
        f"{f'{enriched_sections}\\n' if enriched_sections else ''}"
        f"Nutricao de hoje: {snapshot.today_nutrition}\\n"
        f"Proximos dias: {upcoming}\\n"
        f"Ultimo checkpoint: {checkpoint}\\n"
        f"Restricoes criticas: {constraints}\\n"
        f"Ajuste pendente: {pending}"
    )
