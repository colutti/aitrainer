from copy import deepcopy
from datetime import date, datetime
from unittest.mock import MagicMock, patch

from bson import ObjectId
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.models.nutrition_log import NutritionLog
from src.core.deps import get_mongo_database
from src.api.models.weight_log import WeightLog
from src.api.models.workout_log import ExerciseLog, WorkoutLog
from src.repositories.nutrition_repository import NutritionRepository
from src.repositories.plan_repository import PlanRepository
from src.repositories.weight_repository import WeightRepository
from src.repositories.workout_repository import WorkoutRepository
from src.services.auth import verify_token
from src.api.models.plan import (
    ConflictRule,
    IntensityPrescription,
    NutritionDailyTargets,
    PlanAlignment,
    PlanCreateInput,
    PlanDiscoveryState,
    PlanGoal,
    PlanNutrition,
    PlanTimeline,
    PlanTracking,
    PlanUserContext,
    ProgressMarker,
    ProgressionRule,
    RepRange,
    SuccessMetric,
    TrainingExercise,
    PlanTraining,
    TrainingRoutine,
    UserPlan,
    WeeklyScheduleItem,
)
from src.services.plan_service import build_plan_from_create_input


client = TestClient(app)


class FakeUpdateResult:
    def __init__(
        self,
        *,
        upserted_id: ObjectId | None = None,
        modified_count: int = 0,
    ) -> None:
        self.upserted_id = upserted_id
        self.modified_count = modified_count


class FakeReplaceResult:
    def __init__(self, matched_count: int) -> None:
        self.matched_count = matched_count


class FakeDeleteResult:
    def __init__(self, deleted_count: int) -> None:
        self.deleted_count = deleted_count


class FakeInsertResult:
    def __init__(self, inserted_id: ObjectId) -> None:
        self.inserted_id = inserted_id


class FakeCursor:
    def __init__(self, docs: list[dict]) -> None:
        self._docs = docs

    def sort(self, field: str, direction: int) -> "FakeCursor":
        reverse = direction < 0
        self._docs.sort(key=lambda doc: doc.get(field), reverse=reverse)
        return self

    def skip(self, amount: int) -> "FakeCursor":
        self._docs = self._docs[amount:]
        return self

    def limit(self, amount: int) -> "FakeCursor":
        self._docs = self._docs[:amount]
        return self

    def __iter__(self):
        return iter([deepcopy(doc) for doc in self._docs])


class FakeCollection:
    def __init__(self) -> None:
        self.docs: list[dict] = []

    def create_index(self, *_args, **_kwargs) -> None:
        return None

    def _matches(self, doc: dict, query: dict) -> bool:
        for key, value in query.items():
            if isinstance(value, dict):
                current = doc.get(key)
                if "$ne" in value and current == value["$ne"]:
                    return False
                if "$gte" in value and current < value["$gte"]:
                    return False
                if "$lte" in value and current > value["$lte"]:
                    return False
                continue
            if doc.get(key) != value:
                return False
        return True

    def update_one(self, query: dict, update: dict, upsert: bool = False) -> FakeUpdateResult:
        for doc in self.docs:
            if self._matches(doc, query):
                original = deepcopy(doc)
                for key, value in update.get("$set", {}).items():
                    doc[key] = deepcopy(value)
                for key, value in update.get("$inc", {}).items():
                    doc[key] = doc.get(key, 0) + value
                for key in update.get("$unset", {}):
                    doc.pop(key, None)
                return FakeUpdateResult(
                    modified_count=0 if doc == original else 1,
                )

        if upsert:
            inserted_id = ObjectId()
            new_doc = {"_id": inserted_id, **deepcopy(query), **deepcopy(update.get("$set", {}))}
            self.docs.append(new_doc)
            return FakeUpdateResult(upserted_id=inserted_id, modified_count=0)

        return FakeUpdateResult(modified_count=0)

    def find_one(
        self,
        query: dict,
        projection: dict | None = None,
        sort: list[tuple[str, int]] | None = None,
    ) -> dict | None:
        docs = [doc for doc in self.docs if self._matches(doc, query)]
        if sort:
            field, direction = sort[0]
            docs.sort(key=lambda doc: doc.get(field), reverse=direction < 0)
        if not docs:
            return None
        doc = deepcopy(docs[0])
        if projection:
            keep = {key for key, value in projection.items() if value}
            if keep:
                doc = {key: value for key, value in doc.items() if key in keep or key == "_id"}
        return doc

    def find(self, query: dict, projection: dict | None = None) -> FakeCursor:
        docs = [deepcopy(doc) for doc in self.docs if self._matches(doc, query)]
        if projection:
            keep = {key for key, value in projection.items() if value}
            if keep:
                docs = [
                    {key: value for key, value in doc.items() if key in keep or key == "_id"}
                    for doc in docs
                ]
        return FakeCursor(docs)

    def replace_one(self, query: dict, data: dict) -> FakeReplaceResult:
        for index, doc in enumerate(self.docs):
            if self._matches(doc, query):
                self.docs[index] = {"_id": doc["_id"], **deepcopy(data)}
                return FakeReplaceResult(matched_count=1)
        return FakeReplaceResult(matched_count=0)

    def insert_one(self, data: dict) -> FakeInsertResult:
        inserted_id = ObjectId()
        self.docs.append({"_id": inserted_id, **deepcopy(data)})
        return FakeInsertResult(inserted_id)

    def delete_one(self, query: dict) -> FakeDeleteResult:
        for index, doc in enumerate(self.docs):
            if self._matches(doc, query):
                del self.docs[index]
                return FakeDeleteResult(deleted_count=1)
        return FakeDeleteResult(deleted_count=0)

    def delete_many(self, query: dict) -> None:
        self.docs = [doc for doc in self.docs if not self._matches(doc, query)]

    def count_documents(self, query: dict) -> int:
        return len([doc for doc in self.docs if self._matches(doc, query)])

    def find_one_and_update(
        self,
        query: dict,
        update: dict,
        upsert: bool = False,
        return_document=None,
    ) -> dict | None:
        result = self.update_one(query, update, upsert=upsert)
        if result.upserted_id is not None:
            return self.find_one({"_id": result.upserted_id})
        return self.find_one(query)


class FakeDatabase:
    def __init__(self) -> None:
        self._collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self._collections:
            self._collections[name] = FakeCollection()
        return self._collections[name]


class StatefulPlanDb:
    def __init__(self, database: FakeDatabase | None = None) -> None:
        self.database = database or FakeDatabase()
        self.plans = PlanRepository(self.database)
        self.workouts_repo = WorkoutRepository(self.database)
        self.nutrition = NutritionRepository(self.database)
        self.weight = WeightRepository(self.database)

    def get_plan(self, user_email: str):
        return self.plans.get_plan(user_email)

    def save_plan(self, plan):
        return self.plans.save_plan(plan)

    def get_plan_discovery(self, user_email: str):
        return self.plans.get_discovery(user_email)

    def save_plan_discovery(self, discovery):
        return self.plans.save_discovery(discovery)

    def clear_plan_discovery(self, user_email: str):
        return self.plans.clear_discovery(user_email)

    def get_workout_logs(self, user_email: str, limit: int = 30):
        return self.workouts_repo.get_logs(user_email, limit)

    def get_weight_logs(self, user_email: str, limit: int = 30):
        return self.weight.get_logs(user_email, limit)

    def get_nutrition_stats(self, user_email: str):
        return self.nutrition.get_stats(user_email, tdee_service=None)


def make_create_input() -> PlanCreateInput:
    return PlanCreateInput(
        title="Plano Mestre",
        goal=PlanGoal(
            primary_goal="muscle_gain",
            outcome_summary="Ganhar massa com superavit controlado",
            success_metrics=[
                SuccessMetric(
                    metric_name="peso",
                    target_value=75,
                    unit="kg",
                    direction="increase",
                    deadline=date(2026, 8, 1),
                )
            ],
        ),
        timeline=PlanTimeline(
            start_date=date(2026, 5, 1),
            target_date=date(2026, 8, 1),
            review_cadence_days=7,
            current_phase="acumulacao",
        ),
        user_context=PlanUserContext(
            training_days_available=["monday", "thursday"],
            session_duration_min=60,
            constraints=["nenhuma"],
            preferences=["academia"],
            available_equipment=["barra"],
        ),
        training=PlanTraining(
            split_name="upper_lower",
            frequency_per_week=2,
            session_duration_min=60,
            routines=[
                TrainingRoutine(
                    id="upper_a",
                    name="Upper A",
                    exercises=[
                        TrainingExercise(
                            name="Supino Reto",
                            sets=4,
                            rep_range=RepRange(min_reps=6, max_reps=8),
                            intensity=IntensityPrescription(
                                prescription_type="rpe",
                                target="8",
                            ),
                            progression_rule=ProgressionRule(
                                method="double_progression",
                                increase_when="bater topo da faixa",
                                hold_when="ficar no meio da faixa",
                                deload_when="regredir por 2 semanas",
                            ),
                        )
                    ],
                ),
                TrainingRoutine(
                    id="lower_a",
                    name="Lower A",
                    exercises=[
                        TrainingExercise(
                            name="Agachamento",
                            sets=4,
                            rep_range=RepRange(min_reps=5, max_reps=8),
                            intensity=IntensityPrescription(
                                prescription_type="rpe",
                                target="8",
                            ),
                            progression_rule=ProgressionRule(
                                method="linear_load",
                                increase_when="completar volume com tecnica boa",
                                hold_when="tecnica instavel",
                                deload_when="fadiga acumulada por 2 semanas",
                            ),
                        )
                    ],
                ),
            ],
            weekly_schedule=[
                WeeklyScheduleItem(day="monday", routine_id="upper_a", focus="upper", type="training"),
                WeeklyScheduleItem(day="thursday", routine_id="lower_a", focus="lower", type="training"),
            ],
        ),
        nutrition=PlanNutrition(
            daily_targets=NutritionDailyTargets(
                calories_kcal=2600,
                protein_g=160,
                carbs_g=315,
                fat_g=75,
            ),
            strategy="superavit leve",
            adherence_target_pct=85,
        ),
        alignment=PlanAlignment(
            training_nutrition_rationale="Superavit leve para hipertrofia.",
            energy_strategy="surplus",
            recovery_assumptions=["dormir 7h"],
            conflict_rules=[ConflictRule(trigger="queda de performance", action="revisar recuperacao")],
        ),
        tracking=PlanTracking(
            workout_adherence_target_pct=85,
            nutrition_adherence_target_pct=80,
            progress_markers=[ProgressMarker(name="carga no supino", source="workouts", target_summary="subir carga ou reps")],
            review_questions=["A recuperacao esta coerente?"],
        ),
    )


def make_plan() -> UserPlan:
    return build_plan_from_create_input("test@example.com", make_create_input())


def override_db(mock_db: MagicMock) -> None:
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db


def test_get_plan_returns_plan_payload():
    mock_db = MagicMock()
    mock_db.get_plan.return_value = make_plan()
    override_db(mock_db)

    try:
        response = client.get("/plan")
        assert response.status_code == 200
        assert response.json()["title"] == "Plano Mestre"
    finally:
        app.dependency_overrides.clear()


def test_get_plan_status_returns_no_plan():
    mock_db = MagicMock()
    mock_db.get_plan.return_value = None
    mock_db.get_plan_discovery.return_value = None
    override_db(mock_db)

    try:
        response = client.get("/plan/status")
        assert response.status_code == 200
        assert response.json()["status"] == "NO_PLAN"
        assert "goal_primary" in response.json()["missing_fields"]
    finally:
        app.dependency_overrides.clear()


def test_create_plan_from_discovery_requires_complete_discovery():
    mock_db = MagicMock()
    mock_db.get_plan_discovery.return_value = None
    override_db(mock_db)

    try:
        response = client.post("/plan/create-from-discovery", json=make_create_input().model_dump(mode="json"))
        assert response.status_code == 422
        assert "Discovery incompleto" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_create_plan_from_discovery_saves_plan_and_clears_draft():
    mock_db = MagicMock()
    mock_db.get_plan_discovery.return_value = PlanDiscoveryState(
        user_email="test@example.com",
        goal_primary="muscle_gain",
        goal_summary="Ganhar massa",
        target_date=date(2026, 8, 1),
        training_days_available=["monday", "thursday"],
        session_duration_min=60,
        constraints=["nenhuma"],
        preferences=["academia"],
        available_equipment=["barra"],
        metabolism_confirmed=True,
        missing_fields=[],
    )
    mock_db.save_plan.return_value = "plan_1"
    override_db(mock_db)

    try:
        response = client.post("/plan/create-from-discovery", json=make_create_input().model_dump(mode="json"))
        assert response.status_code == 200
        assert response.json()["id"] == "plan_1"
        saved_plan = mock_db.save_plan.call_args.args[0]
        assert saved_plan.user_email == "test@example.com"
        assert saved_plan.title == "Plano Mestre"
        assert saved_plan.goal.primary_goal == "muscle_gain"
        assert saved_plan.nutrition.daily_targets.calories_kcal == 2600
        assert saved_plan.training.routines[0].exercises[0].name == "Supino Reto"
        mock_db.clear_plan_discovery.assert_called_once_with("test@example.com")
    finally:
        app.dependency_overrides.clear()


def test_create_plan_from_discovery_rejects_semantically_inconsistent_payload():
    mock_db = MagicMock()
    mock_db.get_plan_discovery.return_value = PlanDiscoveryState(
        user_email="test@example.com",
        goal_primary="muscle_gain",
        goal_summary="Ganhar massa",
        target_date=date(2026, 8, 1),
        training_days_available=["monday", "thursday"],
        session_duration_min=60,
        constraints=["nenhuma"],
        preferences=["academia"],
        available_equipment=["barra"],
        metabolism_confirmed=True,
        missing_fields=[],
    )
    override_db(mock_db)

    inconsistent_payload = make_create_input()
    inconsistent_payload.goal.outcome_summary = "Entrar em deficit agressivo para secar"
    inconsistent_payload.alignment.energy_strategy = "surplus"

    try:
        response = client.post(
            "/plan/create-from-discovery",
            json=inconsistent_payload.model_dump(mode="json"),
        )
        assert response.status_code == 422
        assert "semantic consistency validation failed" in response.json()["detail"]
        mock_db.save_plan.assert_not_called()
        mock_db.clear_plan_discovery.assert_not_called()
    finally:
        app.dependency_overrides.clear()


def test_update_plan_discovery_persists_all_supported_fields():
    mock_db = MagicMock()
    mock_db.get_plan_discovery.return_value = None
    mock_db.save_plan_discovery.return_value = "discovery_1"
    override_db(mock_db)

    payload = {
        "goal_primary": "muscle_gain",
        "goal_summary": "Ganhar massa com menos gordura",
        "target_date": "2026-08-01",
        "training_days_available": ["monday", "thursday", "saturday"],
        "session_duration_min": 70,
        "constraints": ["joelho sensivel"],
        "preferences": ["treino curto e intenso"],
        "available_equipment": ["barra", "halteres", "cabo"],
        "training_level": "intermediate",
        "nutrition_preferences": ["alto teor proteico"],
        "metabolism_confirmed": True,
    }

    try:
        response = client.post("/plan/discovery", json=payload)
        assert response.status_code == 200
        assert response.json()["id"] == "discovery_1"
        saved_discovery = mock_db.save_plan_discovery.call_args.args[0]
        assert saved_discovery.user_email == "test@example.com"
        assert saved_discovery.goal_primary == "muscle_gain"
        assert saved_discovery.goal_summary == "Ganhar massa com menos gordura"
        assert saved_discovery.training_days_available == ["monday", "thursday", "saturday"]
        assert saved_discovery.session_duration_min == 70
        assert saved_discovery.constraints == ["joelho sensivel"]
        assert saved_discovery.preferences == ["treino curto e intenso"]
        assert saved_discovery.available_equipment == ["barra", "halteres", "cabo"]
        assert saved_discovery.training_level == "intermediate"
        assert saved_discovery.nutrition_preferences == ["alto teor proteico"]
        assert saved_discovery.metabolism_confirmed is True
        assert saved_discovery.missing_fields == []
    finally:
        app.dependency_overrides.clear()


def test_patch_plan_section_updates_active_plan():
    mock_db = MagicMock()
    mock_db.get_plan.return_value = make_plan()
    mock_db.save_plan.return_value = "plan_2"
    override_db(mock_db)

    payload = {
        "section": "nutrition",
        "nutrition": {
            "daily_targets": {
                "calories_kcal": 2800,
                "protein_g": 170,
                "carbs_g": 330,
                "fat_g": 80,
            },
            "strategy": "superavit moderado",
            "adherence_target_pct": 85,
        },
    }

    try:
        response = client.patch("/plan/section", json=payload)
        assert response.status_code == 200
        assert response.json()["id"] == "plan_2"
        saved_plan = mock_db.save_plan.call_args.args[0]
        assert saved_plan.nutrition.daily_targets.calories_kcal == 2800
        assert saved_plan.nutrition.daily_targets.protein_g == 170
        assert saved_plan.nutrition.strategy == "superavit moderado"
        assert saved_plan.tracking.workout_adherence_target_pct == 85
    finally:
        app.dependency_overrides.clear()


def test_patch_plan_training_preserves_review_reason_and_updates_advanced_fields():
    mock_db = MagicMock()
    plan = make_plan()
    plan.review_reason = "Plano criado apos discovery inicial"
    mock_db.get_plan.return_value = plan
    mock_db.save_plan.return_value = "plan_training_advanced"
    override_db(mock_db)

    payload = {
        "section": "training",
        "training": {
            "split_name": "push_pull_legs",
            "frequency_per_week": 2,
            "session_duration_min": 75,
            "routines": [
                {
                    "id": "push_a",
                    "name": "Push A",
                    "objective": "Foco em peito e ombros",
                    "exercises": [
                        {
                            "name": "Supino Inclinado",
                            "external_exercise_template_id": "hevy_ex_101",
                            "sets": 4,
                            "rep_range": {"min_reps": 6, "max_reps": 10},
                            "intensity": {
                                "prescription_type": "rir",
                                "target": "2",
                            },
                            "rest_seconds": 120,
                            "progression_rule": {
                                "method": "double_progression",
                                "increase_when": "bater 10 reps em todas as series",
                                "hold_when": "ficar abaixo de 8 reps em alguma serie",
                                "deload_when": "estagnar por 3 semanas",
                            },
                            "notes": "Priorizar cadencia controlada",
                        }
                    ],
                    "external_bindings": [
                        {
                            "provider": "hevy",
                            "external_routine_id": "hevy_routine_42",
                            "external_routine_name": "Push Day",
                            "last_synced_at": "2026-05-01T10:00:00Z",
                            "last_sync_error": "sync timeout anterior",
                        }
                    ],
                },
                {
                    "id": "recovery_day",
                    "name": "Recovery",
                    "objective": "Recuperacao ativa",
                    "exercises": [
                        {
                            "name": "Caminhada inclinada",
                            "sets": 1,
                            "rep_range": {"min_reps": 20, "max_reps": 20},
                            "intensity": {
                                "prescription_type": "guidance",
                                "target": "zona 2",
                            },
                            "progression_rule": {
                                "method": "maintenance",
                                "increase_when": "nao se aplica",
                                "hold_when": "manter consistencia",
                                "deload_when": "nao se aplica",
                            },
                            "notes": "Usar como sessao leve",
                        }
                    ],
                    "external_bindings": [],
                },
            ],
            "weekly_schedule": [
                {
                    "day": "monday",
                    "routine_id": "push_a",
                    "focus": "push",
                    "type": "training",
                },
                {
                    "day": "thursday",
                    "routine_id": "recovery_day",
                    "focus": "recovery",
                    "type": "training",
                },
            ],
        },
    }

    try:
        with patch(
            "src.api.endpoints.plan.sync_training_with_hevy_if_needed",
            side_effect=lambda **kwargs: kwargs["updated_plan"],
        ):
            response = client.patch("/plan/section", json=payload)
        assert response.status_code == 200
        assert response.json()["id"] == "plan_training_advanced"
        saved_plan = mock_db.save_plan.call_args.args[0]
        assert saved_plan.review_reason == "Plano criado apos discovery inicial"
        assert saved_plan.training.split_name == "push_pull_legs"
        assert saved_plan.training.session_duration_min == 75
        assert saved_plan.training.routines[0].objective == "Foco em peito e ombros"
        assert (
            saved_plan.training.routines[0].exercises[0].external_exercise_template_id
            == "hevy_ex_101"
        )
        assert saved_plan.training.routines[0].exercises[0].rest_seconds == 120
        assert (
            saved_plan.training.routines[0].exercises[0].notes
            == "Priorizar cadencia controlada"
        )
        assert (
            saved_plan.training.routines[0].external_bindings[0].external_routine_id
            == "hevy_routine_42"
        )
        assert saved_plan.training.weekly_schedule[1].focus == "recovery"
    finally:
        app.dependency_overrides.clear()


def test_record_plan_review_appends_review_history_and_latest_review():
    mock_db = MagicMock()
    mock_db.get_plan.return_value = make_plan()
    mock_db.save_plan.return_value = "plan_3"
    override_db(mock_db)

    payload = {
        "summary": "Boa aderencia e progresso consistente",
        "decision": "manter estrategia atual",
        "changes_made": ["subir carboidratos em dias de treino"],
        "next_review_at": "2026-05-15",
        "evidence_summary": ["2 treinos completos", "peso subindo 0.2kg/semana"],
    }

    try:
        response = client.post("/plan/review", json=payload)
        assert response.status_code == 200
        assert response.json()["id"] == "plan_3"
        saved_plan = mock_db.save_plan.call_args.args[0]
        assert saved_plan.latest_review is not None
        assert saved_plan.latest_review.summary == "Boa aderencia e progresso consistente"
        assert saved_plan.latest_review.decision == "manter estrategia atual"
        assert saved_plan.latest_review.changes_made == ["subir carboidratos em dias de treino"]
        assert saved_plan.latest_review.evidence_summary == [
            "2 treinos completos",
            "peso subindo 0.2kg/semana",
        ]
        assert len(saved_plan.review_history) == 1
        assert saved_plan.review_history[0].summary == "Boa aderencia e progresso consistente"
    finally:
        app.dependency_overrides.clear()


def test_get_plan_progress_returns_computed_snapshot():
    mock_db = MagicMock()
    plan = make_plan()
    plan.id = "plan-progress-1"
    mock_db.get_plan.return_value = plan
    mock_db.get_workout_logs.return_value = [{"id": "w1"}, {"id": "w2"}]
    mock_db.get_weight_logs.return_value = [{"id": "b1"}, {"id": "b2"}]
    mock_nutrition_stats = MagicMock()
    mock_nutrition_stats.total_logs = 5
    mock_db.get_nutrition_stats.return_value = mock_nutrition_stats
    override_db(mock_db)

    try:
        response = client.get("/plan/progress")
        assert response.status_code == 200
        body = response.json()
        assert body["plan_id"] == "plan-progress-1"
        assert body["training_adherence"]["status"] == "on_track"
        assert body["nutrition_adherence"]["status"] == "on_track"
        assert body["progression_status"] == "maintaining"
        assert body["body_trend_status"] == "aligned"
        assert body["recommended_review"] is False
        assert "2 treino(s) registrado(s) recentemente." in body["evidence_summary"]
        assert "5 log(s) nutricionais registrados." in body["evidence_summary"]
    finally:
        app.dependency_overrides.clear()


def test_patch_plan_section_rejects_missing_active_plan():
    mock_db = MagicMock()
    mock_db.get_plan.return_value = None
    override_db(mock_db)

    try:
        response = client.patch("/plan/section", json={"section": "tracking", "tracking": {
            "workout_adherence_target_pct": 85,
            "nutrition_adherence_target_pct": 80,
            "progress_markers": [{"name": "peso", "source": "body", "target_summary": "subir"}],
            "review_questions": ["Tudo coerente?"],
        }})
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_get_plan_view_returns_discovery_state_without_active_plan():
    mock_db = MagicMock()
    mock_db.get_plan.return_value = None
    mock_db.get_plan_discovery.return_value = PlanDiscoveryState(
        user_email="test@example.com",
        goal_primary="muscle_gain",
        missing_fields=["target_date"],
    )
    override_db(mock_db)

    try:
        response = client.get("/plan/view")
        assert response.status_code == 200
        assert response.json()["status"] == "DISCOVERY_IN_PROGRESS"
    finally:
        app.dependency_overrides.clear()


def test_plan_endpoints_stateful_roundtrip_discovery_create_update_review_progress_and_view():
    db = StatefulPlanDb()
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: db

    discovery_payload = {
        "goal_primary": "muscle_gain",
        "goal_summary": "Ganhar massa com menos gordura",
        "target_date": "2026-08-01",
        "training_days_available": ["monday", "thursday", "saturday"],
        "session_duration_min": 70,
        "constraints": ["joelho sensivel"],
        "preferences": ["treino curto e intenso"],
        "available_equipment": ["barra", "halteres", "cabo"],
        "training_level": "intermediate",
        "nutrition_preferences": ["alto teor proteico"],
        "metabolism_confirmed": True,
    }

    try:
        discovery_response = client.post("/plan/discovery", json=discovery_payload)
        assert discovery_response.status_code == 200
        assert discovery_response.json()["id"]

        discovery_get = client.get("/plan/discovery")
        assert discovery_get.status_code == 200
        assert discovery_get.json()["goal_summary"] == "Ganhar massa com menos gordura"
        assert discovery_get.json()["missing_fields"] == []

        status_before_create = client.get("/plan/status")
        assert status_before_create.status_code == 200
        assert status_before_create.json() == {
            "status": "DISCOVERY_IN_PROGRESS",
            "missing_fields": [],
        }

        create_response = client.post(
            "/plan/create-from-discovery",
            json=make_create_input().model_dump(mode="json"),
        )
        assert create_response.status_code == 200
        plan_id = create_response.json()["id"]
        assert plan_id

        plan_response = client.get("/plan")
        assert plan_response.status_code == 200
        assert plan_response.json()["title"] == "Plano Mestre"
        assert plan_response.json()["nutrition"]["daily_targets"]["calories_kcal"] == 2600
        assert (
            plan_response.json()["training"]["routines"][0]["exercises"][0]["name"]
            == "Supino Reto"
        )

        status_after_create = client.get("/plan/status")
        assert status_after_create.status_code == 200
        assert status_after_create.json() == {
            "status": "ACTIVE_PLAN",
            "missing_fields": [],
        }

        discovery_after_create = client.get("/plan/discovery")
        assert discovery_after_create.status_code == 200
        assert discovery_after_create.json() is None

        nutrition_update = client.patch(
            "/plan/section",
            json={
                "section": "nutrition",
                "review_reason": "ajuste por adesao",
                "nutrition": {
                    "daily_targets": {
                        "calories_kcal": 2800,
                        "protein_g": 170,
                        "carbs_g": 330,
                        "fat_g": 80,
                    },
                    "strategy": "superavit moderado",
                    "adherence_target_pct": 88,
                },
            },
        )
        assert nutrition_update.status_code == 200
        assert nutrition_update.json()["id"] == plan_id

        review_response = client.post(
            "/plan/review",
            json={
                "summary": "Boa aderencia e progresso consistente",
                "decision": "manter estrategia atual",
                "changes_made": ["subir carboidratos em dias de treino"],
                "next_review_at": "2026-05-15",
                "evidence_summary": [
                    "2 treinos completos",
                    "peso subindo 0.2kg/semana",
                ],
            },
        )
        assert review_response.status_code == 200
        assert review_response.json()["id"] == plan_id

        persisted_plan = db.get_plan("test@example.com")
        assert persisted_plan is not None
        assert persisted_plan.review_reason == "ajuste por adesao"
        assert persisted_plan.nutrition.daily_targets.calories_kcal == 2800
        assert persisted_plan.nutrition.daily_targets.protein_g == 170
        assert persisted_plan.latest_review is not None
        assert persisted_plan.latest_review.summary == "Boa aderencia e progresso consistente"
        assert len(persisted_plan.review_history) == 1

        db.workouts_repo.save_log(
            WorkoutLog(
                user_email="test@example.com",
                date=datetime.fromisoformat("2026-05-02T10:00:00"),
                workout_type="Upper",
                duration_minutes=65,
                source="manual",
                exercises=[
                    ExerciseLog(
                        name="Supino Reto",
                        sets=4,
                        reps_per_set=[8, 8, 7, 6],
                        weights_per_set=[70.0, 70.0, 72.5, 72.5],
                    )
                ],
            )
        )
        db.nutrition.save_log(
            NutritionLog(
                user_email="test@example.com",
                date=datetime.fromisoformat("2026-05-02T12:00:00"),
                source="manual",
                calories=2800,
                protein_grams=170.0,
                carbs_grams=330.0,
                fat_grams=80.0,
            )
        )
        db.weight.save_log(
            WeightLog(
                user_email="test@example.com",
                date=date(2026, 5, 1),
                weight_kg=72.0,
                trend_weight=71.8,
            )
        )
        db.weight.save_log(
            WeightLog(
                user_email="test@example.com",
                date=date(2026, 5, 8),
                weight_kg=72.3,
                trend_weight=71.9,
            )
        )

        progress_response = client.get("/plan/progress")
        assert progress_response.status_code == 200
        progress_payload = progress_response.json()
        assert progress_payload["plan_id"] == "active-plan"
        assert progress_payload["training_adherence"]["status"] == "on_track"
        assert progress_payload["nutrition_adherence"]["status"] == "on_track"
        assert progress_payload["progression_status"] == "maintaining"
        assert progress_payload["body_trend_status"] == "aligned"
        assert progress_payload["recommended_review"] is False

        view_response = client.get("/plan/view")
        assert view_response.status_code == 200
        view_payload = view_response.json()
        assert view_payload["status"] == "ACTIVE_PLAN"
        assert view_payload["active_plan"]["title"] == "Plano Mestre"
        assert view_payload["active_plan"]["nutrition_targets"]["calories_kcal"] == 2800
        assert view_payload["active_plan"]["latest_review_summary"] == "Boa aderencia e progresso consistente"
        assert view_payload["progress"]["body_trend_status"] == "aligned"
    finally:
        app.dependency_overrides.clear()


def test_plan_discovery_stateful_cold_start_rehydrates_partial_draft_and_allows_resume():
    shared_database = FakeDatabase()
    initial_db = StatefulPlanDb(shared_database)
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: initial_db

    first_payload = {
        "goal_primary": "muscle_gain",
        "goal_summary": "Ganhar massa sem perder consistencia",
        "training_days_available": ["monday", "thursday"],
    }

    second_payload = {
        "session_duration_min": 55,
        "constraints": ["joelho sensivel"],
        "preferences": ["treino objetivo"],
        "available_equipment": ["barra", "halteres"],
        "metabolism_confirmed": True,
    }

    try:
        first_response = client.post("/plan/discovery", json=first_payload)
        assert first_response.status_code == 200
        first_discovery_id = first_response.json()["id"]
        assert first_discovery_id

        first_status = client.get("/plan/status")
        assert first_status.status_code == 200
        assert first_status.json()["status"] == "DISCOVERY_IN_PROGRESS"
        assert set(first_status.json()["missing_fields"]) == {
            "target_date",
            "session_duration_min",
            "constraints",
            "preferences",
            "available_equipment",
            "metabolism_confirmed",
        }

        rehydrated_db = StatefulPlanDb(shared_database)
        app.dependency_overrides[get_mongo_database] = lambda: rehydrated_db

        resumed_discovery = client.get("/plan/discovery")
        assert resumed_discovery.status_code == 200
        resumed_payload = resumed_discovery.json()
        assert resumed_payload["goal_primary"] == "muscle_gain"
        assert resumed_payload["goal_summary"] == "Ganhar massa sem perder consistencia"
        assert resumed_payload["training_days_available"] == ["monday", "thursday"]
        assert resumed_payload["session_duration_min"] is None
        assert set(resumed_payload["missing_fields"]) == {
            "target_date",
            "session_duration_min",
            "constraints",
            "preferences",
            "available_equipment",
            "metabolism_confirmed",
        }

        second_response = client.post("/plan/discovery", json=second_payload)
        assert second_response.status_code == 200
        assert second_response.json()["id"] == first_discovery_id

        resumed_after_second = client.get("/plan/discovery")
        assert resumed_after_second.status_code == 200
        resumed_after_second_payload = resumed_after_second.json()
        assert resumed_after_second_payload["goal_primary"] == "muscle_gain"
        assert resumed_after_second_payload["goal_summary"] == "Ganhar massa sem perder consistencia"
        assert resumed_after_second_payload["training_days_available"] == ["monday", "thursday"]
        assert resumed_after_second_payload["session_duration_min"] == 55
        assert resumed_after_second_payload["constraints"] == ["joelho sensivel"]
        assert resumed_after_second_payload["preferences"] == ["treino objetivo"]
        assert resumed_after_second_payload["available_equipment"] == ["barra", "halteres"]
        assert resumed_after_second_payload["metabolism_confirmed"] is True
        assert resumed_after_second_payload["missing_fields"] == ["target_date"]
    finally:
        app.dependency_overrides.clear()


def test_plan_discovery_stateful_allows_clearing_previously_filled_lists_and_metabolism_flag():
    db = StatefulPlanDb()
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: db

    initial_payload = {
        "goal_primary": "muscle_gain",
        "goal_summary": "Ganhar massa com consistencia",
        "target_date": "2026-08-01",
        "training_days_available": ["monday", "thursday"],
        "session_duration_min": 60,
        "constraints": ["joelho sensivel"],
        "preferences": ["treino curto"],
        "available_equipment": ["barra", "halteres"],
        "metabolism_confirmed": True,
    }
    clearing_payload = {
        "training_days_available": [],
        "constraints": [],
        "preferences": [],
        "available_equipment": [],
        "metabolism_confirmed": False,
    }

    try:
        first_response = client.post("/plan/discovery", json=initial_payload)
        assert first_response.status_code == 200
        discovery_id = first_response.json()["id"]
        assert discovery_id

        clear_response = client.post("/plan/discovery", json=clearing_payload)
        assert clear_response.status_code == 200
        assert clear_response.json()["id"] == discovery_id

        current_discovery = client.get("/plan/discovery")
        assert current_discovery.status_code == 200
        payload = current_discovery.json()
        assert payload["goal_primary"] == "muscle_gain"
        assert payload["goal_summary"] == "Ganhar massa com consistencia"
        assert payload["target_date"] == "2026-08-01"
        assert payload["session_duration_min"] == 60
        assert payload["training_days_available"] == []
        assert payload["constraints"] == []
        assert payload["preferences"] == []
        assert payload["available_equipment"] == []
        assert payload["metabolism_confirmed"] is False
        assert set(payload["missing_fields"]) == {
            "training_days_available",
            "constraints",
            "preferences",
            "available_equipment",
            "metabolism_confirmed",
        }

        status_response = client.get("/plan/status")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "DISCOVERY_IN_PROGRESS"
        assert set(status_response.json()["missing_fields"]) == {
            "training_days_available",
            "constraints",
            "preferences",
            "available_equipment",
            "metabolism_confirmed",
        }
    finally:
        app.dependency_overrides.clear()


def test_plan_training_section_stateful_preserves_review_reason_and_advanced_fields():
    db = StatefulPlanDb()
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    app.dependency_overrides[get_mongo_database] = lambda: db

    try:
        db.save_plan(
            make_plan().model_copy(
                update={"review_reason": "Plano criado apos discovery inicial"}
            )
        )

        payload = {
            "section": "training",
            "training": {
                "split_name": "push_pull_legs",
                "frequency_per_week": 1,
                "session_duration_min": 75,
                "routines": [
                    {
                        "id": "push_a",
                        "name": "Push A",
                        "objective": "Foco em peito e ombros",
                        "exercises": [
                            {
                                "name": "Supino Inclinado",
                                "external_exercise_template_id": "hevy_ex_101",
                                "sets": 4,
                                "rep_range": {"min_reps": 6, "max_reps": 10},
                                "intensity": {
                                    "prescription_type": "rir",
                                    "target": "2",
                                },
                                "rest_seconds": 120,
                                "progression_rule": {
                                    "method": "double_progression",
                                    "increase_when": "bater 10 reps em todas as series",
                                    "hold_when": "ficar abaixo de 8 reps em alguma serie",
                                    "deload_when": "estagnar por 3 semanas",
                                },
                                "notes": "Priorizar cadencia controlada",
                            }
                        ],
                        "external_bindings": [
                            {
                                "provider": "hevy",
                                "external_routine_id": "hevy_routine_42",
                                "external_routine_name": "Push Day",
                                "last_synced_at": "2026-05-01T10:00:00Z",
                                "last_sync_error": "sync timeout anterior",
                            }
                        ],
                    }
                ],
                "weekly_schedule": [
                    {
                        "day": "monday",
                        "routine_id": "push_a",
                        "focus": "push",
                        "type": "training",
                    },
                    {
                        "day": "thursday",
                        "routine_id": None,
                        "focus": "recovery",
                        "type": "off",
                    },
                ],
            },
        }

        with patch(
            "src.api.endpoints.plan.sync_training_with_hevy_if_needed",
            side_effect=lambda **kwargs: kwargs["updated_plan"],
        ):
            response = client.patch("/plan/section", json=payload)

        assert response.status_code == 200
        persisted = db.get_plan("test@example.com")
        assert persisted is not None
        assert persisted.review_reason == "Plano criado apos discovery inicial"
        assert persisted.training.split_name == "push_pull_legs"
        assert persisted.training.session_duration_min == 75
        assert persisted.training.routines[0].objective == "Foco em peito e ombros"
        assert (
            persisted.training.routines[0].exercises[0].external_exercise_template_id
            == "hevy_ex_101"
        )
        assert persisted.training.routines[0].exercises[0].rest_seconds == 120
        assert persisted.training.routines[0].external_bindings[0].external_routine_id == "hevy_routine_42"
        assert persisted.training.weekly_schedule[1].type == "off"
    finally:
        app.dependency_overrides.clear()
