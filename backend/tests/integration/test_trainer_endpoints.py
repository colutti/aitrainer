from __future__ import annotations

from copy import deepcopy

from bson import ObjectId
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.models.trainer_profile import TrainerProfile
from src.api.models.user_profile import UserProfile
from src.core.deps import get_ai_trainer_brain
from src.repositories.trainer_repository import TrainerRepository
from src.repositories.user_repository import UserRepository
from src.services.auth import verify_token
from src.core.subscription import SUBSCRIPTION_PLANS, SubscriptionPlan


client = TestClient(app)


class FakeUpdateResult:
    def __init__(self, *, upserted_id: ObjectId | None = None, modified_count: int = 0):
        self.upserted_id = upserted_id
        self.modified_count = modified_count


class FakeCollection:
    def __init__(self) -> None:
        self.docs: list[dict] = []

    def create_index(self, *_args, **_kwargs) -> None:
        return None

    def _matches(self, doc: dict, query: dict) -> bool:
        return all(doc.get(key) == value for key, value in query.items())

    def update_one(self, query: dict, update: dict, upsert: bool = False) -> FakeUpdateResult:
        for doc in self.docs:
            if self._matches(doc, query):
                original = deepcopy(doc)
                for key, value in update.get("$set", {}).items():
                    doc[key] = deepcopy(value)
                for key in update.get("$inc", {}).items():
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

    def find_one(self, query: dict, projection: dict | None = None, sort=None) -> dict | None:
        for doc in self.docs:
            if self._matches(doc, query):
                found = deepcopy(doc)
                if projection:
                    keep = {key for key, value in projection.items() if value}
                    if keep:
                        found = {
                            key: value
                            for key, value in found.items()
                            if key in keep or key == "_id"
                        }
                return found
        return None


class FakeDatabase:
    def __init__(self) -> None:
        self._collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self._collections:
            self._collections[name] = FakeCollection()
        return self._collections[name]


class StatefulTrainerBrain:
    def __init__(self) -> None:
        database = FakeDatabase()
        self.user_repo = UserRepository(database)
        self.trainer_repo = TrainerRepository(database)

    def get_user_profile(self, email: str) -> UserProfile | None:
        return self.user_repo.get_profile(email)

    def save_user_profile(self, profile: UserProfile) -> None:
        self.user_repo.save_profile(profile)

    def save_trainer_profile(self, profile: TrainerProfile) -> None:
        self.trainer_repo.save_profile(profile)

    def get_trainer_profile(self, email: str) -> TrainerProfile | None:
        return self.trainer_repo.get_profile(email)

    def get_or_create_trainer_profile(self, user_email: str) -> TrainerProfile:
        user_profile = self.get_user_profile(user_email)
        plan_name = user_profile.subscription_plan if user_profile else "Free"
        profile = self.get_trainer_profile(user_email)
        if not profile:
            default_trainer = "gymbro" if plan_name == "Free" else "atlas"
            profile = TrainerProfile(user_email=user_email, trainer_type=default_trainer)
            self.save_trainer_profile(profile)
            return profile

        self.ensure_trainer_allowed(user_email, plan_name, profile)
        return self.get_trainer_profile(user_email) or profile

    def ensure_trainer_allowed(
        self,
        user_email: str,
        plan_name: str,
        trainer_profile: TrainerProfile | None = None,
    ) -> str | None:
        trainer_profile = trainer_profile or self.get_trainer_profile(user_email)
        if not trainer_profile:
            return None
        try:
            plan = SubscriptionPlan(plan_name)
        except (ValueError, AttributeError):
            plan = SubscriptionPlan.FREE
        allowed = SUBSCRIPTION_PLANS[plan].allowed_trainers
        if allowed and trainer_profile.trainer_type not in allowed:
            trainer_profile.trainer_type = allowed[0]
            self.save_trainer_profile(trainer_profile)
            return allowed[0]
        return None


def _build_user(email: str, subscription_plan: str) -> UserProfile:
    return UserProfile(
        email=email,
        role="user",
        gender="Masculino",
        age=30,
        weight=None,
        height=180,
        goal_type="maintain",
        weekly_rate=0.0,
        subscription_plan=subscription_plan,
        onboarding_completed=True,
    )


def test_trainer_endpoints_roundtrip_persists_all_fields_and_supports_update():
    user_email = "trainer@example.com"
    brain = StatefulTrainerBrain()
    brain.save_user_profile(_build_user(user_email, "Pro"))

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_ai_trainer_brain] = lambda: brain

    try:
        create_response = client.put(
            "/trainer/update_trainer_profile",
            json={
                "trainer_type": "sofia",
                "preferred_language": "en-US",
                "personality_level": "energetic",
            },
        )
        assert create_response.status_code == 200
        assert create_response.json() == {
            "user_email": user_email,
            "trainer_type": "sofia",
            "preferred_language": "en-US",
            "personality_level": "energetic",
        }

        persisted = brain.get_trainer_profile(user_email)
        assert persisted is not None
        assert persisted.trainer_type == "sofia"
        assert persisted.preferred_language == "en-US"
        assert persisted.personality_level == "energetic"

        update_response = client.put(
            "/trainer/update_trainer_profile",
            json={
                "trainer_type": "atlas",
                "preferred_language": "es-ES",
                "personality_level": "balanced",
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["trainer_type"] == "atlas"
        assert update_response.json()["preferred_language"] == "es-ES"
        assert update_response.json()["personality_level"] == "balanced"

        get_response = client.get("/trainer/trainer_profile")
        assert get_response.status_code == 200
        assert get_response.json() == update_response.json()
    finally:
        app.dependency_overrides.clear()


def test_get_trainer_profile_creates_default_for_free_plan_and_persists_it():
    user_email = "free@example.com"
    brain = StatefulTrainerBrain()
    brain.save_user_profile(_build_user(user_email, "Free"))

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_ai_trainer_brain] = lambda: brain

    try:
        response = client.get("/trainer/trainer_profile")
        assert response.status_code == 200
        assert response.json() == {
            "user_email": user_email,
            "trainer_type": "gymbro",
            "preferred_language": "pt-BR",
            "personality_level": "balanced",
        }

        persisted = brain.get_trainer_profile(user_email)
        assert persisted is not None
        assert persisted.trainer_type == "gymbro"
        assert persisted.preferred_language == "pt-BR"
        assert persisted.personality_level == "balanced"
    finally:
        app.dependency_overrides.clear()


def test_get_trainer_profile_normalizes_disallowed_saved_trainer_for_free_plan():
    user_email = "normalized@example.com"
    brain = StatefulTrainerBrain()
    brain.save_user_profile(_build_user(user_email, "Free"))
    brain.save_trainer_profile(
        TrainerProfile(
            user_email=user_email,
            trainer_type="atlas",
            preferred_language="en-US",
            personality_level="energetic",
        )
    )

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_ai_trainer_brain] = lambda: brain

    try:
        response = client.get("/trainer/trainer_profile")
        assert response.status_code == 200
        assert response.json()["trainer_type"] == "gymbro"
        assert response.json()["preferred_language"] == "en-US"
        assert response.json()["personality_level"] == "energetic"

        persisted = brain.get_trainer_profile(user_email)
        assert persisted is not None
        assert persisted.trainer_type == "gymbro"
    finally:
        app.dependency_overrides.clear()


def test_update_trainer_profile_rejects_disallowed_trainer_for_free_plan():
    user_email = "blocked@example.com"
    brain = StatefulTrainerBrain()
    brain.save_user_profile(_build_user(user_email, "Free"))

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_ai_trainer_brain] = lambda: brain

    try:
        response = client.put(
            "/trainer/update_trainer_profile",
            json={
                "trainer_type": "atlas",
                "preferred_language": "en-US",
                "personality_level": "balanced",
            },
        )
        assert response.status_code == 403
        assert "is not available in the Free plan" in response.json()["detail"]
        assert brain.get_trainer_profile(user_email) is None
    finally:
        app.dependency_overrides.clear()


def test_update_trainer_profile_returns_404_when_user_profile_missing():
    app.dependency_overrides[verify_token] = lambda: "missing@example.com"
    app.dependency_overrides[get_ai_trainer_brain] = lambda: StatefulTrainerBrain()

    try:
        response = client.put(
            "/trainer/update_trainer_profile",
            json={"trainer_type": "atlas"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "User profile not found"
    finally:
        app.dependency_overrides.clear()


def test_update_trainer_profile_preserves_existing_preferences_when_optional_fields_are_omitted():
    user_email = "preserve-prefs@example.com"
    brain = StatefulTrainerBrain()
    brain.save_user_profile(_build_user(user_email, "Pro"))
    brain.save_trainer_profile(
        TrainerProfile(
            user_email=user_email,
            trainer_type="atlas",
            preferred_language="es-ES",
            personality_level="energetic",
        )
    )

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_ai_trainer_brain] = lambda: brain

    try:
        response = client.put(
            "/trainer/update_trainer_profile",
            json={"trainer_type": "sofia"},
        )

        assert response.status_code == 200
        assert response.json() == {
            "user_email": user_email,
            "trainer_type": "sofia",
            "preferred_language": "es-ES",
            "personality_level": "energetic",
        }

        persisted = brain.get_trainer_profile(user_email)
        assert persisted is not None
        assert persisted.trainer_type == "sofia"
        assert persisted.preferred_language == "es-ES"
        assert persisted.personality_level == "energetic"
    finally:
        app.dependency_overrides.clear()


def test_trainer_profile_roundtrip_tracks_pro_then_free_stateful_behavior():
    user_email = "pro-roundtrip@example.com"
    brain = StatefulTrainerBrain()
    brain.save_user_profile(_build_user(user_email, "Pro"))

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_ai_trainer_brain] = lambda: brain

    try:
        create_response = client.get("/trainer/trainer_profile")
        assert create_response.status_code == 200
        assert create_response.json() == {
            "user_email": user_email,
            "trainer_type": "atlas",
            "preferred_language": "pt-BR",
            "personality_level": "balanced",
        }

        create_persisted = brain.get_trainer_profile(user_email)
        assert create_persisted is not None
        assert create_persisted.trainer_type == "atlas"
        assert create_persisted.preferred_language == "pt-BR"
        assert create_persisted.personality_level == "balanced"

        update_response = client.put(
            "/trainer/update_trainer_profile",
            json={
                "trainer_type": "sofia",
                "preferred_language": "es-ES",
                "personality_level": "energetic",
            },
        )
        assert update_response.status_code == 200
        assert update_response.json() == {
            "user_email": user_email,
            "trainer_type": "sofia",
            "preferred_language": "es-ES",
            "personality_level": "energetic",
        }

        updated_persisted = brain.get_trainer_profile(user_email)
        assert updated_persisted is not None
        assert updated_persisted.trainer_type == "sofia"
        assert updated_persisted.preferred_language == "es-ES"
        assert updated_persisted.personality_level == "energetic"

        get_response = client.get("/trainer/trainer_profile")
        assert get_response.status_code == 200
        assert get_response.json() == update_response.json()

        brain.save_user_profile(_build_user(user_email, "Free"))

        downgraded_response = client.get("/trainer/trainer_profile")
        assert downgraded_response.status_code == 200
        assert downgraded_response.json() == {
            "user_email": user_email,
            "trainer_type": "gymbro",
            "preferred_language": "es-ES",
            "personality_level": "energetic",
        }

        downgraded_persisted = brain.get_trainer_profile(user_email)
        assert downgraded_persisted is not None
        assert downgraded_persisted.trainer_type == "gymbro"
        assert downgraded_persisted.preferred_language == "es-ES"
        assert downgraded_persisted.personality_level == "energetic"
    finally:
        app.dependency_overrides.clear()
