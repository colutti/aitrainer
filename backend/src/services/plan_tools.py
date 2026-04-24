"""LangChain tools for singleton master plan management."""

import hashlib
import json
from textwrap import dedent

from langchain_core.tools import tool
from pydantic import ValidationError

from src.api.models.plan import PlanUpsertInput
from src.core.logs import logger
from src.services.plan_service import (
    build_plan_singleton,
    format_plan_snapshot,
    build_plan_prompt_snapshot,
    missing_master_plan_fields,
)


def _minimum_upsert_payload_template() -> str:
    return dedent(
        """\
        {
          "title": "Plano Mestre Recomp",
          "change_reason": "initial_plan",
          "goal": {
            "primary": "lose_fat",
            "objective_summary": "Chegar a 15% de gordura corporal ate o verao",
            "success_criteria": ["aderencia >= 80%", "perda de gordura sustentavel"]
          },
          "timeline": {
            "target_date": "2026-09-01T00:00:00",
            "review_cadence": "quinzenal"
          },
          "strategy": {
            "rationale": "Deficit moderado com progressao de forca",
            "adaptation_policy": "ajustes por evidencia",
            "constraints": [],
            "preferences": [],
            "current_risks": []
          },
          "nutrition_strategy": {
            "daily_targets": {
              "calories": 2200,
              "protein_g": 180,
              "carbs_g": 200,
              "fat_g": 70
            },
            "adherence_notes": []
          },
          "training_program": {
            "split_name": "push_pull_legs",
            "frequency_per_week": 5,
            "session_duration_min": 60,
            "routines": [
              {
                "id": "push_a",
                "name": "Push A",
                "exercises": [
                  {
                    "name": "Supino reto",
                    "sets": 4,
                    "reps": "6-8",
                    "load_guidance": "RPE 8"
                  }
                ]
              }
            ],
            "weekly_schedule": [
              {"day": "monday", "routine_id": "push_a", "focus": "push", "type": "training"}
            ]
          },
          "current_summary": {
            "active_focus": "consistencia",
            "rationale": "executar bloco base por 2 semanas",
            "key_risks": [],
            "last_review": null,
            "next_review": "2026-09-15"
          },
          "checkpoints": []
        }"""
    )


def create_plan_help_tool(_database, _user_email: str):
    """Provides operational contract for singleton plan tools."""

    @tool
    def plan_help() -> str:
        """Retorna guia de como montar e ajustar plano mestre singleton."""
        return (
            "# Plan Tools Help\n\n"
            "## Fluxo obrigatorio\n"
            "discovery objetivo+prazo -> montar payload completo -> 1 chamada upsert_plan\n\n"
            "## Regras\n"
            "- Plano e singleton sobrescrito por usuario.\n"
            "- Criacao inicial exige objetivo, estrategia, metas nutricionais e programa semanal.\n"
            "- Nao repetir upsert_plan com payload igual no mesmo turno.\n\n"
            "## Payload minimo recomendado\n"
            f"{_minimum_upsert_payload_template()}\n\n"
            "## Ferramentas\n"
            "- get_plan\n"
            "- upsert_plan\n"
            "- plan_help\n"
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
            return (
                "ERRO_UPSERT_PLAN_LOOP_GUARD: upsert_plan foi chamado muitas vezes no "
                "mesmo turno. PLANO_NAO_SALVO. Nao afirme que salvou/ativou o plano. "
                "Nao tente novamente agora; retome no proximo turno com 1 unica chamada."
            )
        if last_payload_hash == payload_hash:
            return (
                "ERRO_UPSERT_PLAN_REPETIDO: payload duplicado no mesmo turno. "
                "PLANO_NAO_SALVO. Nao afirme que salvou/ativou o plano. "
                "Nao repetir a chamada agora."
            )
        last_payload_hash = payload_hash
        return None

    @tool(args_schema=PlanUpsertInput)
    # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    def upsert_plan(
        title: str,
        change_reason: str,
        goal: dict,
        timeline: dict,
        strategy: dict,
        nutrition_strategy: dict,
        training_program: dict,
        current_summary: dict,
        checkpoints: list[dict] | None = None,
    ) -> str:
        """Cria/atualiza o plano mestre singleton com payload completo."""
        logger.info("upsert_plan called for user: %s", user_email)
        payload_hash_source = {
            "title": title,
            "change_reason": change_reason,
            "goal": goal,
            "timeline": timeline,
            "strategy": strategy,
            "nutrition_strategy": nutrition_strategy,
            "training_program": training_program,
            "current_summary": current_summary,
            "checkpoints": checkpoints or [],
        }
        guard_error = _run_loop_guards(payload_hash_source)
        if guard_error:
            return guard_error

        payload = PlanUpsertInput(
            title=title,
            change_reason=change_reason,
            goal=goal,
            timeline=timeline,
            strategy=strategy,
            nutrition_strategy=nutrition_strategy,
            training_program=training_program,
            current_summary=current_summary,
            checkpoints=checkpoints or [],
        )

        missing_fields = missing_master_plan_fields(payload)
        if missing_fields:
            return (
                "ERRO_UPSERT_PLAN_INCOMPLETO: faltam campos obrigatorios: "
                f"{', '.join(missing_fields)}. "
                "PLANO_NAO_SALVO. Nao afirme que salvou/ativou o plano. "
                "Use o payload minimo e tente novamente no proximo turno.\n"
                f"{_minimum_upsert_payload_template()}"
            )

        latest = database.get_latest_plan(user_email)
        try:
            plan = build_plan_singleton(user_email, latest, payload)
            plan_id = database.save_plan(plan)
            snapshot = build_plan_prompt_snapshot(plan)
            logger.info("upsert_plan saved for user: %s (plan_id=%s)", user_email, plan_id)
            return (
                f"SUCESSO_UPSERT_PLAN: Plano salvo com sucesso. ID: {plan_id}.\n"
                f"{format_plan_snapshot(snapshot)}"
            )
        except ValidationError as exc:
            logger.warning(
                "upsert_plan invalid structure for user %s: %s",
                user_email,
                exc,
            )
            validation_issues = ", ".join(
                ".".join(str(part) for part in err["loc"]) for err in exc.errors()
            )
            return (
                "ERRO_UPSERT_PLAN_ESTRUTURA_INVALIDA: "
                "estrutura do plano invalida para persistencia. "
                "PLANO_NAO_SALVO. Campos/locais invalidos: "
                f"{validation_issues}"
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("upsert_plan failed for user %s: %s", user_email, exc, exc_info=True)
            return (
                "ERRO_UPSERT_PLAN_PERSISTENCIA: falha ao salvar no banco. "
                "PLANO_NAO_SALVO. Nao afirme que salvou/ativou o plano."
            )

    return upsert_plan
