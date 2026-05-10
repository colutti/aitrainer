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
    validate_training_program_quality,
)


DISCOVERY_REQUIRED_FIELDS = {
    "goal.primary": "objetivo do aluno (lose_fat, build_muscle, recomposition, performance)",
    "goal.objective_summary": "resumo especifico do objetivo com criterio de sucesso",
    "goal.success_criteria": "criterios de sucesso mensuraveis",
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
    return dedent(
        """\
        {
          "title": "Plano Mestre Ganho de Massa - 6x PPL",
          "change_reason": "initial_plan",
          "goal": {
            "primary": "build_muscle",
            "objective_summary": "Ganhar massa muscular em 3 meses com treino 6x/semana PPL",
            "success_criteria": ["aderencia >= 80%", "progressao de carga semanal", "peso corporal +1.5kg/mes"]
          },
          "timeline": {
            "target_date": "2026-08-10T00:00:00",
            "review_cadence": "semanal"
          },
          "strategy": {
            "rationale": "Superavit calorico com alta frequencia e volume progressivo para hipertrofia",
            "adaptation_policy": "revisoes semanais para ajustar carga e volume",
            "constraints": [],
            "preferences": ["treino a noite", "gosta de agachamento"],
            "current_risks": []
          },
          "nutrition_strategy": {
            "daily_targets": {
              "calories": 2800,
              "protein_g": 150,
              "carbs_g": 370,
              "fat_g": 80
            },
            "adherence_notes": []
          },
          "training_program": {
            "split_name": "push_pull_legs",
            "frequency_per_week": 6,
            "session_duration_min": 60,
            "program_notes": "PPL classico com foco em progressao de carga semanal",
            "progression_rules": ["adicionar 2kg nos exercicios base quando fizer 2 reps extras na faixa alvo"],
            "review_triggers": ["estagnacao por 2 semanas seguidas", "dor ou desconforto articular", "falta de 3+ sessoes na semana"],
            "routines": [
              {
                "id": "push",
                "name": "Push",
                "objective": "empurrar",
                "warmup": "5min aquecimento geral, 2 series de aproximacao no supino",
                "notes": "Foco em forma no desenvolvimento",
                "exercises": [
                  {
                    "name": "Supino reto",
                    "sets": 4,
                    "reps": "6-8",
                    "load_guidance": "RPE 8",
                    "rest_seconds": 90,
                    "tempo": "3-0-1-0",
                    "coach_notes": "escapulas retraidas, cotovelos 45 graus"
                  },
                  {
                    "name": "Desenvolvimento militar",
                    "sets": 3,
                    "reps": "8-10",
                    "load_guidance": "RPE 8",
                    "rest_seconds": 90,
                    "coach_notes": "nao arquear lombar, cotovelo na linha do ombro"
                  },
                  {
                    "name": "Crucifixo reto",
                    "sets": 3,
                    "reps": "10-12",
                    "load_guidance": "RPE 7",
                    "rest_seconds": 60
                  },
                  {
                    "name": "Triceps pulley",
                    "sets": 3,
                    "reps": "12-15",
                    "load_guidance": "RPE 8",
                    "rest_seconds": 60
                  }
                ]
              },
              {
                "id": "pull",
                "name": "Pull",
                "objective": "puxar",
                "warmup": "5min alongamento dinâmico, 2 series leves de remada",
                "notes": "priorizar contraçao escapular",
                "exercises": [
                  {
                    "name": "Remada curvada",
                    "sets": 4,
                    "reps": "6-8",
                    "load_guidance": "RPE 8",
                    "rest_seconds": 90,
                    "coach_notes": "tronco a 45 graus, puxar na direcao do umbigo"
                  },
                  {
                    "name": "Puxada alta na polia",
                    "sets": 3,
                    "reps": "8-10",
                    "load_guidance": "RPE 8",
                    "rest_seconds": 90
                  },
                  {
                    "name": "Rosca direta",
                    "sets": 3,
                    "reps": "10-12",
                    "load_guidance": "RPE 8",
                    "rest_seconds": 60
                  }
                ]
              },
              {
                "id": "legs",
                "name": "Legs",
                "objective": "pernas",
                "warmup": "5min bike, 2 series de aproximacao no agachamento",
                "exercises": [
                  {
                    "name": "Agachamento livre",
                    "sets": 4,
                    "reps": "6-8",
                    "load_guidance": "RPE 8",
                    "rest_seconds": 120,
                    "coach_notes": "quadril para tras, joelho acompanha o pe"
                  },
                  {
                    "name": "Leg press",
                    "sets": 3,
                    "reps": "10-12",
                    "load_guidance": "RPE 8",
                    "rest_seconds": 90
                  },
                  {
                    "name": "Extensora",
                    "sets": 3,
                    "reps": "12-15",
                    "load_guidance": "RPE 8",
                    "rest_seconds": 60
                  }
                ]
              }
            ],
            "weekly_schedule": [
              {"day": "monday", "routine_id": "push", "focus": "push", "type": "training"},
              {"day": "tuesday", "routine_id": "pull", "focus": "pull", "type": "training"},
              {"day": "wednesday", "routine_id": "legs", "focus": "legs", "type": "training"},
              {"day": "thursday", "routine_id": "push", "focus": "push", "type": "training"},
              {"day": "friday", "routine_id": "pull", "focus": "pull", "type": "training"},
              {"day": "saturday", "routine_id": "legs", "focus": "legs", "type": "training"}
            ]
          },
          "current_summary": {
            "active_focus": "ganho de massa",
            "rationale": "alta frequencia e volume para hipertrofia",
            "key_risks": [],
            "last_review": null,
            "next_review": "2026-05-17T00:00:00"
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

        IMPORTANTE: Voce e o plan manager. Nao invente treinos ou dietas.
        O training_program e nutrition_strategy devem vir das propostas
        dos especialistas de dominio, nao da sua criacao propria.
        """
        return (
            "# Plan Tools Help\n\n"
            "## Fluxo obrigatorio\n"
            "1. Aguarde a propostas de treino do training_specialist e de nutricao "
            "do nutrition_specialist.\n"
            "2. Consolide as propostas recebidas.\n"
            "3. Verifique coerencia entre treino, nutricao e timeline.\n"
            "4. Monte o payload COMPLETO com todos os campos obrigatorios.\n"
            "5. Chame upsert_plan UMA VEZ com o payload completo.\n\n"
            "## Quando NAO chamar upsert_plan\n"
            "- Se as propostas de treino ou nutricao ainda nao estao prontas "
            "(proposal_status != 'ready').\n"
            "- Se falta coerencia entre treino e nutricao.\n"
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
            "- Para mudar SOMENTE nutricao: envie training_program com os campos de programa.\n\n"
            "## IMPORTANTE: Qualidade do training_program\n"
            "- Cada rotina deve ter exercicios suficientes para uma sessao produtiva "
            "(tipicamente 4-8 dependendo do split e frequencia).\n"
            "- Cada exercicio precisa de rest_seconds e coach_notes para ser util.\n"
            "- Inclua program_notes, progression_rules e review_triggers.\n"
            "- Nao crie rotinas com 2 exercicios apenas — isso nao e um treino completo.\n\n"
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
        """Cria ou atualiza o plano mestre singleton.

        SO chame esta tool quando voce tiver TODOS os dados obrigatorios do usuario:
        objetivo principal, resumo do objetivo com criterio de sucesso, prazo com data alvo,
        disponibilidade semanal (dias e duracao), restricoes, estrategia, metas nutricionais
        e programa de treino completo (rotinas + agenda semanal).

        Se faltam dados do usuario, NAO chame esta tool. Retorne plan_status='discovery_needed'
        e descreva em technical_summary quais informacoes faltam. O coach_reply vai transformar
        isso em perguntas ao usuario.

        Sempre chame get_metabolism_data ANTES de definir metas nutricionais numericas.
        """
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
            payload.nutrition_strategy.get("daily_targets", {}),
        )

        # NEW PLAN: validate everything and create from scratch
        if latest is None:
            missing_fields = missing_master_plan_fields(payload)
            if missing_fields:
                logger.warning(
                    "upsert_plan REJECTED incomplete: %s", missing_fields,
                )
                discovery_list = _format_missing_fields_with_descriptions(missing_fields)
                return (
                    "ERRO_UPSERT_PLAN_INCOMPLETO: faltam campos obrigatorios:\n"
                    f"{discovery_list}\n\n"
                    "PLANO_NAO_SALVO. Nao afirme que salvou/ativou o plano.\n"
                    "ACAO: NAO tente chamar upsert_plan novamente neste turno. "
                    "RETORNE plan_status=discovery_needed e liste em technical_summary "
                    "que faltam para completar o plano. O coach_reply vai transformar isso em "
                    "perguntas ao usuario.\n"
                    "Consulte plan_help para ver o payload minimo completo."
                )
            quality_issues = validate_training_program_quality(payload.training_program)
            if quality_issues:
                logger.warning(
                    "upsert_plan REJECTED quality: %s", quality_issues,
                )
                return (
                    "ERRO_UPSERT_PLAN_INCOMPLETO: programa de treino abaixo"
                    " do minimo de qualidade:\n"
                    + "\n".join(f"- {issue}" for issue in quality_issues)
                    + "\n\n"
                    "PLANO_NAO_SALVO. Nao afirme que salvou/ativou o plano.\n"
                    "ACAO: Retorne plan_status=discovery_needed e liste as"
                    " correcoes em technical_summary para que o"
                    " training_specialist ajuste a proposta.\n"
                    "Consulte plan_help para ver um exemplo completo."
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

        # EXISTING PLAN: merge with existing, validate, then save
        missing_fields = missing_master_plan_fields(payload, latest)
        if missing_fields:
            logger.warning(
                "upsert_plan REJECTED incomplete: %s", missing_fields,
            )
            discovery_list = _format_missing_fields_with_descriptions(missing_fields)
            return (
                "ERRO_UPSERT_PLAN_INCOMPLETO: faltam campos obrigatorios:\n"
                f"{discovery_list}\n\n"
                "PLANO_NAO_SALVO. Nao afirme que salvou/ativou o plano.\n"
                "ACAO: NAO tente chamar upsert_plan novamente neste turno. "
                "Retorne plan_status='update_failed' e liste em technical_summary quais "
                "informacoes adicionais sao necessarias. "
                "Consulte plan_help para ver o payload minimo completo."
            )
        quality_issues = validate_training_program_quality(payload.training_program)
        if quality_issues:
            logger.warning(
                "upsert_plan REJECTED quality on update: %s", quality_issues,
            )
            return (
                "ERRO_UPSERT_PLAN_INCOMPLETO: programa de treino abaixo"
                " do minimo de qualidade:\n"
                + "\n".join(f"- {issue}" for issue in quality_issues)
                + "\n\n"
                "PLANO_NAO_SALVO. Nao afirme que salvou/ativou o plano.\n"
                "ACAO: Retorne plan_status='update_failed' e liste"
                " correcoes em technical_summary."
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
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("upsert_plan failed for user %s: %s", user_email, exc, exc_info=True)
            return (
                "ERRO_UPSERT_PLAN_PERSISTENCIA: falha ao salvar no banco. "
                "PLANO_NAO_SALVO. Nao afirme que salvou/ativou o plano."
            )

    return upsert_plan
