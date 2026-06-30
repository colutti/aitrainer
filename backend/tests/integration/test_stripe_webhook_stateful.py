from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from bson import ObjectId
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.models.user_profile import UserProfile
from src.core.deps import get_ai_trainer_brain
from src.repositories.user_repository import UserRepository
from src.services.auth import verify_token


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
                for key in update.get("$unset", {}):
                    doc.pop(key, None)
                return FakeUpdateResult(modified_count=0 if doc == original else 1)

        if upsert:
            inserted_id = ObjectId()
            self.docs.append(
                {
                    "_id": inserted_id,
                    **deepcopy(query),
                    **deepcopy(update.get("$set", {})),
                }
            )
            return FakeUpdateResult(upserted_id=inserted_id, modified_count=0)

        return FakeUpdateResult(modified_count=0)

    def find_one(self, query: dict, projection: dict | None = None, sort=None) -> dict | None:
        del sort
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


class StatefulStripeDb:
    def __init__(self) -> None:
        self.database = FakeDatabase()
        self.users = UserRepository(self.database)

    def get_user_profile(self, email: str) -> UserProfile | None:
        return self.users.get_profile(email)

    def save_user_profile(self, profile: UserProfile) -> None:
        self.users.save_profile(profile)

    def update_user_profile_fields(self, email: str, fields: dict) -> bool:
        return self.users.update_profile_fields(email, fields)


class StatefulStripeBrain:
    def __init__(self, database: StatefulStripeDb) -> None:
        self.database = database
        self.ensure_calls: list[tuple[str, str]] = []

    def get_user_profile(self, email: str) -> UserProfile | None:
        return self.database.get_user_profile(email)

    def update_user_profile_fields(self, email: str, fields: dict) -> bool:
        return self.database.update_user_profile_fields(email, fields)

    def ensure_trainer_allowed(self, user_email: str, plan_name: str) -> None:
        self.ensure_calls.append((user_email, plan_name))


def test_stripe_webhook_stateful_roundtrip_updates_profile_subscription_lifecycle():
    user_email = "stripe@example.com"
    fake_db = StatefulStripeDb()
    fake_brain = StatefulStripeBrain(fake_db)
    fake_db.save_user_profile(
        UserProfile(
            email=user_email,
            role="user",
            gender="Masculino",
            age=30,
            weight=80.0,
            height=175,
            goal_type="maintain",
            weekly_rate=0.0,
            subscription_plan="Free",
            onboarding_completed=True,
            messages_sent_this_month=9,
        )
    )

    app.dependency_overrides[get_ai_trainer_brain] = lambda: fake_brain

    cycle_start_ts = int(datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp())
    expected_cycle_start = datetime.fromtimestamp(
        cycle_start_ts, tz=timezone.utc
    ).isoformat()
    fake_settings = SimpleNamespace(
        STRIPE_WEBHOOK_SECRET="whsec_test",
        STRIPE_PRICE_ID_BASIC="price_basic",
        STRIPE_PRICE_ID_PRO="price_pro",
    )

    with (
        patch("src.api.endpoints.stripe.settings", fake_settings),
    ):
        try:
            with patch("src.api.endpoints.stripe.stripe.Webhook.construct_event") as mock_construct:
                mock_construct.return_value = {
                    "type": "checkout.session.completed",
                    "data": {
                        "object": {
                            "metadata": {"user_email": user_email},
                            "customer": "cus_stateful_123",
                        }
                    },
                }
                checkout_response = client.post(
                    "/stripe/webhook",
                    content=b"checkout",
                    headers={"stripe-signature": "sig_test"},
                )
            assert checkout_response.status_code == 200
            assert checkout_response.json() == {"status": "success"}

            profile_after_checkout = fake_db.get_user_profile(user_email)
            assert profile_after_checkout is not None
            assert profile_after_checkout.stripe_customer_id == "cus_stateful_123"
            assert profile_after_checkout.subscription_plan == "Free"

            with patch("src.api.endpoints.stripe.stripe.Webhook.construct_event") as mock_construct:
                mock_construct.return_value = {
                    "type": "customer.subscription.updated",
                    "data": {
                        "object": {
                            "id": "sub_stateful_123",
                            "customer": "cus_stateful_123",
                            "status": "active",
                            "current_period_start": cycle_start_ts,
                            "items": {"data": [{"price": {"id": "price_pro"}}]},
                            "metadata": {"user_email": user_email},
                        }
                    },
                }
                subscription_response = client.post(
                    "/stripe/webhook",
                    content=b"subscription-updated",
                    headers={"stripe-signature": "sig_test"},
                )
            assert subscription_response.status_code == 200
            assert subscription_response.json() == {"status": "success"}

            profile_after_update = fake_db.get_user_profile(user_email)
            assert profile_after_update is not None
            assert profile_after_update.subscription_plan == "Pro"
            assert profile_after_update.stripe_subscription_status == "active"
            assert profile_after_update.stripe_subscription_id == "sub_stateful_123"
            assert profile_after_update.current_billing_cycle_start is not None
            assert (
                profile_after_update.current_billing_cycle_start.isoformat()
                == expected_cycle_start
            )
            assert profile_after_update.messages_sent_this_month == 0
            assert fake_brain.ensure_calls == [(user_email, "Pro")]

            fake_db.update_user_profile_fields(
                user_email, {"messages_sent_this_month": 5}
            )

            with patch("src.api.endpoints.stripe.stripe.Webhook.construct_event") as mock_construct:
                mock_construct.return_value = {
                    "type": "customer.subscription.updated",
                    "data": {
                        "object": {
                            "id": "sub_stateful_123",
                            "customer": "cus_stateful_123",
                            "status": "active",
                            "current_period_start": cycle_start_ts,
                            "items": {"data": [{"price": {"id": "price_pro"}}]},
                            "metadata": {"user_email": user_email},
                        }
                    },
                }
                repeated_update_response = client.post(
                    "/stripe/webhook",
                    content=b"subscription-updated-repeat",
                    headers={"stripe-signature": "sig_test"},
                )
            assert repeated_update_response.status_code == 200
            assert repeated_update_response.json() == {"status": "success"}

            profile_after_repeated_update = fake_db.get_user_profile(user_email)
            assert profile_after_repeated_update is not None
            assert profile_after_repeated_update.subscription_plan == "Pro"
            assert profile_after_repeated_update.messages_sent_this_month == 5
            assert fake_brain.ensure_calls == [(user_email, "Pro")]

            with patch("src.api.endpoints.stripe.stripe.Webhook.construct_event") as mock_construct:
                mock_construct.return_value = {
                    "type": "customer.subscription.deleted",
                    "data": {
                        "object": {
                            "id": "sub_stateful_123",
                            "customer": "cus_stateful_123",
                        }
                    },
                }
                delete_response = client.post(
                    "/stripe/webhook",
                    content=b"subscription-deleted",
                    headers={"stripe-signature": "sig_test"},
                )
            assert delete_response.status_code == 200
            assert delete_response.json() == {"status": "success"}

            profile_after_delete = fake_db.get_user_profile(user_email)
            assert profile_after_delete is not None
            assert profile_after_delete.subscription_plan == "Free"
            assert profile_after_delete.stripe_subscription_status == "canceled"
            assert profile_after_delete.stripe_subscription_id is None
            assert fake_brain.ensure_calls == [(user_email, "Pro"), (user_email, "Free")]
        finally:
            app.dependency_overrides.clear()


def test_stripe_checkout_then_webhook_then_portal_uses_persisted_customer_state():
    user_email = "stripe-flow@example.com"
    fake_db = StatefulStripeDb()
    fake_brain = StatefulStripeBrain(fake_db)
    fake_db.save_user_profile(
        UserProfile(
            email=user_email,
            role="user",
            gender="Masculino",
            age=31,
            weight=81.0,
            height=178,
            goal_type="maintain",
            weekly_rate=0.0,
            subscription_plan="Free",
            onboarding_completed=True,
        )
    )

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_ai_trainer_brain] = lambda: fake_brain

    fake_settings = SimpleNamespace(
        STRIPE_WEBHOOK_SECRET="whsec_test",
        STRIPE_PRICE_ID_BASIC="price_basic",
        STRIPE_PRICE_ID_PRO="price_pro",
    )

    with (
        patch("src.api.endpoints.stripe.settings", fake_settings),
        patch("src.api.endpoints.stripe.are_new_user_signups_enabled", return_value=True),
        patch(
            "src.api.endpoints.stripe.create_checkout_session",
            return_value="https://stripe.test/checkout/session_123",
        ) as mock_checkout,
        patch(
            "src.api.endpoints.stripe.create_customer_portal_session",
            return_value="https://stripe.test/portal/session_123",
        ) as mock_portal,
    ):
        try:
            checkout_response = client.post(
                "/stripe/create-checkout-session",
                json={
                    "price_id": "price_pro",
                    "success_url": "http://localhost:3000/success",
                    "cancel_url": "http://localhost:3000/cancel",
                },
                headers={"Authorization": "Bearer test_token"},
            )
            assert checkout_response.status_code == 200
            assert checkout_response.json() == {
                "url": "https://stripe.test/checkout/session_123"
            }
            mock_checkout.assert_called_once()
            assert mock_checkout.call_args.args[0].email == user_email
            assert mock_checkout.call_args.args[1:] == (
                "price_pro",
                "http://localhost:3000/success",
                "http://localhost:3000/cancel",
            )

            with patch("src.api.endpoints.stripe.stripe.Webhook.construct_event") as mock_construct:
                mock_construct.return_value = {
                    "type": "checkout.session.completed",
                    "data": {
                        "object": {
                            "metadata": {"user_email": user_email},
                            "customer": "cus_portal_ready_123",
                        }
                    },
                }
                webhook_response = client.post(
                    "/stripe/webhook",
                    content=b"checkout-completed",
                    headers={"stripe-signature": "sig_test"},
                )
            assert webhook_response.status_code == 200
            assert webhook_response.json() == {"status": "success"}

            persisted_after_webhook = fake_db.get_user_profile(user_email)
            assert persisted_after_webhook is not None
            assert persisted_after_webhook.stripe_customer_id == "cus_portal_ready_123"

            portal_response = client.post(
                "/stripe/create-portal-session",
                json={"return_url": "http://localhost:3000/settings"},
                headers={"Authorization": "Bearer test_token"},
            )
            assert portal_response.status_code == 200
            assert portal_response.json() == {
                "url": "https://stripe.test/portal/session_123"
            }
            mock_portal.assert_called_once_with(
                "cus_portal_ready_123",
                "http://localhost:3000/settings",
            )
        finally:
            app.dependency_overrides.clear()
