from datetime import datetime
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.api.main import app
from src.core.deps import get_mongo_database
from src.services.auth import verify_token
from src.api.models.plan import ActivePlan, PlanStatus


client = TestClient(app)


def make_plan(version=1, status=PlanStatus.ACTIVE):
    return ActivePlan(
        user_email="test@example.com",
        status=status,
        title="Plano Atual",
        objective_summary="Ganhar massa",
        start_date=datetime(2026, 4, 19),
        end_date=datetime(2026, 6, 19),
        version=version,
        strategy={
            "primary_goal": "gain_muscle",
            "success_criteria": ["volume"],
            "constraints": [],
            "coaching_rationale": "superavit",
            "adaptation_policy": "approval_required",
        },
        execution={
            "today_training": {"title": "Push"},
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
            "checkpoints": [],
            "adherence_snapshot": {"training": "ok", "nutrition": "ok"},
            "progress_snapshot": {"status": "on_track"},
            "last_ai_assessment": None,
            "last_user_acknowledgement": None,
        },
        governance={"change_reason": None, "approval_request": None},
    )


def test_get_plan_returns_plan_payload():
    mock_db = MagicMock()
    mock_db.get_plan.return_value = make_plan()
    mock_db.get_latest_plan.return_value = make_plan()

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    try:
        response = client.get("/plan")
        assert response.status_code == 200
        assert response.json()["title"] == "Plano Atual"
    finally:
        app.dependency_overrides.clear()


def test_get_plan_returns_404_when_missing():
    mock_db = MagicMock()
    mock_db.get_plan.return_value = None
    mock_db.get_latest_plan.return_value = None

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    try:
        response = client.get("/plan")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_list_versions_returns_latest_first():
    mock_db = MagicMock()
    mock_db.list_plan_versions.return_value = [
        make_plan(version=2, status=PlanStatus.AWAITING_APPROVAL),
        make_plan(version=1),
    ]

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    try:
        response = client.get("/plan/versions")
        assert response.status_code == 200
        assert response.json()[0]["version"] == 2
    finally:
        app.dependency_overrides.clear()


def test_create_plan_proposal_persists_active_plan():
    mock_db = MagicMock()
    mock_db.get_latest_plan.return_value = make_plan(version=1)
    mock_db.save_plan.return_value = "plan_2"

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    payload = {
        "title": "Plano V2",
        "objective_summary": "ajuste",
        "change_reason": "baixa_aderencia",
        "strategy": {
            "dias_disponiveis_treino": ["seg", "ter", "qui", "sex"],
            "frequencia_treino_semana": 4,
            "nivel_treinamento": "intermediario",
            "restricoes_lesoes": "nenhuma",
            "tempo_por_sessao_min": 60,
            "preferencia_ambiente": "academia",
        },
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

    try:
        response = client.post("/plan/proposal", json=payload)
        assert response.status_code == 200
        assert response.json()["id"] == "plan_2"
        assert response.json()["status"] == "active"
    finally:
        app.dependency_overrides.clear()


def test_approve_plan_version():
    mock_db = MagicMock()

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    try:
        response = client.post("/plan/approve", json={"version": 2})
        assert response.status_code == 410
        assert "Fluxo de aprovacao foi removido" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_get_plan_returns_current_active_version():
    mock_db = MagicMock()
    mock_db.get_plan.return_value = make_plan(version=1, status=PlanStatus.ACTIVE)
    mock_db.get_latest_plan.return_value = make_plan(version=2, status=PlanStatus.ARCHIVED)

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    try:
        response = client.get("/plan")
        assert response.status_code == 200
        assert response.json()["version"] == 1
        assert response.json()["status"] == "active"
    finally:
        app.dependency_overrides.clear()


def test_create_plan_proposal_rejects_missing_structured_fields():
    mock_db = MagicMock()
    mock_db.get_latest_plan.return_value = None

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    payload = {
        "title": "Plano V2",
        "objective_summary": "ajuste",
        "change_reason": "initial_plan",
        "strategy": {},
        "execution": {},
        "tracking": {},
    }

    try:
        response = client.post("/plan/proposal", json=payload)
        assert response.status_code == 422
        assert "Plano incompleto" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_create_plan_proposal_rejects_when_missing_training_exercises():
    mock_db = MagicMock()
    mock_db.get_latest_plan.return_value = None

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    payload = {
        "title": "Plano V2",
        "objective_summary": "ajuste",
        "change_reason": "initial_plan",
        "strategy": {
            "dias_disponiveis_treino": ["seg", "ter", "qui", "sex"],
            "frequencia_treino_semana": 4,
            "nivel_treinamento": "intermediario",
            "restricoes_lesoes": "nenhuma",
            "tempo_por_sessao_min": 60,
            "preferencia_ambiente": "academia",
        },
        "execution": {
            "today_training": {"title": "Lower A", "session": {"notes": "sem exercicios"}},
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

    try:
        response = client.post("/plan/proposal", json=payload)
        assert response.status_code == 422
        assert "training_exercises" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_create_plan_proposal_rejects_when_upcoming_lacks_exercises():
    mock_db = MagicMock()
    mock_db.get_latest_plan.return_value = None

    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    payload = {
        "title": "Plano V2",
        "objective_summary": "ajuste",
        "change_reason": "initial_plan",
        "strategy": {
            "dias_disponiveis_treino": ["seg", "ter", "qui", "sex"],
            "frequencia_treino_semana": 4,
            "nivel_treinamento": "intermediario",
            "restricoes_lesoes": "nenhuma",
            "tempo_por_sessao_min": 60,
            "preferencia_ambiente": "academia",
        },
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
                    "training": "Upper A",
                    "nutrition": "2400 kcal",
                }
            ],
        },
        "tracking": {},
    }

    try:
        response = client.post("/plan/proposal", json=payload)
        assert response.status_code == 422
        assert "upcoming_training_exercises" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
