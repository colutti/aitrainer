"""LangChain tools for singleton central plan management."""

import hashlib
import json
from textwrap import dedent

from langchain_core.tools import tool

from src.api.models.plan import PlanUpsertInput
from src.core.logs import logger
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.services.plan_service import (
    build_plan_prompt_snapshot,
    build_plan_singleton,
    format_plan_snapshot,
    missing_execution_fields,
)
from src.services.plan_snapshot_context import build_plan_snapshot_context


def _minimum_upsert_payload_template() -> str:
    """Return a compact JSON template that LLM can copy to call upsert_plan once."""
    return dedent(
        """\
        {
          "title": "Plano <objetivo principal>",
          "objective_summary": "Resumo em 1 frase do objetivo e estrategia",
          "change_reason": "initial_plan",
          "strategy": {
            "primary_goal": "<ex.: lose_fat|gain_muscle|maintain>"
          },
          "execution": {
            "today_training": {
              "title": "Treino de hoje",
              "session": {
                "exercises": [
                  {
                    "name": "Exercicio 1",
                    "sets": 3,
                    "reps": "8-12",
                    "load_guidance": "RPE 7-8"
                  }
                ]
              }
            },
            "today_nutrition": {
              "calories": 2300,
              "protein_target": 150
            },
            "active_focus": "consistencia"
          },
          "checkpoints": []
        }"""
    )


def create_plan_help_tool(_database, _user_email: str):
    """Provides operational contract for singleton plan tools."""

    @tool
    def plan_help() -> str:
        """Retorna guia de como montar e ajustar plano singleton."""
        return (
            "# Plan Tools Help\n\n"
            "## Fluxo obrigatorio\n"
            "discovery objetivo -> montar payload completo -> 1 chamada upsert_plan\n\n"
            "## Regras\n"
            "- Em criacao inicial, use payload minimo completo e chame upsert_plan uma vez.\n"
            "- Sempre atualizar o singleton existente quando houver novos dados.\n"
            "- Nao repetir upsert_plan no mesmo turno apos retorno de erro.\n"
            "- O plano e singleton: sempre atualizar o mesmo plano do usuario.\n\n"
            "## Payload minimo recomendado (copiar e preencher)\n"
            f"{_minimum_upsert_payload_template()}\n\n"
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
    call_count = 0
    last_payload_hash: str | None = None

    def _run_loop_guards(payload_for_hash: dict) -> str | None:
        nonlocal call_count, last_payload_hash
        call_count += 1
        payload_hash = hashlib.sha256(
            json.dumps(payload_for_hash, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

        if call_count > 3:
            logger.warning(
                "upsert_plan loop guard triggered for user %s after %s calls",
                user_email,
                call_count,
            )
            return (
                "ERRO_UPSERT_PLAN_LOOP_GUARD: upsert_plan foi chamado muitas vezes no "
                "mesmo turno. Nao tente novamente agora; responda ao usuario com status "
                "atual e prossiga com perguntas objetivas para completar dados faltantes."
            )
        if last_payload_hash == payload_hash:
            logger.warning("upsert_plan duplicate payload for user %s", user_email)
            return (
                "ERRO_UPSERT_PLAN_REPETIDO: payload duplicado no mesmo turno. "
                "Nao repetir a chamada agora; peça apenas os dados faltantes."
            )
        last_payload_hash = payload_hash
        return None

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
        """Cria/atualiza o plano singleton.

        Contrato recomendado para criacao inicial em 1 chamada:
        - Preencha title, objective_summary, change_reason.
        - Em execution, inclua obrigatoriamente:
          execution.today_training.session.exercises (>=1 exercicio)
          execution.today_nutrition
        - Campos opcionais que melhoram qualidade: strategy.primary_goal, execution.active_focus.
        """
        logger.info("upsert_plan called for user: %s", user_email)
        guard_error = _run_loop_guards(
            {
            "title": title,
            "objective_summary": objective_summary,
            "change_reason": change_reason,
            "strategy": strategy,
            "execution": execution,
            "checkpoints": checkpoints or [],
            }
        )
        if guard_error:
            return guard_error

        latest = database.get_latest_plan(user_email)
        if latest is None:
            missing_fields = missing_execution_fields(execution)
            if missing_fields:
                return (
                    "ERRO_UPSERT_PLAN_INCOMPLETO: "
                    "Plano incompleto para criacao inicial. "
                    "Colete e envie estes campos antes de salvar: "
                    f"{', '.join(missing_fields)}. "
                    "Use este payload minimo e chame upsert_plan apenas uma vez no "
                    "proximo turno:\n"
                    f"{_minimum_upsert_payload_template()}\n"
                    "Nao repetir upsert_plan no mesmo turno; primeiro coletar os dados "
                    "faltantes com o usuario."
                )

        payload = PlanUpsertInput(
            title=title,
            objective_summary=objective_summary,
            change_reason=change_reason,
            strategy=strategy,
            execution=execution,
            checkpoints=checkpoints or [],
        )
        try:
            plan = build_plan_singleton(user_email, latest, payload)
            plan_id = database.save_plan(plan)
            logger.info("upsert_plan saved for user: %s (plan_id=%s)", user_email, plan_id)
            return f"SUCESSO_UPSERT_PLAN: Plano salvo com sucesso. ID: {plan_id}."
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error(
                "upsert_plan failed for user %s: %s",
                user_email,
                exc,
                exc_info=True,
            )
            return (
                "ERRO_UPSERT_PLAN_PERSISTENCIA: falha ao salvar no banco. "
                "Tente novamente apos revisar os dados."
            )

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
