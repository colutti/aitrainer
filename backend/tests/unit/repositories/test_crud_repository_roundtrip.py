from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timezone

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from src.api.models.plan import (
    ConflictRule,
    IntensityPrescription,
    NutritionDailyTargets,
    PlanAlignment,
    PlanDiscoveryState,
    PlanGoal,
    PlanNutrition,
    PlanTimeline,
    PlanTracking,
    PlanTraining,
    ProgressMarker,
    ProgressionRule,
    RepRange,
    SuccessMetric,
    TrainingExercise,
    TrainingRoutine,
    UserPlan,
    WeeklyScheduleItem,
)
from src.api.models.nutrition_log import NutritionLog
from src.api.models.scheduled_event import ScheduledEvent
from src.api.models.trainer_profile import TrainerProfile
from src.api.models.invite import Invite
from src.api.models.user_profile import UserProfile
from src.api.models.weight_log import WeightLog
from src.api.models.workout_log import ExerciseLog, WorkoutLog
from src.repositories.event_repository import EventRepository
from src.repositories.invite_repository import InviteRepository
from src.repositories.nutrition_repository import NutritionRepository
from src.repositories.plan_repository import PlanRepository
from src.repositories.telegram_repository import TelegramRepository
from src.repositories.trainer_repository import TrainerRepository
from src.repositories.user_repository import UserRepository
from src.repositories.weight_repository import WeightRepository
from src.repositories.workout_repository import WorkoutRepository


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

    def sort(self, field: str, direction: int) -> FakeCursor:
        reverse = direction < 0
        self._docs.sort(
            key=lambda doc: (
                doc.get(field) is not None,
                doc.get(field) if doc.get(field) is not None else "",
            ),
            reverse=reverse,
        )
        return self

    def skip(self, amount: int) -> FakeCursor:
        self._docs = self._docs[amount:]
        return self

    def limit(self, amount: int) -> FakeCursor:
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
            if key == "$or":
                return any(self._matches(doc, branch) for branch in value)
            if isinstance(value, dict):
                current = doc.get(key)
                if "$ne" in value and current == value["$ne"]:
                    return False
                if "$gte" in value and current < value["$gte"]:
                    return False
                if "$gt" in value and current <= value["$gt"]:
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
                    upserted_id=None,
                    modified_count=0 if doc == original else 1,
                )

        if upsert:
            inserted_id = ObjectId()
            new_doc = {"_id": inserted_id, **deepcopy(query), **deepcopy(update.get("$set", {}))}
            self.docs.append(new_doc)
            return FakeUpdateResult(upserted_id=inserted_id, modified_count=0)

        return FakeUpdateResult(upserted_id=None)

    def find_one(self, query: dict, projection: dict | None = None, sort: list[tuple[str, int]] | None = None) -> dict | None:
        docs = [doc for doc in self.docs if self._matches(doc, query)]
        if sort:
            field, direction = sort[0]
            docs.sort(key=lambda doc: doc.get(field), reverse=direction < 0)
        if docs:
            doc = deepcopy(docs[0])
            if projection:
                keep = {key for key, value in projection.items() if value}
                if keep:
                    doc = {key: value for key, value in doc.items() if key in keep or key == "_id"}
            return doc
        return None

    def find(self, query: dict) -> FakeCursor:
        return FakeCursor([deepcopy(doc) for doc in self.docs if self._matches(doc, query)])

    def replace_one(self, query: dict, data: dict) -> FakeReplaceResult:
        for index, doc in enumerate(self.docs):
            if self._matches(doc, query):
                self.docs[index] = {"_id": doc["_id"], **deepcopy(data)}
                return FakeReplaceResult(matched_count=1)
        return FakeReplaceResult(matched_count=0)

    def delete_one(self, query: dict) -> FakeDeleteResult:
        for index, doc in enumerate(self.docs):
            if self._matches(doc, query):
                del self.docs[index]
                return FakeDeleteResult(deleted_count=1)
        return FakeDeleteResult(deleted_count=0)

    def insert_one(self, data: dict) -> FakeInsertResult:
        if "update_id" in data and any(
            doc.get("update_id") == data["update_id"] for doc in self.docs
        ):
            raise DuplicateKeyError("duplicate update_id")
        inserted_id = ObjectId()
        self.docs.append({"_id": inserted_id, **deepcopy(data)})
        return FakeInsertResult(inserted_id)

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

    def delete_many(self, query: dict) -> None:
        self.docs = [doc for doc in self.docs if not self._matches(doc, query)]

    def find_one_and_delete(self, query: dict) -> dict | None:
        for index, doc in enumerate(self.docs):
            if self._matches(doc, query):
                found = deepcopy(doc)
                del self.docs[index]
                return found
        return None


class FakeDatabase:
    def __init__(self) -> None:
        self._collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self._collections:
            self._collections[name] = FakeCollection()
        return self._collections[name]


def build_user_plan(user_email: str) -> UserPlan:
    return UserPlan(
        user_email=user_email,
        title="Plano de recomposição",
        goal=PlanGoal(
            primary_goal="recomposition",
            outcome_summary="Ganhar massa e reduzir gordura",
            success_metrics=[
                SuccessMetric(
                    metric_name="peso",
                    target_value=78,
                    unit="kg",
                    direction="maintain",
                )
            ],
        ),
        timeline=PlanTimeline(
            start_date=date(2026, 4, 1),
            target_date=date(2026, 7, 1),
            review_cadence_days=14,
            current_phase="base",
        ),
        user_context={
            "training_days_available": ["monday", "wednesday", "friday"],
            "session_duration_min": 60,
            "constraints": ["ombro sensivel"],
            "preferences": ["treino com barra"],
            "available_equipment": ["barra", "halteres"],
            "training_level": "intermediate",
            "nutrition_preferences": ["alto teor proteico"],
        },
        training=PlanTraining(
            split_name="Upper/Lower",
            frequency_per_week=2,
            session_duration_min=60,
            routines=[
                TrainingRoutine(
                    id="upper-a",
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
                            rest_seconds=120,
                            progression_rule=ProgressionRule(
                                method="double_progression",
                                increase_when="atingir topo da faixa",
                                hold_when="faixa incompleta",
                                deload_when="fadiga acumulada",
                            ),
                            notes="manter tecnica",
                        )
                    ],
                )
            ],
            weekly_schedule=[
                WeeklyScheduleItem(day="monday", routine_id="upper-a", focus="upper"),
                WeeklyScheduleItem(day="wednesday", routine_id=None, focus="descanso", type="off"),
                WeeklyScheduleItem(day="friday", routine_id="upper-a", focus="upper"),
            ],
        ),
        nutrition=PlanNutrition(
            daily_targets=NutritionDailyTargets(
                calories_kcal=2400,
                protein_g=180,
                carbs_g=250,
                fat_g=70,
                fiber_g=30,
            ),
            strategy="manter proteina alta",
            adherence_target_pct=85,
        ),
        alignment=PlanAlignment(
            training_nutrition_rationale="volume moderado com suporte calórico",
            energy_strategy="recomposition",
            recovery_assumptions=["sono de 8h"],
            conflict_rules=[
                ConflictRule(trigger="dor persistente", action="reduzir volume")
            ],
        ),
        tracking=PlanTracking(
            workout_adherence_target_pct=85,
            nutrition_adherence_target_pct=80,
            progress_markers=[
                ProgressMarker(
                    name="treinos completos",
                    source="workouts",
                    target_summary="3x por semana",
                )
            ],
            review_questions=["Como ficou a recuperação?"],
        ),
        created_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
        last_material_change_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
    )


def test_weight_repository_roundtrip_persists_all_fields_and_supports_update_list_delete():
    repo = WeightRepository(FakeDatabase())
    create_log = WeightLog(
        user_email="repo@test.com",
        date=date(2026, 3, 17),
        weight_kg=80.2,
        body_fat_pct=18.4,
        muscle_mass_pct=40.8,
        muscle_mass_kg=32.8,
        bone_mass_kg=3.5,
        body_water_pct=57.9,
        visceral_fat=8,
        bmr=1788,
        bmi=25.1,
        neck_cm=39.0,
        chest_cm=104.0,
        waist_cm=84.0,
        hips_cm=98.5,
        bicep_r_cm=36.5,
        bicep_l_cm=36.0,
        thigh_r_cm=58.0,
        thigh_l_cm=57.5,
        calf_r_cm=38.0,
        calf_l_cm=37.5,
        source="manual",
        notes="initial weight note",
        trend_weight=79.47,
    )

    log_id, is_new = repo.save_log(create_log)
    assert is_new is True

    update_log = WeightLog(
        user_email="repo@test.com",
        date=date(2026, 3, 18),
        weight_kg=79.8,
        body_fat_pct=17.1,
        muscle_mass_pct=41.4,
        muscle_mass_kg=33.1,
        bone_mass_kg=3.4,
        body_water_pct=58.2,
        visceral_fat=7,
        bmr=1760,
        bmi=24.9,
        neck_cm=39.5,
        chest_cm=104.5,
        waist_cm=83.0,
        hips_cm=98.0,
        bicep_r_cm=36.0,
        bicep_l_cm=35.5,
        thigh_r_cm=57.0,
        thigh_l_cm=56.5,
        calf_r_cm=37.5,
        calf_l_cm=37.0,
        source="manual",
        notes="updated weight note",
        trend_weight=79.12,
    )

    assert repo.update_log(log_id, "repo@test.com", update_log) is True

    paginated_logs, total = repo.get_paginated("repo@test.com", page=1, page_size=10)
    assert total == 1
    assert paginated_logs[0]["id"] == log_id
    assert paginated_logs[0]["body_fat_pct"] == 17.1
    assert paginated_logs[0]["muscle_mass_kg"] == 33.1
    assert paginated_logs[0]["waist_cm"] == 83.0
    assert paginated_logs[0]["notes"] == "updated weight note"
    assert paginated_logs[0]["trend_weight"] == 79.12

    logs = repo.get_logs("repo@test.com")
    assert len(logs) == 1
    assert logs[0].date == date(2026, 3, 18)
    assert logs[0].calf_l_cm == 37.0

    assert repo.delete_log("repo@test.com", date(2026, 3, 18)) is True
    remaining_logs, remaining_total = repo.get_paginated("repo@test.com", page=1, page_size=10)
    assert remaining_logs == []
    assert remaining_total == 0


def test_nutrition_repository_roundtrip_persists_all_fields_and_daily_upsert_rules():
    repo = NutritionRepository(FakeDatabase())
    repo.ensure_indexes()

    create_log = NutritionLog(
        user_email="repo@test.com",
        date=datetime.fromisoformat("2026-03-17T10:00:00"),
        source="manual",
        calories=2500,
        protein_grams=150.0,
        carbs_grams=300.0,
        fat_grams=70.0,
        fiber_grams=30.0,
        sugar_grams=40.0,
        sodium_mg=1800.0,
        cholesterol_mg=220.0,
        notes="initial nutrition note",
        partial_logged=True,
    )
    log_id, is_new = repo.save_log(create_log)
    assert is_new is True

    update_log = NutritionLog(
        user_email="repo@test.com",
        date=datetime.fromisoformat("2026-03-18T12:30:00"),
        source="myfitnesspal",
        calories=2350,
        protein_grams=165.0,
        carbs_grams=245.0,
        fat_grams=62.0,
        fiber_grams=34.0,
        sugar_grams=28.0,
        sodium_mg=1500.0,
        cholesterol_mg=180.0,
        notes="updated nutrition note",
        partial_logged=False,
    )
    assert repo.update_log(log_id, "repo@test.com", update_log) is True

    paginated_logs, total = repo.get_paginated("repo@test.com", page=1, page_size=10)
    assert total == 1
    assert paginated_logs[0]["id"] == log_id
    assert paginated_logs[0]["fiber_grams"] == 34.0
    assert paginated_logs[0]["sugar_grams"] == 28.0
    assert paginated_logs[0]["sodium_mg"] == 1500.0
    assert paginated_logs[0]["cholesterol_mg"] == 180.0
    assert paginated_logs[0]["notes"] == "updated nutrition note"
    assert paginated_logs[0]["partial_logged"] is False

    same_day_upsert = NutritionLog(
        user_email="repo@test.com",
        date=datetime.fromisoformat("2026-03-18T18:45:00"),
        source="manual",
        calories=2400,
        protein_grams=170.0,
        carbs_grams=250.0,
        fat_grams=64.0,
        fiber_grams=35.0,
        sugar_grams=29.0,
        sodium_mg=1510.0,
        cholesterol_mg=181.0,
        notes="same day overwrite",
        partial_logged=True,
    )
    upserted_id, was_new = repo.save_log(same_day_upsert)
    assert upserted_id == log_id
    assert was_new is False

    persisted = repo.get_log_by_id(log_id)
    assert persisted is not None
    assert persisted["calories"] == 2400
    assert persisted["date"] == datetime.fromisoformat("2026-03-18T00:00:00")
    assert persisted["partial_logged"] is True

    assert repo.delete_log(log_id) is True
    remaining_logs, remaining_total = repo.get_paginated("repo@test.com", page=1, page_size=10)
    assert remaining_logs == []
    assert remaining_total == 0


def test_workout_repository_roundtrip_persists_all_supported_fields_and_pagination():
    repo = WorkoutRepository(FakeDatabase())
    create_log = WorkoutLog(
        user_email="repo@test.com",
        date=datetime.fromisoformat("2026-03-17T10:00:00"),
        workout_type="Hybrid Strength",
        duration_minutes=67,
        source="manual",
        external_id="hevy-workout-123",
        exercises=[
            ExerciseLog(
                name="Bench Press",
                sets=2,
                reps_per_set=[10, 8],
                weights_per_set=[60.0, 70.0],
            ),
            ExerciseLog(
                name="Row Erg",
                sets=2,
                reps_per_set=[1, 1],
                weights_per_set=[0.0, 0.0],
                distance_meters_per_set=[500.0, 500.0],
                duration_seconds_per_set=[110, 115],
            ),
        ],
    )
    workout_id = repo.save_log(create_log)

    updated_log = WorkoutLog(
        user_email="repo@test.com",
        date=datetime.fromisoformat("2026-03-18T11:30:00"),
        workout_type="Conditioning",
        duration_minutes=54,
        source="hevy",
        external_id="hevy-workout-456",
        exercises=[
            ExerciseLog(
                name="Deadlift",
                sets=3,
                reps_per_set=[5, 5, 5],
                weights_per_set=[100.0, 105.0, 110.0],
            ),
            ExerciseLog(
                name="Assault Bike",
                sets=1,
                reps_per_set=[1],
                weights_per_set=[0.0],
                distance_meters_per_set=[1200.0],
                duration_seconds_per_set=[180],
            ),
        ],
    )
    assert repo.update_log(workout_id, "repo@test.com", updated_log) is True

    persisted = repo.get_log_by_id(workout_id)
    assert persisted is not None
    assert persisted["workout_type"] == "Conditioning"
    assert persisted["external_id"] == "hevy-workout-456"
    assert persisted["exercises"][1]["distance_meters_per_set"] == [1200.0]
    assert persisted["exercises"][1]["duration_seconds_per_set"] == [180]

    paginated_workouts, total = repo.get_paginated("repo@test.com", page=1, page_size=10)
    assert total == 1
    assert str(paginated_workouts[0]["_id"]) == workout_id
    assert paginated_workouts[0]["duration_minutes"] == 54

    logs = repo.get_logs("repo@test.com")
    assert len(logs) == 1
    assert logs[0].external_id == "hevy-workout-456"
    assert logs[0].exercises[0].weights_per_set == [100.0, 105.0, 110.0]

    assert repo.delete_log(workout_id) is True
    remaining_logs, remaining_total = repo.get_paginated("repo@test.com", page=1, page_size=10)
    assert remaining_logs == []
    assert remaining_total == 0


def test_event_repository_roundtrip_filters_active_events_and_enforces_user_scoped_update_delete():
    repo = EventRepository(FakeDatabase())

    no_deadline_id = repo.save_event(
        ScheduledEvent(
            user_email="repo@test.com",
            title="Check-in semanal",
            description="Sem prazo fixo",
            date=None,
            recurrence="weekly",
            active=True,
            created_at="2026-03-10T09:00:00",
        )
    )
    future_id = repo.save_event(
        ScheduledEvent(
            user_email="repo@test.com",
            title="Meta de verao",
            description="Secar 3kg",
            date="2099-07-01",
            recurrence="none",
            active=True,
            created_at="2026-03-11T09:00:00",
        )
    )
    past_event_id = repo.save_event(
        ScheduledEvent(
            user_email="repo@test.com",
            title="Evento passado",
            description="Nao deve aparecer como ativo",
            date="2020-01-01",
            recurrence="none",
            active=True,
            created_at="2026-03-12T09:00:00",
        )
    )
    inactive_id = repo.save_event(
        ScheduledEvent(
            user_email="repo@test.com",
            title="Evento inativo",
            description="Apenas para listagem total",
            date="2099-08-01",
            recurrence="monthly",
            active=False,
            created_at="2026-03-13T09:00:00",
        )
    )
    other_user_id = repo.save_event(
        ScheduledEvent(
            user_email="other@test.com",
            title="Evento de outro usuario",
            description="Nao deve aparecer nas listagens",
            date="2099-09-01",
            recurrence="none",
            active=True,
            created_at="2026-03-14T09:00:00",
        )
    )

    active_events = repo.get_active_events("repo@test.com")
    assert [event.title for event in active_events] == ["Check-in semanal", "Meta de verao"]
    assert active_events[0].date is None
    assert active_events[1].date == "2099-07-01"

    assert (
        repo.update_event(
            future_id,
            "repo@test.com",
            {
                "title": "Meta de praia",
                "description": "Secar 4kg",
                "date": None,
                "recurrence": "monthly",
                "active": False,
            },
        )
        is True
    )
    assert repo.update_event(future_id, "other@test.com", {"title": "Nao autorizado"}) is False

    listed_events = repo.list_all_events("repo@test.com")
    assert [event.title for event in listed_events] == [
        "Check-in semanal",
        "Meta de praia",
        "Evento passado",
        "Evento inativo",
    ]
    updated_future = next(event for event in listed_events if event.id == future_id)
    assert updated_future.date is None
    assert updated_future.recurrence == "monthly"
    assert updated_future.active is False
    assert any(event.id == inactive_id for event in listed_events)
    assert all(event.id != other_user_id for event in listed_events)

    assert repo.delete_event(no_deadline_id, "other@test.com") is False
    assert repo.delete_event(no_deadline_id, "repo@test.com") is True
    remaining_events = repo.list_all_events("repo@test.com")
    assert [event.id for event in remaining_events] == [future_id, past_event_id, inactive_id]
    assert repo.get_active_events("repo@test.com") == []


def test_invite_repository_roundtrip_create_mark_used_revoke_and_filter_active():
    repo = InviteRepository(FakeDatabase())
    active_invite = Invite(
        token="invite-active",
        email="active@test.com",
        created_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
        expires_at=datetime(2099, 4, 4, tzinfo=timezone.utc),
        used=False,
    )
    expired_invite = Invite(
        token="invite-expired",
        email="expired@test.com",
        created_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
        expires_at=datetime(2026, 4, 2, tzinfo=timezone.utc),
        used=False,
    )
    second_active_invite = Invite(
        token="invite-second",
        email="active@test.com",
        created_at=datetime(2026, 4, 3, tzinfo=timezone.utc),
        expires_at=datetime(2099, 4, 6, tzinfo=timezone.utc),
        used=False,
    )

    repo.create(active_invite)
    repo.create(expired_invite)
    repo.create(second_active_invite)

    by_token = repo.get_by_token("invite-active")
    assert by_token is not None
    assert by_token.email == "active@test.com"

    by_email = repo.get_by_email("active@test.com")
    assert by_email is not None
    assert by_email.token == "invite-second"

    assert repo.has_active_invite("active@test.com") is True
    active_list = repo.list_active()
    assert [invite.token for invite in active_list] == ["invite-second", "invite-active"]

    assert repo.mark_as_used("invite-active") is True
    used_invite = repo.get_by_token("invite-active")
    assert used_invite is not None
    assert used_invite.used is True
    assert used_invite.used_at is not None

    assert repo.revoke("invite-second") is True
    assert repo.get_by_token("invite-second") is None
    assert repo.has_active_invite("active@test.com") is False


def test_telegram_repository_roundtrip_code_validation_relink_and_idempotency():
    repo = TelegramRepository(FakeDatabase())

    code = repo.create_linking_code("user@test.com")
    assert len(code) == 6
    first_code_doc = repo.codes_collection.find_one({"code": code})
    assert first_code_doc is not None
    assert first_code_doc["user_email"] == "user@test.com"

    replacement_code = repo.create_linking_code("user@test.com")
    assert repo.codes_collection.find_one({"code": code}) is None
    assert repo.codes_collection.find_one({"code": replacement_code}) is not None

    linked_email = repo.validate_and_consume_code(
        replacement_code.lower(),
        123456789,
        username="telegram-user",
    )
    assert linked_email == "user@test.com"
    link = repo.get_link_by_email("user@test.com")
    assert link is not None
    assert link.chat_id == 123456789
    assert link.telegram_username == "telegram-user"
    assert repo.get_link_by_chat_id(123456789) is not None
    assert repo.validate_and_consume_code(replacement_code, 999999999) is None

    repo.create_or_replace_link("user@test.com", 987654321, username="updated-user")
    replaced = repo.get_link_by_email("user@test.com")
    assert replaced is not None
    assert replaced.chat_id == 987654321
    assert replaced.telegram_username == "updated-user"
    assert repo.get_link_by_chat_id(123456789) is None

    assert repo.try_record_update(42) is True
    assert repo.try_record_update(42) is False

    assert repo.delete_link("user@test.com") is True
    assert repo.get_link_by_email("user@test.com") is None


def test_user_repository_roundtrip_persists_updates_unsets_nullable_fields_and_resets_daily_counts():
    repo = UserRepository(FakeDatabase())
    profile = UserProfile(
        email="repo@test.com",
        role="user",
        gender="Masculino",
        age=31,
        height=180,
        goal_type="maintain",
        weekly_rate=0.0,
        notes="nota inicial",
        display_name="User Repo",
        onboarding_completed=True,
        telegram_notify_on_workout=True,
        telegram_notify_on_nutrition=False,
        telegram_notify_on_weight=False,
        current_billing_cycle_start=datetime(2026, 4, 1, tzinfo=timezone.utc),
        photo_base64="data:image/png;base64,abc",
    )
    repo.save_profile(profile)

    updated_profile = profile.model_copy(
        update={
            "notes": None,
            "photo_base64": None,
            "display_name": "User Repo Updated",
        }
    )
    repo.save_profile(updated_profile)
    persisted = repo.get_profile("repo@test.com")
    assert persisted is not None
    assert persisted.display_name == "User Repo Updated"
    assert persisted.notes is None
    assert persisted.photo_base64 is None

    assert repo.update_profile_fields(
        "repo@test.com",
        {
            "telegram_notify_on_workout": False,
            "telegram_notify_on_nutrition": True,
            "telegram_notify_on_weight": True,
        },
    ) is True
    toggled = repo.get_profile("repo@test.com")
    assert toggled is not None
    assert toggled.telegram_notify_on_workout is False
    assert toggled.telegram_notify_on_nutrition is True
    assert toggled.telegram_notify_on_weight is True

    repo.increment_message_counts("repo@test.com")
    counted = repo.get_profile("repo@test.com")
    assert counted is not None
    assert counted.messages_sent_today == 1
    assert counted.messages_sent_this_month == 1
    assert counted.total_messages_sent == 1


def test_trainer_repository_roundtrip_persists_optional_fields_and_updates_existing_profile():
    repo = TrainerRepository(FakeDatabase())
    profile = TrainerProfile(
        user_email="repo@test.com",
        trainer_type="sofia",
        preferred_language="es-ES",
        personality_level="high",
    )
    repo.save_profile(profile)

    updated_profile = TrainerProfile(
        user_email="repo@test.com",
        trainer_type="gymbro",
        preferred_language="pt-BR",
        personality_level="balanced",
    )
    repo.save_profile(updated_profile)

    persisted = repo.get_profile("repo@test.com")
    assert persisted is not None
    assert persisted.trainer_type == "gymbro"
    assert persisted.preferred_language == "pt-BR"
    assert persisted.personality_level == "balanced"


def test_plan_repository_roundtrip_enforces_singleton_partial_updates_and_discovery_clear():
    repo = PlanRepository(FakeDatabase())
    initial_plan = build_user_plan("repo@test.com")
    plan_id = repo.save_plan(initial_plan)
    assert plan_id

    duplicated_plan = build_user_plan("repo@test.com").model_copy(
        update={"title": "Plano duplicado"}
    )
    second_id = repo.save_plan(duplicated_plan)
    assert second_id

    persisted = repo.get_plan("repo@test.com")
    assert persisted is not None
    assert persisted.title == "Plano duplicado"
    assert len(repo.collection.docs) == 1

    repo.partial_update_plan(
        "repo@test.com",
        {
            "review_reason": "ajuste por adesao",
            "tracking": {
                "workout_adherence_target_pct": 90,
                "nutrition_adherence_target_pct": 85,
                "progress_markers": [
                    {
                        "name": "aderencia",
                        "source": "manual",
                        "target_summary": "check semanal",
                    }
                ],
                "review_questions": ["Como foi a aderência?"],
            },
        },
    )
    updated = repo.get_plan("repo@test.com")
    assert updated is not None
    assert updated.review_reason == "ajuste por adesao"
    assert updated.tracking.workout_adherence_target_pct == 90

    discovery = PlanDiscoveryState(
        user_email="repo@test.com",
        goal_primary="recomposition",
        goal_summary="ganhar massa com controle de gordura",
        target_date=date(2026, 7, 1),
        training_days_available=["monday", "wednesday", "friday"],
        session_duration_min=60,
        constraints=["ombro sensivel"],
        preferences=["treino com barra"],
        available_equipment=["barra"],
        training_level="intermediate",
        nutrition_preferences=["proteina alta"],
        metabolism_confirmed=True,
        missing_fields=[],
        confidence={"goal_summary": "user_provided"},
    )
    discovery_id = repo.save_discovery(discovery)
    assert discovery_id
    persisted_discovery = repo.get_discovery("repo@test.com")
    assert persisted_discovery is not None
    assert persisted_discovery.goal_summary == "ganhar massa com controle de gordura"

    repo.clear_discovery("repo@test.com")
    assert repo.get_discovery("repo@test.com") is None
