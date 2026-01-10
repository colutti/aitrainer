"""
Tests for the health check endpoint in main.py
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.api.main import app


client = TestClient(app)


def test_health_endpoint_all_services_healthy():
    """Test health endpoint when all services are healthy."""
    with patch('src.api.main.get_mongo_database') as mock_mongo, \
         patch('src.api.main.get_mem0_client') as mock_mem0:
        
        # Mock MongoDB ping
        mock_db = MagicMock()
        mock_db.client.admin.command.return_value = {'ok': 1}
        mock_mongo.return_value = mock_db
        
        # Mock Mem0 client
        mock_mem0.return_value = MagicMock()
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["services"]["mongodb"] == "healthy"
        assert data["services"]["mem0"] == "healthy"


def test_health_endpoint_mongodb_unhealthy():
    """Test health endpoint when MongoDB is unhealthy."""
    with patch('src.api.main.get_mongo_database') as mock_mongo, \
         patch('src.api.main.get_mem0_client') as mock_mem0:
        
        # Mock MongoDB failure
        mock_mongo.side_effect = Exception("Connection failed")
        
        # Mock Mem0 client as healthy
        mock_mem0.return_value = MagicMock()
        
        response = client.get("/health")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "unhealthy" in data["services"]["mongodb"]
        assert data["services"]["mem0"] == "healthy"


def test_health_endpoint_mem0_unhealthy():
    """Test health endpoint when Mem0 is unhealthy."""
    with patch('src.api.main.get_mongo_database') as mock_mongo, \
         patch('src.api.main.get_mem0_client') as mock_mem0:
        
        # Mock MongoDB as healthy
        mock_db = MagicMock()
        mock_db.client.admin.command.return_value = {'ok': 1}
        mock_mongo.return_value = mock_db
        
        # Mock Mem0 failure
        mock_mem0.return_value = None
        
        response = client.get("/health")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["services"]["mongodb"] == "healthy"
        assert "unhealthy" in data["services"]["mem0"]


def test_health_endpoint_all_services_unhealthy():
    """Test health endpoint when all services are unhealthy."""
    with patch('src.api.main.get_mongo_database') as mock_mongo, \
         patch('src.api.main.get_mem0_client') as mock_mem0:
        
        # Mock MongoDB failure
        mock_mongo.side_effect = Exception("MongoDB down")
        
        # Mock Mem0 failure
        mock_mem0.side_effect = Exception("Mem0 down")
        
        response = client.get("/health")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "unhealthy" in data["services"]["mongodb"]
        assert "unhealthy" in data["services"]["mem0"]
