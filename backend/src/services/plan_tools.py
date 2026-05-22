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


DISCOVERY_REQUIRED_FIELDS = {
    "goal.primary": "objetivo do aluno (lose_fat, build_muscle, recomposition, performance)",
    "goal.objective_summary": "resumo especifico do objetivo com criterio de sucesso",
    "goal.success_criteria": "criterios de sucesso mensuraveis",
    "goal.metric_targets.direction": "direcao operacional (lose, gain, maintain)",
    "goal.metric_targets.target_weight_kg": "peso-alvo em kg para projeções",
    "goal.metric_targets.weekly_weight_change_kg": "ritmo semanal desejado em kg",
    "goal.metric_targets.target_body_fat_pct": "percentual de gordura alvo opcional",
    "timeline.target_date": "data alvo para atingir o objetivo (ISO 8601)",
    "timeline.review_cadence": "cadencia de revisao (ex: semanal, quinzenal, mensal)",
    "strategy.rationale": "racional estrategico do plano",
    "strategy.adaptation_policy": "politica de adaptacao do plano",
    "strategy.constraints": "restricoes e limitacoes",
    "strategy.preferences": "preferencias do aluno",
    "strategy.current_risks": "riscos atuais identificados",
    "nutrition_strategy.daily_targets": "metas diarias (calories, protein_g, carbs_g, fat_g)",
    "nutrition_strategy.daily_targets.calories": "calorias diarias alvo",
    "nutrition_strategy.daily_targets.protein_g": "gramas de proteina diarios alvo",
    "nutrition_strategy.daily_targets.carbs_g": "gramas de carboidratos diarios alvo",
    "nutrition_strategy.daily_targets.fat_g": "gramas de gordura diarios alvo",
    "training_program.split_name": "nome do split (push_pull_legs, upper_lower, full_body)",
    "training_program.frequency_per_week": "frequencia semanal de treino (dias por semana)",
    "training_program.session_duration_min": "duracao de cada sessao em minutos",
    "training_program.routines": "lista de rotinas de treino com exercicios",
    "training_program.weekly_schedule": "agenda semanal de treinos",
    "current_summary.active_focus": "foco atual do plano",
    "current_summary.rationale": "justificativa do foco atual",
    "current_summary.next_review": "data da proxima revisao (ISO 8601)",
}


def _format_missing_fields_with_descriptions(missing_fields: list[str]) -> str:
    lines = []
    for field in missing_fields:
        desc = DISCOVERY_REQUIRED_FIELDS.get(field, "campo obrigatorio")
        lines.append(f"- {field}: {desc}")
    return "\n".join(lines)


def _minimum_upsert_payload_template() -> str:
    # pylint: disable=line-too-long
    return dedent(
        """\
        {
          "title": "Plano Mestre Recomp",
          "change_reason": "initial_plan",
          "goal": {
            "primary": "lose_fat",
            "objective_summary": "Chegar a 15% de gordura corporal ate o verao",
            "success_criteria": ["aderencia >= 80%", "perda de gordura sustentavel"],
            "metric_targets": {
              "direction": "lose",
              "target_weight_kg": 76,
              "weekly_weight_change_kg": 0.4
            }
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
              "calories": 2100,
              "protein_g": 160,
              "carbs_g": 215,
              "fat_g": 63
            },
            "adherence_notes": []
          },
          "training_program": {
            "split_name": "push_pull_legs",
            "frequency_per_week": 6,
            "session_duration_min": 60,
            "routines": [
              {
                "id": "push_a",
                "name": "Push A",
                "exercises": [
                  {"name": "Supino reto com barra", "sets": 4, "reps": "6-8", "load_guidance": "RPE 8"},
                  {"name": "Supino inclinado com halteres", "sets": 3, "reps": "8-10", "load_guidance": "RPE 8"},
                  {"name": "Desenvolvimento militar com barra", "sets": 3, "reps": "8-10", "load_guidance": "RPE 8"},
                  {"name": "Elevacao lateral com halteres", "sets": 3, "reps": "12-15", "load_guidance": "RPE 7"},
                  {"name": "Triceps corda no pulley", "sets": 3, "reps": "10-12", "load_guidance": "RPE 8"},
                  {"name": "Triceps frances com barra EZ", "sets": 3, "reps": "10-12", "load_guidance": "RPE 8"}
                ]
              },
              {
                "id": "pull_a",
                "name": "Pull A",
                "exercises": [
                  {"name": "Puxada alta pela frente", "sets": 4, "reps": "8-10", "load_guidance": "RPE 8"},
                  {"name": "Remada curvada com barra", "sets": 4, "reps": "6-8", "load_guidance": "RPE 8"},
                  {"name": "Remada unilateral com halter", "sets": 3, "reps": "8-10", "load_guidance": "RPE 8"},
                  {"name": "Face pull no pulley", "sets": 3, "reps": "12-15", "load_guidance": "RPE 7"},
                  {"name": "Rosca direta com barra", "sets": 3, "reps": "10-12", "load_guidance": "RPE 8"},
                  {"name": "Rosca martelo com halteres", "sets": 3, "reps": "10-12", "load_guidance": "RPE 8"}
                ]
              },
              {
                "id": "legs_a",
                "name": "Legs A",
                "exercises": [
                  {"name": "Agachamento livre com barra", "sets": 4, "reps": "6-8", "load_guidance": "RPE 8"},
                  {"name": "Leg press 45 graus", "sets": 3, "reps": "8-10", "load_guidance": "RPE 8"},
                  {"name": "Cadeira extensora", "sets": 3, "reps": "10-12", "load_guidance": "RPE 8"},
                  {"name": "Mesa flexora", "sets": 3, "reps": "10-12", "load_guidance": "RPE 8"},
                  {"name": "Stiff com barra", "sets": 3, "reps": "8-10", "load_guidance": "RPE 7"},
                  {"name": "Elevacao de panturrilha em pe", "sets": 4, "reps": "12-15", "load_guidance": "RPE 8"}
                ]
              }
            ],
            "weekly_schedule": [
              {"day": "monday", "routine_id": "push_a", "focus": "push", "type": "training"},
              {"day": "tuesday", "routine_id": "pull_a", "focus": "pull", "type": "training"},
              {"day": "wednesday", "routine_id": "legs_a", "focus": "legs", "type": "training"},
              {"day": "thursday", "routine_id": "push_a", "focus": "push", "type": "training"},
              {"day": "friday", "routine_id": "pull_a", "focus": "pull", "type": "training"},
              {"day": "saturday", "routine_id": "legs_a", "focus": "legs", "type": "training"}
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
        """Retorna guia de como montar e ajustar plano mestre singleton.

        Use esta tool para relembrar o fluxo completo de criacao de plano,
        incluindo quais dados coletar antes de chamar upsert_plan.
        """
        return (
            "# Plan Tools Help\n\n"
            "## Fluxo obrigatorio\n"
            "1. Discovery: colete do usuario objetivo, prazo, disponibilidade semanal, "
            "restricoes e preferencias.\n"
            "2. Consulte get_metabolism_data antes de definir macros.\n"
            "3. Monte o payload COMPLETO com todos os campos obrigatorios.\n"
            "4. Chame upsert_plan UMA VEZ com o payload completo.\n\n"
            "## Quando NAO chamar upsert_plan\n"
            "- Se o usuario nao informou objetivo principal, prazo/meta com data alvo, "
            "disponibilidade semanal (dias e minutos), ou restricoes relevantes.\n"
            "- Se voce nao tem dados metabolicos (chame get_metabolism_data primeiro).\n"
            "- Se esta em fase de discovery: retorne plan_status='discovery_needed'.\n"
            "- Se upsert_plan retornou ERRO_UPSERT_PLAN_INCOMPLETO: NAO tente novamente "
            "no mesmo turno. Retorne plan_status='discovery_needed' e liste o que falta.\n\n"
            "## Regras\n"
            "- Plano e singleton sobrescrito por usuario.\n"
            "- Criacao inicial exige objetivo, estrategia, metas nutricionais e programa semanal.\n"
            "- Metas nutricionais (nutrition_strategy.daily_targets) DEVEM incluir "
            "calories, protein_g, carbs_g e fat_g. Nunca omitir carbs_g ou fat_g.\n"
            "- Nao repetir upsert_plan com payload igual no mesmo turno.\n"
            "- Para ATUALIZAR: envie o payload COMPLETO com todos os campos. "
            "O sistema faz merge automatico com o plano existente.\n"
            "- Para mudar SOMENTE nutricao: envie training_program com split_name e "
            "routines contendo apenas id+name. O sistema preserva exercises existentes.\n\n"
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

# pylint: disable=too-many-statements
def create_upsert_plan_tool(database, user_email: str):
    """Creates or updates singleton plan."""

    call_count = 0
    last_payload_hash: str | None = None
    retry_blocked = False
    retry_block_reason = ""

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

    def _mark_retry_blocked(reason: str) -> None:
        nonlocal retry_blocked, retry_block_reason
        retry_blocked = True
        retry_block_reason = reason

    @tool(args_schema=PlanUpsertInput)
    # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals,too-many-return-statements,too-many-statements
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
        """Cria ou atualiza o plano mestre singleton.

        SO chame esta tool quando voce tiver TODOS os dados obrigatorios do usuario:
        objetivo principal, resumo do objetivo com criterio de sucesso, prazo com data alvo,
        disponibilidade semanal (dias e duracao), restricoes, estrategia, metas nutricionais
        e programa de treino completo (rotinas + agenda semanal).

        Se faltam dados do usuario, NAO chame esta tool. Retorne plan_status='discovery_needed',
        use internal_analysis para explicar quais informacoes faltam e public_message para
        perguntar ao usuario somente o proximo bloqueio.

        Sempre chame get_metabolism_data ANTES de definir metas nutricionais numericas.
        """
        if retry_blocked:
            return (
                "ERRO_UPSERT_PLAN_RETRY_BLOQUEADO: houve falha anterior de persistencia "
                f"neste turno ({retry_block_reason}). PLANO_NAO_SALVO. "
                "Nao tente novamente agora; retome no proximo turno com payload corrigido."
            )

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
            logger.warning("upsert_plan BLOCKED by loop guard: %s", guard_error)
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

        latest = database.get_latest_plan(user_email)
        logger.info(
            "upsert_plan nutrition payload: %s",
            payload.nutrition_strategy.get("daily_targets", {}),  # pylint: disable=no-member
        )

        # NEW PLAN: validate everything and create from scratch
        if latest is None:
            missing_fields = missing_master_plan_fields(payload)
            if missing_fields:
                logger.warning(
                    "upsert_plan REJECTED incomplete: %s", missing_fields,
                )
                _mark_retry_blocked("incompleto")
                discovery_list = _format_missing_fields_with_descriptions(missing_fields)
                return (
                    "ERRO_UPSERT_PLAN_INCOMPLETO: faltam campos obrigatorios:\n"
                    f"{discovery_list}\n\n"
                    "PLANO_NAO_SALVO. Nao afirme que salvou/ativou o plano.\n"
                    "ACAO: NAO tente chamar upsert_plan novamente neste turno. "
                    "RETORNE plan_status=discovery_needed, liste em internal_analysis "
                    "o que falta para completar o plano e use public_message para a "
                    "proxima pergunta ao usuario.\n"
                    "Consulte plan_help para ver o payload minimo completo."
                )
            try:
                plan = build_plan_singleton(user_email, None, payload)
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
                _mark_retry_blocked("estrutura_invalida")
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
                _mark_retry_blocked("persistencia")
                return (
                    "ERRO_UPSERT_PLAN_PERSISTENCIA: falha ao salvar no banco. "
                    "PLANO_NAO_SALVO. Nao afirme que salvou/ativou o plano."
                )

        # EXISTING PLAN: merge with existing, validate, then save
        missing_fields = missing_master_plan_fields(payload, latest)
        if missing_fields:
            logger.warning(
                "upsert_plan REJECTED incomplete: %s", missing_fields,
            )
            _mark_retry_blocked("incompleto")
            discovery_list = _format_missing_fields_with_descriptions(missing_fields)
            return (
                "ERRO_UPSERT_PLAN_INCOMPLETO: faltam campos obrigatorios:\n"
                f"{discovery_list}\n\n"
                "PLANO_NAO_SALVO. Nao afirme que salvou/ativou o plano.\n"
                "ACAO: NAO tente chamar upsert_plan novamente neste turno. "
                "Retorne plan_status='update_failed', liste em internal_analysis quais "
                "informacoes adicionais sao necessarias e use public_message para a "
                "proxima pergunta ao usuario. "
                "Consulte plan_help para ver o payload minimo completo."
            )
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
            _mark_retry_blocked("estrutura_invalida")
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
            _mark_retry_blocked("persistencia")
            return (
                "ERRO_UPSERT_PLAN_PERSISTENCIA: falha ao salvar no banco. "
                "PLANO_NAO_SALVO. Nao afirme que salvou/ativou o plano."
            )

    return upsert_plan
