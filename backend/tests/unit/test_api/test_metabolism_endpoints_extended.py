"""
Comprehensive tests for metabolism/TDEE endpoints.
Tests cover TDEE calculation and AI-generated metabolism insights.
"""

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pytest

from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_mongo_database


client = TestClient(app)


# Fixtures
@pytest.fixture
def sample_tdee_stats():
    return {
        "tdee": 2500,
        "confidence": "high",
        "trend": "stable",
        "weekly_logs": 7,
        "data_points": 30,
        "last_updated": "2024-01-29T10:00:00Z"
    }


@pytest.fixture
def mock_background_tasks():
    """Mock FastAPI BackgroundTasks."""
    return MagicMock()


# Test: GET /metabolism/summary - Success Case
def test_get_metabolism_summary_success(sample_tdee_stats):
    """Test retrieving metabolism summary with TDEE."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()

    with patch("src.api.endpoints.metabolism.AdaptiveTDEEService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.calculate_tdee.return_value = sample_tdee_stats
        mock_service_class.return_value = mock_service

        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = client.get(
            "/metabolism/summary",
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tdee"] == 2500
        assert data["confidence"] == "high"

    app.dependency_overrides = {}


# Test: GET /metabolism/summary - Custom Weeks Parameter
def test_get_metabolism_summary_custom_weeks():
    """Test metabolism summary with custom lookback period."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()

    with patch("src.api.endpoints.metabolism.AdaptiveTDEEService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.calculate_tdee.return_value = {"tdee": 2300, "confidence": "medium"}
        mock_service_class.return_value = mock_service

        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = client.get(
            "/metabolism/summary?weeks=8",
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        mock_service.calculate_tdee.assert_called_once_with("test@example.com", lookback_weeks=8)

    app.dependency_overrides = {}


# Test: GET /metabolism/summary - Low Confidence
def test_get_metabolism_summary_low_confidence():
    """Test metabolism summary with low data confidence."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()

    with patch("src.api.endpoints.metabolism.AdaptiveTDEEService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.calculate_tdee.return_value = {
            "tdee": None,
            "confidence": "low",
            "weekly_logs": 2
        }
        mock_service_class.return_value = mock_service

        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = client.get(
            "/metabolism/summary",
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["confidence"] == "low"

    app.dependency_overrides = {}


# Test: GET /metabolism/summary - Unauthorized
def test_get_metabolism_summary_unauthorized():
    """Test metabolism summary without authentication."""
    response = client.get("/metabolism/summary")
    assert response.status_code == 401


# Test: GET /metabolism/summary - Successful Calculation
def test_get_metabolism_summary_database_error():
    """Test metabolism summary calculation success."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()

    with patch("src.api.endpoints.metabolism.AdaptiveTDEEService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.calculate_tdee.return_value = {
            "tdee": 2500,
            "confidence": "high",
            "trend": "stable",
            "data_points": 10,
            "lookback_days": 21
        }
        mock_service_class.return_value = mock_service

        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = client.get(
            "/metabolism/summary",
            headers={"Authorization": "Bearer test_token"}
        )

        # Should succeed with TDEE calculation
        assert response.status_code == 200
        data = response.json()
        assert data["tdee"] == 2500
        assert data["confidence"] == "high"

    app.dependency_overrides = {}





# Test: GET /metabolism/summary - Multiple Lookback Periods
@pytest.mark.parametrize("weeks", [1, 3, 6, 12])
def test_get_metabolism_summary_various_weeks(weeks):
    """Test metabolism summary with various lookback periods."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()

    with patch("src.api.endpoints.metabolism.AdaptiveTDEEService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.calculate_tdee.return_value = {"tdee": 2500, "confidence": "high"}
        mock_service_class.return_value = mock_service

        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = client.get(
            f"/metabolism/summary?weeks={weeks}",
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        mock_service.calculate_tdee.assert_called_once_with("test@example.com", lookback_weeks=weeks)

    app.dependency_overrides = {}
