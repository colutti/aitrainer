from unittest.mock import MagicMock

from src.api.models.plan import PlanPromptContext
from src.services.prompt_builder import PromptBuilder


def _base_input(plan_snapshot: PlanPromptContext):
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


def test_prompt_builder_injects_active_plan_context():
    snapshot = PlanPromptContext(
        status="ACTIVE_PLAN",
        schema_version="plan_v2",
        active_plan={
            "title": "Plano Atual",
            "goal": {"primary_goal": "muscle_gain", "outcome_summary": "Ganhar massa"},
            "training": {"split_name": "Push/Pull/Legs"},
        },
        discovery={},
        progress_summary={},
    )

    input_data = _base_input(snapshot)
    rendered = PromptBuilder.get_prompt_template(input_data).format(**input_data)

    assert '"plan"' in rendered
    assert "ACTIVE_PLAN" in rendered
    assert "Push/Pull/Legs" in rendered


def test_prompt_builder_injects_discovery_context_without_active_plan():
    snapshot = PlanPromptContext(
        status="NO_PLAN",
        schema_version=None,
        active_plan={},
        discovery={"missing_fields": ["goal_primary", "target_date"]},
        progress_summary={},
    )

    input_data = _base_input(snapshot)
    rendered = PromptBuilder.get_prompt_template(input_data).format(**input_data)

    assert '"plan"' in rendered
    assert "START_OR_CONTINUE_DISCOVERY" in rendered
    assert "objetivo principal" in rendered
    assert "`update_plan_discovery` antes de responder" in rendered
