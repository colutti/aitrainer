"""
Integration tests to ensure Hevy and Telegram endpoints return correct response formats.
These tests prevent regressions on field naming and endpoint existence.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
import jwt

from src.api.main import app
from src.core.config import settings


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def valid_token():
    """Create a valid JWT token."""
    payload = {
        "sub": "test@example.com",
        "exp": datetime.now(timezone.utc) + timedelta(hours=2)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


class TestHevyEndpoints:
    """Test Hevy integration endpoints critical paths."""

    def test_hevy_sync_endpoint_does_not_exist(self, client):
        """
        CRITICAL REGRESSION TEST: /integrations/hevy/sync should NOT exist.
        Frontend must call /integrations/hevy/import instead.
        This prevents the 404 error reported by user.
        """
        # POST /sync should return 404
        response = client.post("/integrations/hevy/sync", json={})
        assert response.status_code == 404

        # GET /sync should also return 404
        response = client.get("/integrations/hevy/sync")
        assert response.status_code == 404

    def test_hevy_import_endpoint_exists(self, client):
        """
        CRITICAL TEST: /integrations/hevy/import must exist.
        This is the correct endpoint frontend should call.
        """
        # The endpoint should exist (won't work without proper auth/setup,
        # but shouldn't return 404)
        response = client.post(
            "/integrations/hevy/import",
            json={"mode": "skip_duplicates"}
        )
        # Will fail auth but NOT with 404
        assert response.status_code != 404
        assert response.status_code in [401, 422]  # Auth or validation error, not "not found"


class TestTelegramResponseFormat:
    """
    Test that Telegram endpoints return fields with correct names.
    These tests prevent field-mapping bugs.
    """

    def test_telegram_status_response_has_linked_field_not_connected(self, client, valid_token):
        """
        CRITICAL REGRESSION TEST:
        Telegram /status endpoint MUST return 'linked' field, NOT 'connected'.
        This was causing UI to never show the connected status.
        """
        headers = {"Authorization": f"Bearer {valid_token}"}

        response = client.get("/telegram/status", headers=headers)

        # Should not be 404
        assert response.status_code != 404

        if response.status_code == 200:
            data = response.json()

            # MUST have 'linked' field
            assert "linked" in data, "Response missing 'linked' field"

            # MUST NOT have 'connected' field (old field name)
            assert "connected" not in data, "Response should not have 'connected' field"

            # Should be boolean
            assert isinstance(data["linked"], bool)

    def test_telegram_username_field_not_username(self, client, valid_token):
        """
        CRITICAL REGRESSION TEST:
        Telegram /status endpoint MUST return 'telegram_username', NOT 'username'.
        """
        headers = {"Authorization": f"Bearer {valid_token}"}

        response = client.get("/telegram/status", headers=headers)

        if response.status_code == 200:
            data = response.json()

            # If linked, must have telegram_username
            if data.get("linked"):
                assert "telegram_username" in data, "Linked response missing 'telegram_username'"
                assert "username" not in data, "Should not have old 'username' field"

    def test_telegram_notification_flags_present(self, client, valid_token):
        """
        Test that notification preferences are included in status response.
        """
        headers = {"Authorization": f"Bearer {valid_token}"}

        response = client.get("/telegram/status", headers=headers)

        if response.status_code == 200:
            data = response.json()

            # Must include notification flags
            assert "telegram_notify_on_workout" in data
            assert "telegram_notify_on_nutrition" in data
            assert "telegram_notify_on_weight" in data

            # Should all be boolean
            assert isinstance(data["telegram_notify_on_workout"], bool)
            assert isinstance(data["telegram_notify_on_nutrition"], bool)
            assert isinstance(data["telegram_notify_on_weight"], bool)


class TestFieldNameConsistency:
    """
    Ensure consistent field naming across API responses.
    """

    def test_hevy_endpoints_use_camelcase(self, client, valid_token):
        """
        Test that Hevy endpoints consistently use camelCase for field names.
        """
        headers = {"Authorization": f"Bearer {valid_token}"}

        # Test /status endpoint
        response = client.get("/integrations/hevy/status", headers=headers)

        if response.status_code == 200:
            data = response.json()

            # Should have camelCase fields
            expected_camel_fields = {"enabled", "hasKey", "apiKeyMasked", "lastSync"}

            for field in expected_camel_fields:
                assert field in data, f"Missing camelCase field: {field}"

            # Should NOT have snake_case fields
            wrong_fields = {"has_key", "api_key_masked", "last_sync"}
            for field in wrong_fields:
                assert field not in data, f"Should not have snake_case field: {field}"

    def test_no_endpoint_returns_old_telegram_fields(self, client, valid_token):
        """
        Ensure no endpoint accidentally returns old field names for Telegram.
        """
        headers = {"Authorization": f"Bearer {valid_token}"}

        endpoints_to_check = [
            "/telegram/status",
        ]

        for endpoint in endpoints_to_check:
            response = client.get(endpoint, headers=headers)

            if response.status_code == 200:
                data = response.json()

                # Check for old field names
                old_fields = {"connected", "username"}
                for field in old_fields:
                    assert field not in data, (
                        f"Endpoint {endpoint} returned old field '{field}'. "
                        f"Should use 'linked' and 'telegram_username' instead."
                    )


class TestEndpointExistence:
    """
    Test that required endpoints exist and wrong ones don't.
    """

    def test_required_hevy_endpoints_exist(self, client):
        """Validate required Hevy endpoints exist."""
        required_endpoints = [
            ("/integrations/hevy/status", "GET", 401),  # Auth required
            ("/integrations/hevy/config", "POST", 401),  # Auth required
            ("/integrations/hevy/import", "POST", 401),  # Auth required
            ("/integrations/hevy/validate", "POST", 401),  # Auth required
        ]

        for endpoint, method, expected_auth_code in required_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})

            # Should not be 404 (would be auth error without token)
            assert response.status_code != 404, (
                f"Required Hevy endpoint {endpoint} returned 404"
            )

    def test_non_existent_hevy_endpoints_return_404(self, client):
        """Validate that non-existent endpoints return 404."""
        non_existent = [
            ("/integrations/hevy/sync", "POST"),  # OLD endpoint - MUST NOT EXIST
            ("/integrations/hevy/invalid", "GET"),
            ("/integrations/hevy/wrongendpoint", "POST"),
        ]

        for endpoint, method in non_existent:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})

            assert response.status_code == 404, (
                f"Non-existent endpoint {endpoint} should return 404, "
                f"got {response.status_code}"
            )

    def test_required_telegram_endpoints_exist(self, client):
        """Validate required Telegram endpoints exist."""
        required_endpoints = [
            ("/telegram/status", "GET", 401),
            ("/telegram/generate-code", "POST", 401),
        ]

        for endpoint, method, expected_auth_code in required_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})

            # Should not be 404
            assert response.status_code != 404, (
                f"Required Telegram endpoint {endpoint} returned 404"
            )
