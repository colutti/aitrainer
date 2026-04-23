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


def test_upsert_plan_creation_allows_empty_strategy_when_execution_is_complete():
    db = MagicMock()
    db.get_latest_plan.return_value = None
    db.save_plan.return_value = "plan_123"
    tool = create_upsert_plan_tool(db, "user@test.com")

    result = tool.invoke(
        {
            "title": "Plano Inicial",
            "objective_summary": "Criar base de treino e nutricao",
            "change_reason": "initial_plan",
            "strategy": {},
            "execution": {
                "today_training": {
                    "title": "Full Body A",
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
                "today_nutrition": {"calories": 2400, "protein_target": 140},
                "upcoming_days": [
                    {
                        "date": "2026-04-20",
                        "label": "Amanha",
                        "status": "planned",
                        "training": {
                            "title": "Upper A",
                            "session": {
                                "exercises": [
                                    {
                                        "name": "Supino Inclinado",
                                        "sets": 4,
                                        "reps": "8-10",
                                        "load_guidance": "RPE 8",
                                    }
                                ]
                            },
                        },
                        "nutrition": "2400 kcal",
                    }
                ],
            },
            "checkpoints": [],
        }
    )

    assert result.startswith("SUCESSO_UPSERT_PLAN:")
    db.save_plan.assert_called_once()


def test_upsert_plan_creation_allows_minimal_execution_without_upcoming_days():
    db = MagicMock()
    db.get_latest_plan.return_value = None
    db.save_plan.return_value = "plan_min_123"
    tool = create_upsert_plan_tool(db, "user@test.com")

    result = tool.invoke(
        {
            "title": "Plano Minimo",
            "objective_summary": "Criar plano rapido e funcional",
            "change_reason": "initial_plan",
            "strategy": {},
            "execution": {
                "today_training": {
                    "title": "Full Body A",
                    "session": {
                        "exercises": [
                            {
                                "name": "Agachamento",
                                "sets": 3,
                                "reps": "8-10",
                                "load_guidance": "RPE 7-8",
                            }
                        ]
                    },
                },
                "today_nutrition": {"calories": 2300, "protein_target": 150},
            },
            "checkpoints": [],
        }
    )

    assert result.startswith("SUCESSO_UPSERT_PLAN:")
    db.save_plan.assert_called_once()


def test_upsert_plan_incomplete_error_returns_actionable_template():
    db = MagicMock()
    db.get_latest_plan.return_value = None
    tool = create_upsert_plan_tool(db, "user@test.com")

    result = tool.invoke(
        {
            "title": "Plano Incompleto",
            "objective_summary": "Teste de erro",
            "change_reason": "initial_plan",
            "strategy": {},
            "execution": {"today_training": {}},
            "checkpoints": [],
        }
    )

    assert result.startswith("ERRO_UPSERT_PLAN_INCOMPLETO:")
    assert "today_nutrition" in result
    assert "payload minimo" in result.lower()
    assert '"today_training"' in result
    assert '"today_nutrition"' in result


def test_upsert_plan_rejects_duplicate_payload_in_same_turn():
    db = MagicMock()
    db.get_latest_plan.return_value = make_existing_plan()
    db.save_plan.return_value = "plan_123"
    tool = create_upsert_plan_tool(db, "user@test.com")
    payload = {
        "title": "Plano Atualizado",
        "objective_summary": "Mesmo objetivo com ajuste de foco",
        "change_reason": "title_update",
        "strategy": {},
        "execution": {},
        "checkpoints": [],
    }

    first = tool.invoke(payload)
    second = tool.invoke(payload)

    assert first.startswith("SUCESSO_UPSERT_PLAN:")
    assert second.startswith("ERRO_UPSERT_PLAN_REPETIDO:")
    db.save_plan.assert_called_once()


def test_upsert_plan_loop_guard_after_multiple_calls_same_turn():
    db = MagicMock()
    db.get_latest_plan.return_value = make_existing_plan()
    db.save_plan.return_value = "plan_123"
    tool = create_upsert_plan_tool(db, "user@test.com")

    payload_1 = {
        "title": "Plano 1",
        "objective_summary": "Ajuste 1",
        "change_reason": "ajuste_1",
        "strategy": {},
        "execution": {},
        "checkpoints": [],
    }
    payload_2 = {
        "title": "Plano 2",
        "objective_summary": "Ajuste 2",
        "change_reason": "ajuste_2",
        "strategy": {"any": "value"},
        "execution": {"active_focus": "consistencia"},
        "checkpoints": [],
    }
    payload_3 = {
        "title": "Plano 3",
        "objective_summary": "Ajuste 3",
        "change_reason": "ajuste_3",
        "strategy": {"x": 1},
        "execution": {"pending_changes": []},
        "checkpoints": [],
    }
    payload_4 = {
        "title": "Plano 4",
        "objective_summary": "Ajuste 4",
        "change_reason": "ajuste_4",
        "strategy": {"y": 2},
        "execution": {"current_risks": []},
        "checkpoints": [],
    }

    first = tool.invoke(payload_1)
    second = tool.invoke(payload_2)
    third = tool.invoke(payload_3)
    fourth = tool.invoke(payload_4)

    assert first.startswith("SUCESSO_UPSERT_PLAN:")
    assert second.startswith("SUCESSO_UPSERT_PLAN:")
    assert third.startswith("SUCESSO_UPSERT_PLAN:")
    assert fourth.startswith("ERRO_UPSERT_PLAN_LOOP_GUARD:")
    assert db.save_plan.call_count == 3


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
