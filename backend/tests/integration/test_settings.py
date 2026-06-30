from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from types import SimpleNamespace

from bson import ObjectId
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.models.user_profile import UserProfile
from src.core.deps import get_mongo_database
from src.services.auth import create_token, verify_token
from src.repositories.user_repository import UserRepository
from src.repositories.token_repository import TokenRepository

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


class StatefulUserDb:
    def __init__(self) -> None:
        database = FakeDatabase()
        self.repo = UserRepository(database)
        self.tokens = TokenRepository(database)

    def get_user_profile(self, email: str) -> UserProfile | None:
        return self.repo.get_profile(email)

    def save_user_profile(self, profile: UserProfile) -> None:
        self.repo.save_profile(profile)

    def update_user_profile_fields(self, email: str, fields: dict) -> bool:
        return self.repo.update_profile_fields(email, fields)

    def is_demo_user(self, email: str) -> bool:
        return self.repo.is_demo_user(email)

    def add_token_to_blocklist(self, token: str, expires_at: datetime) -> None:
        self.tokens.add_to_blocklist(token, expires_at)

    def is_token_blocklisted(self, token: str) -> bool:
        return self.tokens.is_blocklisted(token)


def test_user_settings_roundtrip_updates_profile_identity_notifications_and_me():
    user_email = "test@example.com"
    fake_db = StatefulUserDb()
    fake_db.save_user_profile(
        UserProfile(
            email=user_email,
            role="user",
            gender="Masculino",
            age=30,
            weight=70.0,
            height=170,
            goal_type="maintain",
            weekly_rate=0.0,
            target_weight=None,
            subscription_plan="Free",
            display_name="Original Name",
            photo_base64="data:image/png;base64,old",
            notes="Original note",
            onboarding_completed=True,
            telegram_notify_on_workout=True,
            telegram_notify_on_nutrition=False,
            telegram_notify_on_weight=False,
            tdee_last_check_in="2026-03-10",
            tdee_last_target=2200,
        )
    )

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_mongo_database] = lambda: fake_db

    try:
        response = client.get("/user/profile")
        assert response.status_code == 200
        assert response.json()["display_name"] == "Original Name"

        update_payload = {
            "gender": "Feminino",
            "age": 31,
            "height": 168,
            "goal_type": "lose",
            "weekly_rate": 0.5,
            "target_weight": 64.5,
            "notes": "Updated note",
            "display_name": "Updated Name",
            "photo_base64": "data:image/png;base64,new",
            "onboarding_completed": False,
        }

        update_response = client.post("/user/update_profile", json=update_payload)
        assert update_response.status_code == 200
        assert update_response.json()["message"] == "Profile updated successfully"

        persisted_after_profile = fake_db.get_user_profile(user_email)
        assert persisted_after_profile is not None
        assert persisted_after_profile.gender == "Feminino"
        assert persisted_after_profile.age == 31
        assert persisted_after_profile.height == 168
        assert persisted_after_profile.goal_type == "lose"
        assert persisted_after_profile.weekly_rate == 0.5
        assert persisted_after_profile.target_weight == 64.5
        assert persisted_after_profile.notes == "Updated note"
        assert persisted_after_profile.display_name == "Updated Name"
        assert persisted_after_profile.photo_base64 == "data:image/png;base64,new"
        assert persisted_after_profile.onboarding_completed is False
        assert persisted_after_profile.weight == 70.0
        assert persisted_after_profile.tdee_last_check_in is None
        assert persisted_after_profile.tdee_last_target is None

        identity_response = client.post(
            "/user/update_identity",
            json={
                "display_name": "Identity Name",
                "photo_base64": "data:image/png;base64,identity",
            },
        )
        assert identity_response.status_code == 200
        assert identity_response.json()["message"] == "Identity updated successfully"

        notifications_response = client.post(
            "/user/telegram-notifications",
            json={
                "telegram_notify_on_workout": False,
                "telegram_notify_on_nutrition": True,
                "telegram_notify_on_weight": True,
            },
        )
        assert notifications_response.status_code == 200
        assert (
            notifications_response.json()["message"]
            == "Notification settings updated successfully"
        )

        persisted_after_notifications = fake_db.get_user_profile(user_email)
        assert persisted_after_notifications is not None
        assert persisted_after_notifications.display_name == "Identity Name"
        assert (
            persisted_after_notifications.photo_base64
            == "data:image/png;base64,identity"
        )
        assert persisted_after_notifications.telegram_notify_on_workout is False
        assert persisted_after_notifications.telegram_notify_on_nutrition is True
        assert persisted_after_notifications.telegram_notify_on_weight is True

        me_response = client.get("/user/me")
        assert me_response.status_code == 200
        assert me_response.json()["name"] == "Identity Name"
        assert me_response.json()["photo_base64"] == "data:image/png;base64,identity"
        assert me_response.json()["subscription_plan"] == "Free"
        assert me_response.json()["onboarding_completed"] is False
    finally:
        app.dependency_overrides.clear()


def test_user_settings_roundtrip_clears_nullable_fields_in_profile_and_identity():
    user_email = "clear-fields@example.com"
    fake_db = StatefulUserDb()
    fake_db.save_user_profile(
        UserProfile(
            email=user_email,
            role="user",
            gender="Masculino",
            age=34,
            weight=82.0,
            height=178,
            goal_type="maintain",
            weekly_rate=0.0,
            target_weight=79.0,
            subscription_plan="Pro",
            display_name="Filled Name",
            photo_base64="data:image/png;base64,filled",
            notes="Filled notes",
            onboarding_completed=True,
        )
    )

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_mongo_database] = lambda: fake_db

    try:
        clear_profile_response = client.post(
            "/user/update_profile",
            json={
                "goal_type": "maintain",
                "weekly_rate": 0.0,
                "target_weight": None,
                "notes": None,
            },
        )
        assert clear_profile_response.status_code == 200

        clear_identity_response = client.post(
            "/user/update_identity",
            json={
                "display_name": None,
                "photo_base64": None,
            },
        )
        assert clear_identity_response.status_code == 200

        persisted = fake_db.get_user_profile(user_email)
        assert persisted is not None
        assert persisted.target_weight is None
        assert persisted.notes is None
        assert persisted.display_name is None
        assert persisted.photo_base64 is None

        raw_doc = fake_db.repo.collection.find_one({"email": user_email})
        assert raw_doc is not None
        assert "target_weight" not in raw_doc
        assert "notes" not in raw_doc
        assert "display_name" not in raw_doc
        assert "photo_base64" not in raw_doc

        profile_response = client.get("/user/profile")
        assert profile_response.status_code == 200
        assert "target_weight" not in profile_response.json()
        assert profile_response.json()["notes"] is None

        me_response = client.get("/user/me")
        assert me_response.status_code == 200
        assert me_response.json()["name"] is None
        assert me_response.json()["photo_base64"] is None
    finally:
        app.dependency_overrides.clear()


def test_update_identity_partial_updates_preserve_other_identity_fields():
    user_email = "partial-identity@example.com"
    fake_db = StatefulUserDb()
    fake_db.save_user_profile(
        UserProfile(
            email=user_email,
            role="user",
            gender="Masculino",
            age=33,
            weight=78.0,
            height=177,
            goal_type="maintain",
            weekly_rate=0.0,
            subscription_plan="Pro",
            display_name="Existing Identity Name",
            photo_base64="data:image/png;base64,existing-photo",
            onboarding_completed=True,
        )
    )

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_mongo_database] = lambda: fake_db

    try:
        photo_only_response = client.post(
            "/user/update_identity",
            json={
                "photo_base64": "data:image/png;base64,updated-photo",
            },
        )
        assert photo_only_response.status_code == 200
        assert photo_only_response.json()["message"] == "Identity updated successfully"

        after_photo_only = fake_db.get_user_profile(user_email)
        assert after_photo_only is not None
        assert after_photo_only.display_name == "Existing Identity Name"
        assert after_photo_only.photo_base64 == "data:image/png;base64,updated-photo"

        name_only_response = client.post(
            "/user/update_identity",
            json={
                "display_name": "Updated Identity Name",
            },
        )
        assert name_only_response.status_code == 200
        assert name_only_response.json()["message"] == "Identity updated successfully"

        after_name_only = fake_db.get_user_profile(user_email)
        assert after_name_only is not None
        assert after_name_only.display_name == "Updated Identity Name"
        assert after_name_only.photo_base64 == "data:image/png;base64,updated-photo"

        me_response = client.get("/user/me")
        assert me_response.status_code == 200
        assert me_response.json()["name"] == "Updated Identity Name"
        assert me_response.json()["photo_base64"] == "data:image/png;base64,updated-photo"
    finally:
        app.dependency_overrides.clear()


def test_login_creates_profile_and_exposes_defaults_via_me():
    email = "new-user@example.com"
    fake_db = StatefulUserDb()
    app.dependency_overrides[get_mongo_database] = lambda: fake_db

    try:
        from unittest.mock import patch

        with (
            patch("src.api.endpoints.user.verify_id_token") as mock_verify,
            patch(
                "src.api.endpoints.user.are_new_user_signups_enabled",
                return_value=True,
            ),
        ):
            mock_verify.return_value = {
                "email": email,
                "email_verified": True,
                "name": "New User",
                "picture": "data:image/png;base64,avatar",
            }

            login_response = client.post("/user/login", json={"token": "firebase-token"})

        assert login_response.status_code == 200
        assert "token" in login_response.json()

        persisted = fake_db.get_user_profile(email)
        assert persisted is not None
        assert persisted.subscription_plan == "Free"
        assert persisted.display_name == "New User"
        assert persisted.photo_base64 == "data:image/png;base64,avatar"
        assert persisted.onboarding_completed is False
        assert persisted.goal_type == "maintain"
        assert persisted.height == 170

        app.dependency_overrides[verify_token] = lambda: email
        me_response = client.get("/user/me")
        assert me_response.status_code == 200
        assert me_response.json()["email"] == email
        assert me_response.json()["name"] == "New User"
        assert me_response.json()["photo_base64"] == "data:image/png;base64,avatar"
        assert me_response.json()["subscription_plan"] == "Free"
        assert me_response.json()["onboarding_completed"] is False
    finally:
        app.dependency_overrides.clear()


def test_public_config_reflects_signup_toggle_and_login_keeps_existing_user_access():
    email = "existing-user@example.com"
    fake_db = StatefulUserDb()
    fake_db.save_user_profile(
        UserProfile(
            email=email,
            role="user",
            gender="Masculino",
            age=32,
            weight=74.0,
            height=176,
            goal_type="maintain",
            weekly_rate=0.0,
            subscription_plan="Pro",
            display_name="Persisted User",
            onboarding_completed=True,
        )
    )

    app.dependency_overrides[get_mongo_database] = lambda: fake_db

    from unittest.mock import patch

    with (
        patch("src.api.endpoints.user.settings", SimpleNamespace(ENABLE_NEW_USER_SIGNUPS=False)),
        patch("src.api.endpoints.user.verify_id_token") as mock_verify,
    ):
        mock_verify.return_value = {
            "email": email,
            "email_verified": True,
            "name": "Persisted User",
            "picture": "data:image/png;base64,persisted",
        }

        public_config_response = client.get("/user/public-config")
        login_response = client.post("/user/login", json={"token": "firebase-token"})

    try:
        assert public_config_response.status_code == 200
        assert public_config_response.json() == {"enable_new_user_signups": False}

        assert login_response.status_code == 200
        assert "token" in login_response.json()

        persisted = fake_db.get_user_profile(email)
        assert persisted is not None
        assert persisted.display_name == "Persisted User"
        assert persisted.subscription_plan == "Pro"
        assert persisted.onboarding_completed is True

        app.dependency_overrides[verify_token] = lambda: email
        me_response = client.get("/user/me")
        assert me_response.status_code == 200
        assert me_response.json()["email"] == email
        assert me_response.json()["name"] == "Persisted User"
        assert me_response.json()["subscription_plan"] == "Pro"
        assert me_response.json()["onboarding_completed"] is True
    finally:
        app.dependency_overrides.clear()


def test_e2e_login_creates_and_refreshes_same_user_statefully():
    email = "bot-real@fityq.it"
    fake_db = StatefulUserDb()
    app.dependency_overrides[get_mongo_database] = lambda: fake_db

    try:
        from unittest.mock import patch

        with patch("src.api.endpoints.user.is_e2e_test_auth_enabled", return_value=True):
            create_response = client.post(
                "/user/e2e-login",
                json={
                    "email": email,
                    "display_name": "Real QA Bot",
                    "onboarding_completed": False,
                    "subscription_plan": "Free",
                    "is_demo": False,
                },
            )

            assert create_response.status_code == 200
            assert create_response.json()["email"] == email
            assert create_response.json()["token"]

            created = fake_db.get_user_profile(email)
            assert created is not None
            assert created.display_name == "Real QA Bot"
            assert created.onboarding_completed is False
            assert created.subscription_plan == "Free"
            assert created.is_demo is False

            refresh_response = client.post(
                "/user/e2e-login",
                json={
                    "email": email,
                    "display_name": "Updated QA Bot",
                    "onboarding_completed": True,
                    "subscription_plan": "Pro",
                    "is_demo": True,
                },
            )

        assert refresh_response.status_code == 200
        refreshed = fake_db.get_user_profile(email)
        assert refreshed is not None
        assert refreshed.display_name == "Updated QA Bot"
        assert refreshed.onboarding_completed is True
        assert refreshed.subscription_plan == "Pro"
        assert refreshed.is_demo is True
        assert refreshed.height == 180
        assert refreshed.goal_type == "maintain"
    finally:
        app.dependency_overrides.clear()


def test_logout_blocklists_token_and_rejects_future_authenticated_requests():
    email = "logout@example.com"
    fake_db = StatefulUserDb()
    app.dependency_overrides[get_mongo_database] = lambda: fake_db

    token = create_token(email)

    try:
        from unittest.mock import patch

        with patch("src.services.auth.get_mongo_database", return_value=fake_db):
            logout_response = client.post(
                "/user/logout",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert logout_response.status_code == 200
            assert logout_response.json()["message"] == "Logged out successfully"
            assert fake_db.is_token_blocklisted(token) is True

            refresh_response = client.post(
                "/user/refresh",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert refresh_response.status_code == 401
        assert refresh_response.json()["detail"] == "Could not validate credentials"
    finally:
        app.dependency_overrides.clear()
