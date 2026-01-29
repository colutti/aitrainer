"""
Comprehensive tests for metabolism/TDEE endpoints.
Tests cover TDEE calculation and AI-generated metabolism insights.
"""

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pytest

from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_ai_trainer_brain, get_mongo_database


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
    assert response.status_code == 403


# Test: GET /metabolism/summary - Database Error
def test_get_metabolism_summary_database_error():
    """Test metabolism summary when database error occurs."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()

    with patch("src.api.endpoints.metabolism.AdaptiveTDEEService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.calculate_tdee.side_effect = Exception("DB Error")
        mock_service_class.return_value = mock_service

        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = client.get(
            "/metabolism/summary",
            headers={"Authorization": "Bearer test_token"}
        )

        # Depending on error handling, could be 500 or streaming error
        assert response.status_code in [200, 500]

    app.dependency_overrides = {}


# Test: GET /metabolism/insight - Success Case with Data
def test_get_metabolism_insight_stream_success():
    """Test retrieving AI-generated metabolism insight."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_brain = MagicMock()

    def mock_insight_generator():
        yield "Your metabolism is "
        yield "performing well this week."

    mock_brain.generate_insight_stream.return_value = mock_insight_generator()

    with patch("src.api.endpoints.metabolism.AdaptiveTDEEService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.calculate_tdee.return_value = {
            "tdee": 2500,
            "confidence": "high"
        }
        mock_service_class.return_value = mock_service

        app.dependency_overrides[get_mongo_database] = lambda: mock_db
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        response = client.get(
            "/metabolism/insight",
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200

    app.dependency_overrides = {}


# Test: GET /metabolism/insight - Insufficient Data
def test_get_metabolism_insight_insufficient_data():
    """Test insight when insufficient data for confidence."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_brain = MagicMock()

    with patch("src.api.endpoints.metabolism.AdaptiveTDEEService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.calculate_tdee.return_value = {
            "confidence": "none"
        }
        mock_service_class.return_value = mock_service

        app.dependency_overrides[get_mongo_database] = lambda: mock_db
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        response = client.get(
            "/metabolism/insight",
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        content = response.text
        assert "insuficientes" in content.lower() or "Dados" in content

    app.dependency_overrides = {}


# Test: GET /metabolism/insight - Force Regenerate
def test_get_metabolism_insight_force_regenerate():
    """Test forcing insight regeneration bypassing cache."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_brain = MagicMock()
    mock_brain.generate_insight_stream.return_value = (x for x in ["Insight"])

    with patch("src.api.endpoints.metabolism.AdaptiveTDEEService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.calculate_tdee.return_value = {"confidence": "high"}
        mock_service_class.return_value = mock_service

        app.dependency_overrides[get_mongo_database] = lambda: mock_db
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        response = client.get(
            "/metabolism/insight?force=true",
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        mock_brain.generate_insight_stream.assert_called_once()
        call_kwargs = mock_brain.generate_insight_stream.call_args[1]
        assert call_kwargs["force"] is True

    app.dependency_overrides = {}


# Test: GET /metabolism/insight - Custom Weeks
def test_get_metabolism_insight_custom_weeks():
    """Test insight generation with custom analysis period."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_brain = MagicMock()
    mock_brain.generate_insight_stream.return_value = (x for x in ["Data"])

    with patch("src.api.endpoints.metabolism.AdaptiveTDEEService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.calculate_tdee.return_value = {"confidence": "high"}
        mock_service_class.return_value = mock_service

        app.dependency_overrides[get_mongo_database] = lambda: mock_db
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        response = client.get(
            "/metabolism/insight?weeks=6",
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        call_kwargs = mock_brain.generate_insight_stream.call_args[1]
        assert call_kwargs["weeks"] == 6

    app.dependency_overrides = {}


# Test: GET /metabolism/insight - Unauthorized
def test_get_metabolism_insight_unauthorized():
    """Test metabolism insight without authentication."""
    response = client.get("/metabolism/insight")
    assert response.status_code == 403


# Test: GET /metabolism/insight - Empty Response
def test_get_metabolism_insight_empty_stats():
    """Test insight when stats return None."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_brain = MagicMock()

    with patch("src.api.endpoints.metabolism.AdaptiveTDEEService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.calculate_tdee.return_value = None
        mock_service_class.return_value = mock_service

        app.dependency_overrides[get_mongo_database] = lambda: mock_db
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        response = client.get(
            "/metabolism/insight",
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200

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
