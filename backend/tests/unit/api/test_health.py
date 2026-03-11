"""
Tests for the health check endpoint in main.py
"""

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.api.main import app


client = TestClient(app)


def test_health_endpoint_all_services_healthy():
    """Test health endpoint when all services are healthy."""
    with patch("src.api.main.get_mongo_database") as mock_mongo:
        # Mock MongoDB ping
        mock_db = MagicMock()
        mock_db.client.admin.command.return_value = {"ok": 1}
        mock_mongo.return_value = mock_db

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["services"]["mongodb"] == "healthy"


def test_health_endpoint_mongodb_unhealthy():
    """Test health endpoint when MongoDB is unhealthy."""
    with patch("src.api.main.get_mongo_database") as mock_mongo:
        # Mock MongoDB failure
        mock_mongo.side_effect = Exception("Connection failed")

        response = client.get("/health")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "unhealthy" in data["services"]["mongodb"]


def test_health_endpoint_mongodb_unhealthy_with_exception():
    """Test health endpoint when MongoDB throws exception."""
    with patch("src.api.main.get_mongo_database") as mock_mongo:
        # Mock MongoDB failure
        mock_mongo.side_effect = Exception("MongoDB down")

        response = client.get("/health")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "unhealthy" in data["services"]["mongodb"]
