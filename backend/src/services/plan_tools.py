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
)


class ApprovePlanInput(BaseModel):
    """Input schema for plan approval tool."""

    version: int = Field(..., ge=1)


class ProposeAdjustmentInput(BaseModel):
    """Input schema for quick adjustment proposals."""

    change_reason: str = Field(..., min_length=1)
    proposal_summary: str = Field(..., min_length=1)


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
        snapshot = build_plan_prompt_snapshot(plan)
        if snapshot is None:
            return "Nenhum plano ativo encontrado."
        return format_plan_snapshot(snapshot)

    return get_plan_prompt_snapshot


def create_create_plan_proposal_tool(database, user_email: str):
    """Creates a new plan proposal version awaiting user approval."""

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
        """Cria uma nova proposta de plano aguardando aprovacao do usuario."""
        latest = database.get_latest_plan(user_email)
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
        return f"Proposta de plano criada com sucesso (ID: {plan_id}, versao {plan.version})."

    return create_plan_proposal


def create_propose_plan_adjustment_tool(database, user_email: str):
    """Creates an adjustment proposal using current plan as baseline."""

    @tool(args_schema=ProposeAdjustmentInput)
    def propose_plan_adjustment(change_reason: str, proposal_summary: str) -> str:
        """Propõe ajuste com base no plano mais recente e pede aprovacao."""
        latest = database.get_latest_plan(user_email)
        if latest is None:
            return "Nao existe plano para ajustar. Crie uma proposta inicial primeiro."

        proposal = PlanProposalInput(
            title=latest.title,
            objective_summary=latest.objective_summary,
            change_reason=change_reason,
            strategy={},
            execution={
                "pending_changes": [
                    {
                        "reason": change_reason,
                        "summary": proposal_summary,
                    }
                ]
            },
            tracking={},
        )
        new_plan = build_next_plan_version(
            user_email=user_email,
            latest_plan=latest,
            payload=proposal,
            approval_summary=proposal_summary,
        )
        plan_id = database.save_plan(new_plan)
        return (
            "Ajuste proposto. Aguardando aprovacao do usuario "
            f"(ID: {plan_id}, versao {new_plan.version})."
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
