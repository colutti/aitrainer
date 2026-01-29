"""
Extended comprehensive tests for weight endpoints.
Expands existing coverage with additional test cases for better code coverage.
Tests cover logging, stats, imports, and deletion operations.
"""

from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
import pytest
from datetime import date, timedelta
from io import BytesIO

from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_ai_trainer_brain, get_mongo_database
from src.api.models.weight_log import WeightLog, WeightLogInput
from src.api.models.import_result import ImportResult


client = TestClient(app)


# Fixtures
@pytest.fixture
def sample_weight_log():
    return WeightLog(
        user_email="test@example.com",
        date=date.today(),
        weight_kg=75.5,
        body_fat_pct=22.0,
        muscle_mass_pct=45.0,
        notes="Morning weight",
        trend_weight=75.3
    )


@pytest.fixture
def sample_weight_logs():
    """Generate sample weight logs for trend analysis."""
    logs = []
    for i in range(5):
        log_date = date.today() - timedelta(days=i)
        logs.append(WeightLog(
            user_email="test@example.com",
            date=log_date,
            weight_kg=75.5 - (i * 0.3),
            body_fat_pct=22.0 - (i * 0.1),
            muscle_mass_pct=45.0 + (i * 0.05),
            trend_weight=75.3 - (i * 0.3)
        ))
    return logs


# Test: POST /weight - Success (New Log)
def test_log_weight_new():
    """Test logging a new weight entry."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_db = MagicMock()

    mock_db.weight.get_logs.return_value = []
    mock_db.weight.save_log.return_value = ("weight_123", True)

    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    payload = {
        "date": str(date.today()),
        "weight_kg": 75.5,
        "body_fat_pct": 22.0,
        "notes": "Morning weight"
    }

    response = client.post(
        "/weight",
        json=payload,
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Weight logged successfully"
    assert data["is_new"] is True
    assert data["id"] == "weight_123"

    app.dependency_overrides = {}


# Test: POST /weight - Update Existing Log
def test_log_weight_update():
    """Test updating existing weight log for same date."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_db = MagicMock()

    prev_log = WeightLog(
        user_email="test@example.com",
        date=date.today(),
        weight_kg=76.0,
        trend_weight=75.8
    )
    mock_db.weight.get_logs.return_value = [prev_log]
    mock_db.weight.save_log.return_value = ("weight_123", False)

    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    payload = {
        "date": str(date.today()),
        "weight_kg": 75.5,
    }

    response = client.post(
        "/weight",
        json=payload,
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_new"] is False

    app.dependency_overrides = {}


# Test: POST /weight - Unauthorized
def test_log_weight_unauthorized():
    """Test weight logging without authentication."""
    payload = {
        "date": str(date.today()),
        "weight_kg": 75.5
    }

    response = client.post("/weight", json=payload)
    assert response.status_code == 401


# Test: DELETE /weight/{date_str} - Success
def test_delete_weight_log_success():
    """Test successful deletion of weight log."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_brain._database.delete_weight_log.return_value = True
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.delete(
        f"/weight/{date.today().isoformat()}",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] is True

    app.dependency_overrides = {}


# Test: DELETE /weight/{date_str} - Not Found
def test_delete_weight_log_not_found():
    """Test deleting non-existent weight log."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_brain._database.delete_weight_log.return_value = False
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.delete(
        f"/weight/{date.today().isoformat()}",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] is False

    app.dependency_overrides = {}


# Test: DELETE /weight/{date_str} - Invalid Date Format
def test_delete_weight_log_invalid_date():
    """Test deletion with invalid date format."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.delete(
        "/weight/invalid-date",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "Invalid date format" in data["error"]

    app.dependency_overrides = {}


# Test: GET /weight - Success
def test_get_weight_logs_success(sample_weight_logs):
    """Test retrieving weight logs."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_brain._database.get_weight_logs.return_value = sample_weight_logs
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.get(
        "/weight",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 5

    app.dependency_overrides = {}


# Test: GET /weight - Custom Limit
def test_get_weight_logs_custom_limit():
    """Test retrieving weight logs with custom limit."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_brain._database.get_weight_logs.return_value = []
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.get(
        "/weight?limit=50",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    mock_brain._database.get_weight_logs.assert_called_once()
    call_kwargs = mock_brain._database.get_weight_logs.call_args[1]
    assert call_kwargs["limit"] == 50

    app.dependency_overrides = {}


# Test: GET /weight/stats - Success with Trends
def test_get_body_composition_stats_success(sample_weight_logs):
    """Test retrieving body composition stats with trends."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_brain._database.get_weight_logs.return_value = sample_weight_logs
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.get(
        "/weight/stats",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "latest" in data
    assert "weight_trend" in data
    assert "fat_trend" in data
    assert "muscle_trend" in data
    assert len(data["weight_trend"]) > 0

    app.dependency_overrides = {}


# Test: GET /weight/stats - No Data
def test_get_body_composition_stats_no_data():
    """Test stats when no weight logs exist."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_brain._database.get_weight_logs.return_value = []
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.get(
        "/weight/stats",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["latest"] is None
    assert data["weight_trend"] == []

    app.dependency_overrides = {}


# Test: GET /weight/stats - Unauthorized
def test_get_body_composition_stats_unauthorized():
    """Test stats without authentication."""
    response = client.get("/weight/stats")
    assert response.status_code == 401


# Test: POST /weight/import/zepp-life - Success
@pytest.mark.asyncio
async def test_import_zepp_life_success():
    """Test successful import from Zepp Life."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    with patch("src.api.endpoints.weight.import_zepp_life_data") as mock_import:
        mock_import.return_value = ImportResult(created=10, updated=2, errors=0, total_days=30)

        csv_content = b"Date,Weight,BodyFat\n2024-01-29,75.5,22.0"

        response = client.post(
            "/weight/import/zepp-life",
            files={"file": ("zepp.csv", BytesIO(csv_content), "text/csv")},
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["created"] == 10
        assert data["updated"] == 2

    app.dependency_overrides = {}


# Test: POST /weight/import/zepp-life - Invalid File Type
@pytest.mark.asyncio
async def test_import_zepp_life_invalid_file():
    """Test import with non-CSV file."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.post(
        "/weight/import/zepp-life",
        files={"file": ("zepp.json", BytesIO(b"{}"), "application/json")},
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 400

    app.dependency_overrides = {}


# Test: POST /weight/import/zepp-life - Unauthorized
@pytest.mark.asyncio
async def test_import_zepp_life_unauthorized():
    """Test import without authentication."""
    response = client.post(
        "/weight/import/zepp-life",
        files={"file": ("zepp.csv", BytesIO(b"data"), "text/csv")}
    )
    assert response.status_code == 401


# Test: GET /weight - Unauthorized
def test_get_weight_logs_unauthorized():
    """Test weight logs retrieval without authentication."""
    response = client.get("/weight")
    assert response.status_code == 401


# Test: POST /weight - Missing Required Fields
def test_log_weight_missing_fields():
    """Test weight logging with missing required fields."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"

    payload = {
        # Missing date and weight_kg
        "notes": "Missing required fields"
    }

    response = client.post(
        "/weight",
        json=payload,
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 422

    app.dependency_overrides = {}
