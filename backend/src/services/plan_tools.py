"""LangChain tools for central plan management."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.api.models.plan import (
    PlanProposalInput,
)
from src.services.plan_service import (
    build_next_plan_version,
    build_plan_prompt_snapshot,
    format_plan_snapshot,
    missing_intake_fields,
    missing_execution_fields,
)
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.services.plan_snapshot_context import build_plan_snapshot_context


class ApprovePlanInput(BaseModel):
    """Input schema for plan approval tool."""

    version: int = Field(..., ge=1)


class ProposeAdjustmentInput(BaseModel):
    """Input schema for quick adjustment proposals."""

    change_reason: str = Field(..., min_length=1)
    proposal_summary: str = Field(..., min_length=1)


def create_plan_help_tool(_database, _user_email: str):
    """Provides operational contract for plan creation tools."""

    @tool
    def plan_help() -> str:
        """Retorna guia de como montar e ajustar plano com as tools de plano."""
        return (
            "# Plan Tools Help\n\n"
            "## Fluxo obrigatorio\n"
            "discovery -> criacao/edicao direta -> acompanhamento continuo\n\n"
            "## Regras\n"
            "- Nao chamar create_plan_proposal com intake incompleto.\n"
            "- Fazer perguntas de discovery ate preencher todos os campos obrigatorios.\n"
            "- Nao criar plano sem prescricao operacional de treino/nutricao.\n"
            "- Nao pedir aprovacao nem proposta para criar/editar plano.\n"
            "- O plano e unico por usuario: editar sempre sobrescreve o plano atual.\n\n"
            "## Campos obrigatorios em strategy\n"
            "- dias_disponiveis_treino\n"
            "- frequencia_treino_semana\n"
            "- nivel_treinamento\n"
            "- restricoes_lesoes\n"
            "- tempo_por_sessao_min\n"
            "- preferencia_ambiente\n\n"
            "## Campos obrigatorios em execution\n"
            "- today_training (com session.exercises detalhado)\n"
            "- today_nutrition (metas objetivas)\n"
            "- upcoming_days (com proximos dias reais)\n\n"
            "- cada dia planned/adjusted em upcoming_days deve incluir\n"
            "  training.session.exercises\n\n"
            "## Exemplo minimo de execution\n"
            "```json\n"
            "{\n"
            '  "today_training": {"title": "Lower A", "session": {"exercises": ['
            '{"name":"Agachamento","sets":4,"reps":"6-8","load_guidance":"RPE 8"}]}},\n'
            '  "today_nutrition": {"calories": 2400, "protein_target": 140, '
            '"carbs_target": 260, "fat_target": 70},\n'
            '  "upcoming_days": [{"date":"2026-04-20","label":"Amanha",'
            '"training":"Upper A","nutrition":"2400 kcal","status":"planned"}]\n'
            "}\n"
            "```\n\n"
            "## Ferramentas recomendadas\n"
            "- get_active_plan\n"
            "- get_plan_prompt_snapshot\n"
            "- create_plan_proposal\n"
            "- propose_plan_adjustment\n"
            "- get_today_plan_brief\n"
        )

    return plan_help


def create_get_active_plan_tool(database, user_email: str):
    """Returns the full active plan payload."""

    @tool
    def get_active_plan() -> str:
        """Retorna o plano ativo atual do usuario em formato serializado."""
        plan = database.get_active_plan(user_email)
        if plan is None:
            return "Nenhum plano ativo encontrado."
        return str(plan.model_dump())

    return get_active_plan


def create_get_plan_prompt_snapshot_tool(database, user_email: str):
    """Returns the compact prompt snapshot generated from active plan."""

    @tool
    def get_plan_prompt_snapshot() -> str:
        """Retorna o snapshot compacto de plano usado no contexto do prompt."""
        plan = database.get_active_plan(user_email)
        if plan is None:
            return "Nenhum plano ativo encontrado."
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

    return get_plan_prompt_snapshot


def create_create_plan_proposal_tool(database, user_email: str):
    """Creates a new active plan version immediately."""

    @tool(args_schema=PlanProposalInput)
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def create_plan_proposal(
        title: str,
        objective_summary: str,
        change_reason: str,
        strategy: dict,
        execution: dict,
        tracking: dict,
    ) -> str:
        """Cria uma nova versao ativa de plano com dados completos."""
        latest = database.get_latest_plan(user_email)
        merged_strategy = (
            {**latest.strategy.model_dump(), **strategy} if latest else strategy
        )
        merged_execution = (
            {**latest.execution.model_dump(), **execution} if latest else execution
        )
        missing_strategy_fields = missing_intake_fields(merged_strategy)
        missing_exec_fields = missing_execution_fields(merged_execution)
        if missing_strategy_fields or missing_exec_fields:
            missing_list = ", ".join(missing_strategy_fields + missing_exec_fields)
            return (
                "Plano incompleto. Antes de criar proposta, colete estes campos: "
                f"{missing_list}."
            )

        proposal = PlanProposalInput(
            title=title,
            objective_summary=objective_summary,
            change_reason=change_reason,
            strategy=strategy,
            execution=execution,
            tracking=tracking,
        )
        plan = build_next_plan_version(user_email, latest, proposal)
        plan_id = database.save_plan(plan)
        return (
            "Plano criado/atualizado com sucesso (sem aprovacao necessaria). "
            f"ID: {plan_id}."
        )

    return create_plan_proposal


def create_propose_plan_adjustment_tool(database, user_email: str):
    """Creates an adjustment proposal using current plan as baseline."""

    @tool(args_schema=ProposeAdjustmentInput)
    def propose_plan_adjustment(change_reason: str, proposal_summary: str) -> str:
        """Propõe ajuste com base no plano mais recente e aplica nova versao ativa."""
        latest = database.get_latest_plan(user_email)
        if latest is None:
            return "Nao existe plano para ajustar. Crie um plano inicial primeiro."
        _ = (change_reason, proposal_summary)
        return (
            "Para ajustar o plano, use create_plan_proposal com payload estruturado "
            "(strategy/execution/tracking) contendo as alteracoes completas. "
            "Nao existe fluxo de aprovacao."
        )

    return propose_plan_adjustment


def create_approve_plan_change_tool(database, user_email: str):
    """Approves a previously proposed version."""

    @tool(args_schema=ApprovePlanInput)
    def approve_plan_change(version: int) -> str:
        approved = database.approve_plan(user_email, version)
        if not approved:
            return "Nao foi possivel aprovar a versao informada."
        return f"Plano aprovado com sucesso. Versao {version} agora esta ativa."

    return approve_plan_change


def create_get_today_plan_brief_tool(database, user_email: str):
    """Returns a concise mission-of-the-day briefing from active plan."""

    @tool
    def get_today_plan_brief() -> str:
        """Retorna o resumo operacional do dia do plano ativo."""
        plan = database.get_active_plan(user_email)
        snapshot = build_plan_prompt_snapshot(plan)
        if snapshot is None:
            return "Nenhum plano ativo encontrado."
        return (
            f"Missao de hoje - Treino: {snapshot.today_training}. "
            f"Nutricao: {snapshot.today_nutrition}. "
            f"Foco: {snapshot.active_focus}."
        )

    return get_today_plan_brief
