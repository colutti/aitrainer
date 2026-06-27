"""Local tools for plan V2 lifecycle management."""

import json
from textwrap import dedent

from pydantic import ValidationError

from src.api.models.plan import (
    CANONICAL_PLAN_SECTIONS,
    PlanCreateInput,
    PlanDiscoveryUpdateInput,
    PlanReviewInput,
    PlanSectionUpdateInput,
)
from src.core.logs import logger
from src.services.compat_tools import tool
from src.services.plan_hevy_sync import HevySyncError, sync_training_with_hevy_if_needed
from src.services.plan_service import (
    apply_discovery_update,
    attach_review,
    build_plan_from_create_input,
    build_plan_view_model,
    build_progress_snapshot,
    build_review_record,
    merge_plan_section,
    missing_discovery_fields,
)


def _tool_result(**payload) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)


def create_plan_help_tool(_database, _user_email: str):
    """Return operational instructions for the plan V2 tools."""

    @tool
    def plan_help() -> str:
        """Explica o contrato V2 do plano e o fluxo correto das tools."""
        return dedent(
            """\
            PLAN_V2_HELP

            O plano ativo e a fonte primaria para treino, nutricao e progresso.

            Fluxo quando NAO existe plano:
            1. Use get_plan_status.
            2. Use update_plan_discovery ate completar os dados obrigatorios.
            3. Chame get_metabolism_data antes de fechar a estrategia nutricional.
            4. Chame create_plan_from_discovery com o payload completo e tipado.

            Fluxo quando existe plano:
            1. Use get_plan_status para confirmar ACTIVE_PLAN.
            2. Use update_plan_section para alterar goal, timeline,
               user_context, training, nutrition, alignment ou tracking.
               Para mudancas de estrategia (ex: bulking -> recomposition),
               envie goal+alignment+timeline (e nutrition se necessario)
               no mesmo update_plan_section para manter consistencia atomica.
            3. Use record_plan_review para registrar evidencia, decisao e proxima revisao.

            Regras de formato:
            - Datas: YYYY-MM-DD.
            - Dias: monday..sunday.
            - goal.primary_goal: fat_loss | muscle_gain | recomposition | performance | health.
            - alignment.energy_strategy: deficit | maintenance | surplus | recomposition.
            - intensidade: use prescription_type + target.
            - progressao: use method + increase_when + hold_when + deload_when.

            Regras fortes:
            - Sem plano ativo, qualquer recomendacao deve ser tratada como generica.
            - Nao crie plano generico sem discovery completo.
            - saved=false significa que a IA NAO pode afirmar criacao,
              atualizacao ou ativacao do plano.
            """
        )

    return plan_help


def create_get_plan_tool(database, user_email: str):
    """Return the active plan as serialized JSON when it exists."""

    @tool
    def get_plan() -> str:
        """Retorna o plano ativo completo em JSON."""
        plan = database.get_plan(user_email)
        if plan is None:
            return _tool_result(
                status="NO_PLAN",
                saved=False,
                plan_materially_changed=False,
                plan=None,
            )
        return _tool_result(
            status="ACTIVE_PLAN",
            saved=False,
            plan_materially_changed=False,
            plan=plan.model_dump(),
        )

    return get_plan


def create_get_plan_status_tool(database, user_email: str):
    """Return the current plan lifecycle state."""

    @tool
    def get_plan_status() -> str:
        """Retorna o status do plano: NO_PLAN, DISCOVERY_IN_PROGRESS ou ACTIVE_PLAN."""
        plan = database.get_plan(user_email)
        if plan is not None:
            progress = build_progress_snapshot(plan, database)
            view = build_plan_view_model(plan, None, progress)
            return _tool_result(
                status="ACTIVE_PLAN",
                saved=False,
                plan_materially_changed=False,
                plan_id=plan.id,
                missing_fields=[],
                view=view.model_dump(),
            )

        discovery = database.get_plan_discovery(user_email)
        missing_fields = missing_discovery_fields(discovery)
        return _tool_result(
            status="DISCOVERY_IN_PROGRESS" if discovery else "NO_PLAN",
            saved=False,
            plan_materially_changed=False,
            plan_id=None,
            missing_fields=missing_fields,
            discovery=discovery.model_dump() if discovery else None,
        )

    return get_plan_status


def create_update_plan_discovery_tool(database, user_email: str):
    """Persist incremental discovery answers."""

    @tool(args_schema=PlanDiscoveryUpdateInput)
    def update_plan_discovery(**kwargs) -> str:
        """Atualiza o discovery do plano com respostas do usuario."""
        payload = PlanDiscoveryUpdateInput(**kwargs)
        current = database.get_plan_discovery(user_email)
        discovery = apply_discovery_update(user_email, current, payload)
        discovery_id = database.save_plan_discovery(discovery)
        logger.info("plan discovery updated for user %s", user_email)
        return _tool_result(
            status="discovery_updated",
            saved=True,
            plan_materially_changed=False,
            plan_id=None,
            discovery_id=discovery_id,
            missing_fields=discovery.missing_fields,
            validation_errors=[],
            changed_sections=["discovery"],
            external_sync_failed=False,
            message_for_ai="Discovery atualizado. Continue perguntando apenas o proximo bloqueio.",
        )

    return update_plan_discovery


def create_create_plan_from_discovery_tool(database, user_email: str):
    """Create the first active plan once discovery is complete."""

    @tool(args_schema=PlanCreateInput)
    def create_plan_from_discovery(**kwargs) -> str:
        """Cria o plano ativo a partir de discovery completo e payload tipado."""
        discovery = database.get_plan_discovery(user_email)
        missing_fields = missing_discovery_fields(discovery)
        if missing_fields:
            return _tool_result(
                status="discovery_needed",
                saved=False,
                plan_materially_changed=False,
                plan_id=None,
                changed_sections=[],
                missing_fields=missing_fields,
                validation_errors=[],
                external_sync_failed=False,
                message_for_ai="Discovery incompleto. Nao crie o plano ainda.",
            )

        try:
            payload = PlanCreateInput(**kwargs)
            plan = build_plan_from_create_input(user_email, payload)
            plan_id = database.save_plan(plan)
            database.clear_plan_discovery(user_email)
            return _tool_result(
                status="success",
                saved=True,
                plan_materially_changed=True,
                plan_id=plan_id,
                changed_sections=list(CANONICAL_PLAN_SECTIONS),
                missing_fields=[],
                validation_errors=[],
                external_sync_failed=False,
                message_for_ai="Plano criado com sucesso.",
            )
        except ValidationError as exc:
            logger.warning("create_plan_from_discovery invalid payload: %s", exc)
            return _tool_result(
                status="validation_error",
                saved=False,
                plan_materially_changed=False,
                plan_id=None,
                changed_sections=[],
                missing_fields=[],
                validation_errors=exc.errors(),
                external_sync_failed=False,
                message_for_ai="Payload do plano invalido. Corrija os campos e tente novamente.",
            )

    return create_plan_from_discovery


def create_update_plan_section_tool(database, user_email: str):
    """Update a single typed section of the active plan."""

    @tool(args_schema=PlanSectionUpdateInput)
    def update_plan_section(**kwargs) -> str:
        """Atualiza uma secao tipada do plano ativo."""
        current = database.get_plan(user_email)
        if current is None:
            return _tool_result(
                status="no_plan",
                saved=False,
                plan_materially_changed=False,
                plan_id=None,
                changed_sections=[],
                missing_fields=["active_plan"],
                validation_errors=[],
                external_sync_failed=False,
                message_for_ai="Nao existe plano ativo. Faca discovery e crie o plano primeiro.",
            )

        try:
            payload = PlanSectionUpdateInput(**kwargs)
            changed_sections = [
                section
                for section in CANONICAL_PLAN_SECTIONS
                if getattr(payload, section) is not None
            ]
            updated_plan = merge_plan_section(current, payload)
            if payload.section == "training":
                updated_plan = sync_training_with_hevy_if_needed(
                    database=database,
                    user_email=user_email,
                    current_plan=current,
                    updated_plan=updated_plan,
                )
            plan_id = database.save_plan(updated_plan)
            return _tool_result(
                status="success",
                saved=True,
                plan_materially_changed=True,
                plan_id=plan_id,
                changed_sections=changed_sections,
                missing_fields=[],
                validation_errors=[],
                external_sync_failed=False,
                message_for_ai="Plano atualizado com sucesso.",
            )
        except HevySyncError as exc:
            logger.warning("update_plan_section hevy sync failed: %s", exc)
            return _tool_result(
                status="external_sync_failed",
                saved=False,
                plan_materially_changed=False,
                plan_id=current.id,
                changed_sections=[],
                missing_fields=[],
                validation_errors=[],
                external_sync_failed=True,
                message_for_ai=str(exc),
            )
        except ValidationError as exc:
            logger.warning("update_plan_section validation error: %s", exc)
            return _tool_result(
                status="validation_error",
                saved=False,
                plan_materially_changed=False,
                plan_id=current.id,
                changed_sections=[],
                missing_fields=[],
                validation_errors=exc.errors(),
                external_sync_failed=False,
                message_for_ai="A secao do plano nao foi atualizada por erro de validacao.",
            )
        except ValueError as exc:
            logger.warning("update_plan_section semantic validation error: %s", exc)
            return _tool_result(
                status="validation_error",
                saved=False,
                plan_materially_changed=False,
                plan_id=current.id,
                changed_sections=[],
                missing_fields=[],
                validation_errors=[{"msg": str(exc), "type": "value_error"}],
                external_sync_failed=False,
                message_for_ai=(
                    "A secao do plano nao foi atualizada por inconsistencias "
                    "semanticas entre objetivo e estrategia."
                ),
            )

    return update_plan_section


def create_record_plan_review_tool(database, user_email: str):
    """Append a review to the active plan."""

    @tool(args_schema=PlanReviewInput)
    def record_plan_review(**kwargs) -> str:
        """Registra uma revisao estruturada do plano ativo."""
        current = database.get_plan(user_email)
        if current is None:
            return _tool_result(
                status="no_plan",
                saved=False,
                plan_materially_changed=False,
                plan_id=None,
                changed_sections=[],
                missing_fields=["active_plan"],
                validation_errors=[],
                external_sync_failed=False,
                message_for_ai="Nao existe plano ativo para revisar.",
            )

        try:
            payload = PlanReviewInput(**kwargs)
            review = build_review_record(payload)
            updated_plan = attach_review(current, review)
            plan_id = database.save_plan(updated_plan)
            return _tool_result(
                status="review_recorded",
                saved=True,
                plan_materially_changed=False,
                plan_id=plan_id,
                changed_sections=["latest_review", "review_history"],
                missing_fields=[],
                validation_errors=[],
                external_sync_failed=False,
                message_for_ai="Revisao do plano registrada com sucesso.",
            )
        except ValidationError as exc:
            logger.warning("record_plan_review validation error: %s", exc)
            return _tool_result(
                status="validation_error",
                saved=False,
                plan_materially_changed=False,
                plan_id=current.id,
                changed_sections=[],
                missing_fields=[],
                validation_errors=exc.errors(),
                external_sync_failed=False,
                message_for_ai="A revisao nao foi registrada por erro de validacao.",
            )

    return record_plan_review
