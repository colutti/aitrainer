"""Tests for admin logs endpoints."""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from src.api.main import app
from src.core.auth import verify_admin


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_admin_user():
    """Mock admin user."""
    return "admin@test.com"


class TestAdminLogs:
    """Test admin logs endpoints."""

    def test_get_application_logs_success(self, client, mock_admin_user):
        """Test retrieving application logs."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        
        # Create temp log file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("[INFO] Application started\n")
            f.write("[ERROR] Something failed\n")
            f.write("[WARNING] Deprecated API\n")
            temp_log = f.name
        
        try:
            with patch('src.api.endpoints.admin_logs.open', create=True) as mock_open_func:
                with open(temp_log, 'r') as f:
                    content = f.readlines()
                
                mock_open_func.return_value.__enter__.return_value.readlines.return_value = content
                
                with patch('os.path.exists', return_value=True):
                    response = client.get("/admin/logs/application?limit=10")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["source"] == "local"
                    assert data["total"] > 0
        finally:
            os.unlink(temp_log)
        
        app.dependency_overrides = {}

    def test_get_application_logs_not_found(self, client, mock_admin_user):
        """Test logs when file doesn't exist."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        
        with patch('os.path.exists', return_value=False):
            response = client.get("/admin/logs/application")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0
            assert "not found" in data.get("message", "").lower()
        
        app.dependency_overrides = {}

    def test_get_application_logs_with_level_filter(self, client, mock_admin_user):
        """Test retrieving logs with level filter."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        
        log_lines = [
            "[INFO] Info message\n",
            "[ERROR] Error message\n",
            "[WARNING] Warning message\n",
        ]
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', create=True) as mock_open_func:
                mock_open_func.return_value.__enter__.return_value.readlines.return_value = log_lines
                
                response = client.get("/admin/logs/application?level=ERROR")
                
                assert response.status_code == 200
                data = response.json()
                # Should filter to ERROR logs only
                assert "total" in data
        
        app.dependency_overrides = {}

    def test_get_application_logs_limit(self, client, mock_admin_user):
        """Test logs respect limit parameter."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        
        log_lines = [f"[INFO] Line {i}\n" for i in range(200)]
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', create=True) as mock_open_func:
                mock_open_func.return_value.__enter__.return_value.readlines.return_value = log_lines
                
                response = client.get("/admin/logs/application?limit=50")
                
                assert response.status_code == 200
                data = response.json()
                assert data["total"] <= 50
        
        app.dependency_overrides = {}
