from unittest.mock import MagicMock

from src.services.prompt_builder import PromptBuilder
from src.api.models.plan import PlanPromptContext


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
    snapshot = PlanPromptContext(
        title="Plano Atual",
        goal_primary="ganhar massa",
        objective_summary="Ganhar massa",
        timeline_window="2026-04-19 a 2026-06-19",
        review_cadence="semanal",
        strategy_rationale="progressao",
        constraints=["viagem quinta"],
        preferences=[],
        nutrition_targets={"calories": 3000, "protein_g": 180},
        training_split="Push/Pull/Legs",
        weekly_schedule=[{"day": "segunda", "routine_id": "push", "focus": "peito"}],
        routines=[{"id": "push", "name": "Push", "exercises": []}],
        current_summary={"active_focus": "consistencia", "next_review": "2026-04-26"},
        latest_checkpoint={"summary": "aderencia boa"},
    )

    input_data = _base_input(snapshot)
    rendered = PromptBuilder.get_prompt_template(input_data).format(**input_data)

    assert '"plan"' in rendered
    assert "Push" in rendered


def test_prompt_builder_removes_plan_section_when_snapshot_missing():
    input_data = _base_input(None)
    rendered = PromptBuilder.get_prompt_template(input_data).format(**input_data)

    assert '"plan"' in rendered
    assert "Nenhum plano mestre registrado." in rendered
