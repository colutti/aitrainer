"""LangChain tools for singleton central plan management."""

from langchain_core.tools import tool

from src.api.models.plan import PlanUpsertInput
from src.core.logs import logger
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.services.plan_service import (
    build_plan_prompt_snapshot,
    build_plan_singleton,
    format_plan_snapshot,
    missing_execution_fields,
    missing_intake_fields,
)
from src.services.plan_snapshot_context import build_plan_snapshot_context


def create_plan_help_tool(_database, _user_email: str):
    """Provides operational contract for singleton plan tools."""

    @tool
    def plan_help() -> str:
        """Retorna guia de como montar e ajustar plano singleton."""
        return (
            "# Plan Tools Help\n\n"
            "## Fluxo obrigatorio\n"
            "discovery -> criar plano -> atualizar continuamente\n\n"
            "## Regras\n"
            "- Em criacao inicial, upsert_plan exige plano operacional completo.\n"
            "- Sempre atualizar o singleton existente quando houver novos dados.\n"
            "- O plano e singleton: sempre atualizar o mesmo plano do usuario.\n\n"
            "## Ferramentas\n"
            "- get_plan\n"
            "- get_plan_context\n"
            "- upsert_plan\n"
            "- get_today_plan_brief\n"
        )

    return plan_help


def create_get_plan_tool(database, user_email: str):
    """Returns the full singleton plan payload."""

    @tool
    def get_plan() -> str:
        """Retorna o plano atual do usuario em formato serializado."""
        plan = database.get_plan(user_email)
        if plan is None:
            return "Nenhum plano registrado."
        return str(plan.model_dump())

    return get_plan


def create_get_plan_context_tool(database, user_email: str):
    """Returns the compact context generated from singleton plan."""

    @tool
    def get_plan_context() -> str:
        """Retorna o contexto compacto de plano usado no prompt."""
        plan = database.get_plan(user_email)
        if plan is None:
            return "Nenhum plano registrado."
        metabolism_data = AdaptiveTDEEService(database).calculate_tdee(user_email)
        context = build_plan_snapshot_context(
            database=database,
            user_email=user_email,
            plan=plan,
            metabolism_data=metabolism_data,
        )
        snapshot = build_plan_prompt_snapshot(
            plan,
            today_training_context=context.today_training_context,
            adherence_7d=context.adherence_7d,
            weight_trend_weekly=context.weight_trend_weekly,
        )
        return format_plan_snapshot(snapshot)

    return get_plan_context


def create_upsert_plan_tool(database, user_email: str):
    """Creates or updates singleton plan."""

    @tool(args_schema=PlanUpsertInput)
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def upsert_plan(
        title: str,
        objective_summary: str,
        change_reason: str,
        strategy: dict,
        execution: dict,
        checkpoints: list[dict] | None = None,
    ) -> str:
        """Cria ou atualiza o plano singleton com dados completos."""
        logger.info("upsert_plan called for user: %s", user_email)
        latest = database.get_latest_plan(user_email)
        is_creation = latest is None

        if is_creation:
            missing_fields = missing_intake_fields(strategy) + missing_execution_fields(
                execution
            )
            if missing_fields:
                missing_list = ", ".join(missing_fields)
                return (
                    "Plano incompleto para criacao inicial. "
                    "Colete e envie estes campos antes de salvar: "
                    f"{missing_list}."
                )

        payload = PlanUpsertInput(
            title=title,
            objective_summary=objective_summary,
            change_reason=change_reason,
            strategy=strategy,
            execution=execution,
            checkpoints=checkpoints or [],
        )
        plan = build_plan_singleton(user_email, latest, payload)
        plan_id = database.save_plan(plan)
        logger.info("upsert_plan saved for user: %s (plan_id=%s)", user_email, plan_id)
        return f"Plano salvo com sucesso. ID: {plan_id}."

    return upsert_plan


def create_get_today_plan_brief_tool(database, user_email: str):
    """Returns a concise mission-of-the-day briefing from singleton plan."""

    @tool
    def get_today_plan_brief() -> str:
        """Retorna o resumo operacional do dia do plano."""
        plan = database.get_plan(user_email)
        snapshot = build_plan_prompt_snapshot(plan)
        if snapshot is None:
            return "Nenhum plano registrado."
        return (
            f"Missao de hoje - Treino: {snapshot.today_training}. "
            f"Nutricao: {snapshot.today_nutrition}. "
            f"Foco: {snapshot.active_focus}."
        )

    return get_today_plan_brief
