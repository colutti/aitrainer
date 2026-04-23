from datetime import datetime
from unittest.mock import MagicMock

from src.api.models.plan import ActivePlan, PlanStatus
from src.services.plan_tools import (
    create_plan_help_tool,
    create_get_plan_tool,
    create_get_plan_context_tool,
    create_create_plan_proposal_tool,
    create_propose_plan_adjustment_tool,
    create_approve_plan_change_tool,
    create_get_today_plan_brief_tool,
)

MINIMUM_STRATEGY = {
    "dias_disponiveis_treino": ["seg", "ter", "qui", "sex"],
    "frequencia_treino_semana": 4,
    "nivel_treinamento": "intermediario",
    "restricoes_lesoes": "nenhuma",
    "tempo_por_sessao_min": 60,
    "preferencia_ambiente": "academia",
}


def make_active_plan(version=1, status=PlanStatus.ACTIVE) -> ActivePlan:
    return ActivePlan(
        user_email="user@test.com",
        status=status,
        title="Plano Atual",
        objective_summary="Ganhar massa",
        start_date=datetime(2026, 4, 19),
        end_date=datetime(2026, 6, 19),
        version=version,
        strategy={
            "primary_goal": "gain_muscle",
            "success_criteria": ["volume"],
            "constraints": ["viagem"],
            "coaching_rationale": "superavit",
            "adaptation_policy": "approval_required",
        },
        execution={
            "today_training": {
                "title": "Push",
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
            "today_nutrition": {"calories": 3000, "protein_target": 180},
            "upcoming_days": [
                {
                    "date": "2026-04-20",
                    "label": "Amanha",
                    "status": "planned",
                    "training": {
                        "title": "Pull",
                        "session": {
                            "exercises": [
                                {
                                    "name": "Remada Curvada",
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
            "active_focus": "consistencia",
            "current_risks": [],
            "pending_changes": [],
        },
        tracking={
            "checkpoints": [{"summary": "ok"}],
            "adherence_snapshot": {"training": "ok", "nutrition": "ok"},
            "progress_snapshot": {"status": "on_track"},
            "last_ai_assessment": None,
            "last_user_acknowledgement": None,
        },
        governance={"change_reason": None, "approval_request": None},
    )


def test_get_plan_tool_returns_serialized_plan():
    db = MagicMock()
    db.get_plan.return_value = make_active_plan()

    tool = create_get_plan_tool(db, "user@test.com")
    result = tool.invoke({})

    assert "Plano Atual" in result
    db.get_plan.assert_called_once_with("user@test.com")


def test_plan_help_tool_returns_markdown_with_required_flow():
    db = MagicMock()
    tool = create_plan_help_tool(db, "user@test.com")
    result = tool.invoke({})

    assert "## Fluxo obrigatorio" in result
    assert "discovery -> criacao/edicao direta -> acompanhamento continuo" in result
    assert "dias_disponiveis_treino" in result
    assert "tempo_por_sessao_min" in result
    assert "today_training" in result
    assert "today_nutrition" in result
    assert "upcoming_days" in result


def test_get_plan_context_tool_returns_compact_snapshot(monkeypatch):
    db = MagicMock()
    db.get_plan.return_value = make_active_plan()
    db.get_workout_logs.return_value = []
    db.get_nutrition_logs_by_date_range.return_value = []
    monkeypatch.setattr(
        "src.services.plan_tools.AdaptiveTDEEService",
        MagicMock(
            return_value=MagicMock(
                calculate_tdee=MagicMock(return_value={"weight_change_per_week": -0.2})
            )
        ),
    )

    tool = create_get_plan_context_tool(db, "user@test.com")
    result = tool.invoke({})

    assert "Treino de hoje" in result
    assert "Push" in result
    assert "Aderencia 7d:" in result
    assert "Tendencia de peso:" in result


def test_create_plan_proposal_tool_persists_active_version():
    db = MagicMock()
    db.get_latest_plan.return_value = make_active_plan(version=1)
    db.save_plan.return_value = "plan_2"

    tool = create_create_plan_proposal_tool(db, "user@test.com")
    result = tool.invoke(
        {
            "title": "Plano V2",
            "objective_summary": "ajuste",
            "change_reason": "baixa_aderencia",
            "strategy": MINIMUM_STRATEGY,
            "execution": {
                "today_training": {
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
                "today_nutrition": {"calories": 2400, "protein_target": 140},
                "upcoming_days": [
                    {
                        "date": "2026-04-20",
                        "label": "Amanha",
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
                        "status": "planned",
                    }
                ],
            },
            "tracking": {},
        }
    )

    assert "sem aprovacao necessaria" in result.lower()
    saved_plan = db.save_plan.call_args.args[0]
    assert saved_plan.status == PlanStatus.ACTIVE
    assert saved_plan.version == 1


def test_create_plan_proposal_tool_backfills_minimum_execution_when_empty():
    db = MagicMock()
    db.get_latest_plan.return_value = None
    db.save_plan.return_value = "plan_2"

    tool = create_create_plan_proposal_tool(db, "user@test.com")
    result = tool.invoke(
        {
            "title": "Plano Recomposicao",
            "objective_summary": "Recomposicao corporal com foco em consistencia",
            "change_reason": "initial_plan",
            "strategy": MINIMUM_STRATEGY,
            "execution": {},
            "tracking": {},
        }
    )

    assert "Plano incompleto" in result
    db.save_plan.assert_not_called()


def test_create_plan_proposal_tool_rejects_when_mandatory_intake_fields_missing():
    db = MagicMock()
    db.get_latest_plan.return_value = None

    tool = create_create_plan_proposal_tool(db, "user@test.com")
    result = tool.invoke(
        {
            "title": "Plano Recomposicao",
            "objective_summary": "Recomposicao corporal",
            "change_reason": "initial_plan",
            "strategy": {},
            "execution": {},
            "tracking": {},
        }
    )

    assert "Plano incompleto" in result
    assert "dias_disponiveis_treino" in result
    db.save_plan.assert_not_called()


def test_propose_plan_adjustment_tool_requires_structured_plan_update():
    db = MagicMock()
    db.get_latest_plan.return_value = make_active_plan(version=3)

    tool = create_propose_plan_adjustment_tool(db, "user@test.com")
    result = tool.invoke({"change_reason": "rotina_mudou", "proposal_summary": "ajuste de volume"})

    assert "use create_plan_proposal" in result.lower()
    db.save_plan.assert_not_called()


def test_create_plan_proposal_tool_rejects_when_training_has_no_exercises():
    db = MagicMock()
    db.get_latest_plan.return_value = None

    tool = create_create_plan_proposal_tool(db, "user@test.com")
    result = tool.invoke(
        {
            "title": "Plano V1",
            "objective_summary": "ajuste",
            "change_reason": "initial_plan",
            "strategy": MINIMUM_STRATEGY,
            "execution": {
                "today_training": {"title": "Lower A", "session": {"notes": "sem exercicios"}},
                "today_nutrition": {"calories": 2400, "protein_target": 140},
                "upcoming_days": [{"date": "2026-04-20", "label": "Amanha"}],
            },
            "tracking": {},
        }
    )

    assert "training_exercises" in result
    db.save_plan.assert_not_called()


def test_create_plan_proposal_tool_rejects_when_upcoming_days_have_no_exercises():
    db = MagicMock()
    db.get_latest_plan.return_value = None

    tool = create_create_plan_proposal_tool(db, "user@test.com")
    result = tool.invoke(
        {
            "title": "Plano V1",
            "objective_summary": "ajuste",
            "change_reason": "initial_plan",
            "strategy": MINIMUM_STRATEGY,
            "execution": {
                "today_training": {
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
                "today_nutrition": {"calories": 2400, "protein_target": 140},
                "upcoming_days": [
                    {
                        "date": "2026-04-20",
                        "label": "Amanha",
                        "status": "planned",
                        "training": "Full Body A",
                        "nutrition": "2400 kcal",
                    }
                ],
            },
            "tracking": {},
        }
    )

    assert "upcoming_training_exercises" in result
    db.save_plan.assert_not_called()


def test_propose_plan_adjustment_rejects_when_base_plan_has_no_exercises():
    db = MagicMock()
    invalid_plan = make_active_plan(version=3)
    invalid_plan.execution.today_training = {"title": "Lower A", "session": None}
    db.get_latest_plan.return_value = invalid_plan

    tool = create_propose_plan_adjustment_tool(db, "user@test.com")
    result = tool.invoke(
        {"change_reason": "rotina_mudou", "proposal_summary": "ajuste de volume"}
    )

    assert "use create_plan_proposal" in result.lower()
    db.save_plan.assert_not_called()


def test_approve_plan_change_tool_delegates_approval():
    db = MagicMock()
    db.approve_plan.return_value = True

    tool = create_approve_plan_change_tool(db, "user@test.com")
    result = tool.invoke({"version": 5})

    assert "aprovado" in result.lower()
    db.approve_plan.assert_called_once_with("user@test.com", 5)


def test_get_today_plan_brief_tool_returns_training_and_nutrition():
    db = MagicMock()
    db.get_plan.return_value = make_active_plan()

    tool = create_get_today_plan_brief_tool(db, "user@test.com")
    result = tool.invoke({})

    assert "Push" in result
    assert "3000" in result
