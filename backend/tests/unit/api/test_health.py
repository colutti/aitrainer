"""Tests for the health check endpoint in main.py."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from pymongo.errors import PyMongoError
from src.api.main import app


client = TestClient(app)


def test_health_endpoint_all_services_healthy():
    """Test health endpoint when all services are healthy."""
    with patch("src.api.main.get_mongo_database") as mock_mongo:
        # Mock MongoDB ping
        mock_db = MagicMock()
        mock_db.client.admin.command.return_value = {"ok": 1}
        mock_mongo.return_value = mock_db
        with patch("src.api.main.get_qdrant_client") as mock_qdrant, patch(
            "src.api.main.ensure_firebase_initialized"
        ) as mock_firebase_init, patch(
            "src.api.main.get_app"
        ) as mock_get_app, patch("src.api.main.stripe") as mock_stripe:
            mock_qdrant.return_value.get_collections.return_value = {"collections": []}
            mock_qdrant.return_value.info.return_value = {"title": "qdrant"}
            mock_get_app.return_value = MagicMock()
            mock_stripe.api_key = None

            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["services"]["mongodb"] == "healthy"
            assert data["services"]["qdrant"] == "healthy"
            assert data["services"]["firebase"] == "healthy"
            assert data["services"]["stripe"] == "healthy"
            mock_firebase_init.assert_called_once()


def test_health_endpoint_mongodb_unhealthy():
    """Test health endpoint when MongoDB is unhealthy."""
    with patch("src.api.main.get_mongo_database") as mock_mongo:
        # Mock MongoDB failure
        mock_mongo.side_effect = PyMongoError("Connection failed")

        response = client.get("/health")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "unhealthy" in data["services"]["mongodb"]


def test_health_endpoint_qdrant_unhealthy():
    """Test health endpoint when Qdrant is unhealthy."""
    with patch("src.api.main.get_mongo_database") as mock_mongo, patch(
        "src.api.main.get_qdrant_client"
    ) as mock_qdrant, patch("src.api.main.ensure_firebase_initialized"), patch(
        "src.api.main.get_app"
    ) as mock_get_app:
        mock_db = MagicMock()
        mock_db.client.admin.command.return_value = {"ok": 1}
        mock_mongo.return_value = mock_db
        mock_qdrant.return_value.info.side_effect = RuntimeError("qdrant down")
        mock_get_app.return_value = MagicMock()

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "degraded" in data["services"]["qdrant"]


def test_health_endpoint_firebase_unhealthy():
    """Test health endpoint when Firebase Admin is unhealthy."""
    with patch("src.api.main.get_mongo_database") as mock_mongo, patch(
        "src.api.main.get_qdrant_client"
    ) as mock_qdrant, patch("src.api.main.ensure_firebase_initialized") as mock_init, patch(
        "src.api.main.get_app"
    ) as mock_get_app:
        mock_db = MagicMock()
        mock_db.client.admin.command.return_value = {"ok": 1}
        mock_mongo.return_value = mock_db
        mock_qdrant.return_value.info.return_value = {"title": "qdrant"}
        mock_init.side_effect = RuntimeError("firebase down")
        mock_get_app.return_value = MagicMock()

        response = client.get("/health")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "unhealthy" in data["services"]["firebase"]


def test_health_endpoint_stripe_unhealthy():
    """Test health endpoint when Stripe config is incomplete."""
    with patch("src.api.main.get_mongo_database") as mock_mongo, patch(
        "src.api.main.get_qdrant_client"
    ) as mock_qdrant, patch("src.api.main.ensure_firebase_initialized"), patch(
        "src.api.main.get_app"
    ) as mock_get_app, patch("src.api.main.stripe") as mock_stripe:
        mock_db = MagicMock()
        mock_db.client.admin.command.return_value = {"ok": 1}
        mock_mongo.return_value = mock_db
        mock_qdrant.return_value.info.return_value = {"title": "qdrant"}
        mock_get_app.return_value = MagicMock()
        mock_stripe.api_key = None
        with patch("src.api.main.settings") as mock_settings:
            mock_settings.STRIPE_API_KEY = ""
            mock_settings.STRIPE_WEBHOOK_SECRET = ""

            response = client.get("/health")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "unhealthy" in data["services"]["stripe"]


def test_health_endpoint_mongodb_unhealthy_with_exception():
    """Test health endpoint when MongoDB throws exception."""
    with patch("src.api.main.get_mongo_database") as mock_mongo:
        # Mock MongoDB failure
        mock_mongo.side_effect = PyMongoError("MongoDB down")

        response = client.get("/health")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "unhealthy" in data["services"]["mongodb"]
