from datetime import datetime
from unittest.mock import MagicMock

from src.api.models.plan import PlanUpsertInput, UserPlan
from src.services.plan_service import build_plan_singleton
from src.services.plan_tools import create_upsert_plan_tool


MINIMUM_STRATEGY = {
    "dias_disponiveis_treino": ["seg", "ter", "qui", "sex"],
    "frequencia_treino_semana": 4,
    "nivel_treinamento": "intermediario",
    "restricoes_lesoes": "nenhuma",
    "tempo_por_sessao_min": 60,
    "preferencia_ambiente": "academia",
}


def make_existing_plan() -> UserPlan:
    return UserPlan(
        user_email="user@test.com",
        title="Plano Atual",
        objective_summary="Ganho de massa com consistencia",
        start_date=datetime(2026, 4, 1),
        end_date=datetime(2026, 4, 28),
        strategy={
            "primary_goal": "gain_muscle",
            "success_criteria": ["consistencia >= 80%"],
            "constraints": [],
            "coaching_rationale": "progressao de carga semanal",
            "adaptation_policy": "ajuste continuo",
        },
        execution={
            "today_training": {
                "title": "Upper A",
                "session": {
                    "exercises": [
                        {
                            "name": "Supino Reto",
                            "sets": 4,
                            "reps": "6-8",
                            "load_guidance": "RPE 8",
                        }
                    ]
                },
            },
            "today_nutrition": {"calories": 2400, "protein_target": 160},
            "upcoming_days": [
                {
                    "date": "2026-04-02",
                    "label": "Amanha",
                    "status": "planned",
                    "training": {
                        "title": "Lower A",
                        "session": {
                            "exercises": [
                                {
                                    "name": "Agachamento",
                                    "sets": 4,
                                    "reps": "6-8",
                                    "load_guidance": "RPE 8",
                                }
                            ]
                        },
                    },
                    "nutrition": "2400 kcal",
                }
            ],
            "active_focus": "consistencia",
            "current_risks": [],
            "pending_changes": [],
        },
        checkpoints=[],
        change_reason="initial_plan",
    )


def test_upsert_plan_rejects_initial_creation_with_incomplete_execution():
    db = MagicMock()
    db.get_latest_plan.return_value = None
    tool = create_upsert_plan_tool(db, "user@test.com")

    result = tool.invoke(
        {
            "title": "Plano V1",
            "objective_summary": "Recomposicao corporal",
            "change_reason": "initial_plan",
            "strategy": MINIMUM_STRATEGY,
            "execution": {},
            "checkpoints": [],
        }
    )

    assert "Plano incompleto para criacao inicial" in result
    db.save_plan.assert_not_called()


def test_upsert_plan_allows_partial_update_when_plan_already_exists():
    db = MagicMock()
    db.get_latest_plan.return_value = make_existing_plan()
    db.save_plan.return_value = "plan_123"
    tool = create_upsert_plan_tool(db, "user@test.com")

    result = tool.invoke(
        {
            "title": "Plano Atualizado",
            "objective_summary": "Mesmo objetivo com ajuste de foco",
            "change_reason": "title_update",
            "strategy": {},
            "execution": {},
            "checkpoints": [],
        }
    )

    assert "Plano salvo com sucesso" in result
    db.save_plan.assert_called_once()


def test_build_plan_singleton_does_not_inject_placeholder_defaults():
    payload = PlanUpsertInput(
        title="Plano V1",
        objective_summary="Recomposicao corporal",
        change_reason="initial_plan",
        strategy=MINIMUM_STRATEGY,
        execution={},
        checkpoints=[],
    )

    plan = build_plan_singleton("user@test.com", None, payload)

    assert plan.execution.today_training == {}
    assert plan.execution.today_nutrition == {}
    assert plan.execution.upcoming_days == []
