from unittest.mock import MagicMock

from src.services.prompt_builder import PromptBuilder
from src.api.models.plan import PlanSnapshot


def _base_input(plan_snapshot=None):
    profile = MagicMock()
    profile.display_name = "Rafa"
    profile.timezone = "Europe/Madrid"

    return PromptBuilder.build_input_data(
        profile=profile,
        trainer_profile_summary="**Nome:** Atlas",
        user_profile_summary="Perfil",
        formatted_history_msgs=[],
        user_input="Como estou no plano?",
        current_date="2026-04-19",
        plan_snapshot=plan_snapshot,
    )


def test_prompt_builder_injects_plan_section_when_snapshot_exists():
    snapshot = PlanSnapshot(
        title="Plano Atual",
        objective_summary="Ganhar massa",
        plan_period="2026-04-19 a 2026-06-19",
        status="active",
        active_focus="consistencia",
        today_training="Push",
        today_nutrition="3000 kcal / 180g",
        upcoming_days=["Pull"],
        last_checkpoint_summary="aderencia boa",
        critical_constraints=["viagem quinta"],
        pending_adjustment=None,
    )

    input_data = _base_input(snapshot)
    rendered = PromptBuilder.get_prompt_template(input_data).format(**input_data)

    assert "## Plano ativo do aluno" in rendered
    assert "Push" in rendered


def test_prompt_builder_removes_plan_section_when_snapshot_missing():
    input_data = _base_input(None)
    rendered = PromptBuilder.get_prompt_template(input_data).format(**input_data)

    assert "## Plano ativo do aluno" in rendered
    assert "Nenhum plano ativo registrado." in rendered
