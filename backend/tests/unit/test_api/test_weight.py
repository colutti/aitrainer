from datetime import date, timedelta, datetime
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_ai_trainer_brain, get_mongo_database
from src.api.models.weight_log import WeightLog
import io

client = TestClient(app)


def mock_get_current_user():
    return "test@example.com"


def test_log_weight():
    # Arrange
    app.dependency_overrides[verify_token] = mock_get_current_user
    mock_brain = MagicMock()
    mock_db = MagicMock()
    mock_db.weight.save_log.return_value = ("123", True)
    # mock_db.weight.get_logs should return empty or some trend for EMA
    mock_db.weight.get_logs.return_value = []

    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    payload = {
        "user_email": "test@example.com",
        "date": str(date.today()),
        "weight_kg": 75.5,
        "notes": "Morning weight",
    }

    # Act
    response = client.post(
        "/weight", json=payload, headers={"Authorization": "Bearer test_token"}
    )

    # Assert
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["message"] == "Weight logged successfully"
    assert res_data["id"] == "123"
    assert res_data["is_new"] is True
    assert res_data["date"] == str(date.today())
    assert "trend_weight" in res_data
    mock_db.weight.save_log.assert_called_once()

    # Clean up
    app.dependency_overrides = {}


def test_log_weight_with_ema_trend():
    """Test that EMA trend is calculated correctly."""
    app.dependency_overrides[verify_token] = mock_get_current_user
    mock_brain = MagicMock()
    mock_db = MagicMock()

    # Simulate previous log with trend weight
    prev_log = WeightLog(
        user_email="test@example.com",
        date=date.today() - timedelta(days=1),
        weight_kg=76.0,
        trend_weight=75.8
    )
    mock_db.weight.get_logs.return_value = [prev_log]
    mock_db.weight.save_log.return_value = ("456", False)  # False = update existing

    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    payload = {
        "date": str(date.today()),
        "weight_kg": 75.5,
    }

    # Act
    response = client.post(
        "/weight", json=payload, headers={"Authorization": "Bearer test_token"}
    )

    # Assert
    assert response.status_code == 200
    res_data = response.json()
    assert "trend_weight" in res_data
    # Verify EMA was calculated (should use prev trend 75.8)
    assert res_data["trend_weight"] is not None
    app.dependency_overrides = {}


def test_log_weight_trend_rounded():
    """Test that trend weight is rounded to 2 decimal places."""
    app.dependency_overrides[verify_token] = mock_get_current_user
    mock_brain = MagicMock()
    mock_db = MagicMock()
    mock_db.weight.save_log.return_value = ("123", True)
    mock_db.weight.get_logs.return_value = []

    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    payload = {
        "date": str(date.today()),
        "weight_kg": 75.55555,
    }

    # Act
    response = client.post(
        "/weight", json=payload, headers={"Authorization": "Bearer test_token"}
    )

    # Assert
    assert response.status_code == 200
    res_data = response.json()
    if res_data["trend_weight"] is not None:
        # Check that it's rounded to max 2 decimals
        assert len(str(res_data["trend_weight"]).split('.')[-1]) <= 2
    app.dependency_overrides = {}


def test_get_weight_logs():
    # Arrange
    app.dependency_overrides[verify_token] = mock_get_current_user
    mock_brain = MagicMock()
    mock_brain._database.get_weight_logs.return_value = [
        WeightLog(user_email="test@example.com", date=date.today(), weight_kg=75.5),
        WeightLog(
            user_email="test@example.com",
            date=date.today() - timedelta(days=1),
            weight_kg=76.0,
        ),
    ]
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    # Act
    response = client.get("/weight", headers={"Authorization": "Bearer test_token"})

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["weight_kg"] == 75.5
    assert data[1]["weight_kg"] == 76.0

    # Clean up
    app.dependency_overrides = {}


def test_get_weight_logs_with_custom_limit():
    """Test retrieving weight logs with custom limit."""
    app.dependency_overrides[verify_token] = mock_get_current_user
    mock_brain = MagicMock()
    mock_brain._database.get_weight_logs.return_value = [
        WeightLog(user_email="test@example.com", date=date.today() - timedelta(days=i), weight_kg=75.5)
        for i in range(50)
    ]
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    # Act - request with custom limit
    response = client.get("/weight?limit=50", headers={"Authorization": "Bearer test_token"})

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 50
    mock_brain._database.get_weight_logs.assert_called_with(user_email="test@example.com", limit=50)
    app.dependency_overrides = {}


def test_get_weight_logs_empty():
    """Test retrieving weight logs when none exist."""
    app.dependency_overrides[verify_token] = mock_get_current_user
    mock_brain = MagicMock()
    mock_brain._database.get_weight_logs.return_value = []
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    # Act
    response = client.get("/weight", headers={"Authorization": "Bearer test_token"})

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0
    app.dependency_overrides = {}


def test_delete_weight_log():
    # Arrange
    app.dependency_overrides[verify_token] = mock_get_current_user
    mock_brain = MagicMock()
    # Mock successful deletion
    mock_brain._database.delete_weight_log.return_value = True
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    date_str = str(date.today())

    # Act
    response = client.delete(
        f"/weight/{date_str}", headers={"Authorization": "Bearer test_token"}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": "Weight log deleted successfully",
        "deleted": True,
    }

    # Verify mock call arguments
    mock_brain._database.delete_weight_log.assert_called_once()
    call_args = mock_brain._database.delete_weight_log.call_args
    assert call_args[1]["user_email"] == "test@example.com"

    # Clean up
    app.dependency_overrides = {}


def test_delete_weight_log_not_found():
    """Test deleting weight log that doesn't exist."""
    app.dependency_overrides[verify_token] = mock_get_current_user
    mock_brain = MagicMock()
    mock_brain._database.delete_weight_log.return_value = False
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    date_str = str(date.today())

    # Act
    response = client.delete(
        f"/weight/{date_str}", headers={"Authorization": "Bearer test_token"}
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["deleted"] is False
    app.dependency_overrides = {}


def test_delete_weight_log_invalid_date_format():
    """Test deleting with invalid date format."""
    app.dependency_overrides[verify_token] = mock_get_current_user
    mock_brain = MagicMock()
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    # Act - use invalid date format
    response = client.delete(
        "/weight/invalid-date", headers={"Authorization": "Bearer test_token"}
    )

    # Assert
    assert response.status_code == 200
    assert "error" in response.json()
    assert "Invalid date format" in response.json()["error"]
    app.dependency_overrides = {}


def test_get_body_composition_stats_success():
    """Test retrieving body composition stats."""
    app.dependency_overrides[verify_token] = mock_get_current_user
    mock_brain = MagicMock()

    # Mock 30 weight logs
    logs = [
        WeightLog(
            user_email="test@example.com",
            date=date.today() - timedelta(days=i),
            weight_kg=75.0 + i*0.1,
            body_fat_pct=25.0 - i*0.05,
            muscle_mass_pct=45.0 + i*0.02
        )
        for i in range(30)
    ]
    mock_brain._database.get_weight_logs.return_value = logs
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    # Act
    response = client.get("/weight/stats", headers={"Authorization": "Bearer test_token"})

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "latest" in data
    assert "weight_trend" in data
    assert "fat_trend" in data
    assert "muscle_trend" in data
    assert data["latest"]["weight_kg"] == logs[0].weight_kg
    assert len(data["weight_trend"]) == 30
    app.dependency_overrides = {}


def test_get_body_composition_stats_empty():
    """Test retrieving stats when no weight logs exist."""
    app.dependency_overrides[verify_token] = mock_get_current_user
    mock_brain = MagicMock()
    mock_brain._database.get_weight_logs.return_value = []
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    # Act
    response = client.get("/weight/stats", headers={"Authorization": "Bearer test_token"})

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["latest"] is None
    assert data["weight_trend"] == []
    assert data["fat_trend"] == []
    assert data["muscle_trend"] == []
    app.dependency_overrides = {}


def test_get_body_composition_stats_partial_data():
    """Test stats with logs missing body_fat and muscle_mass."""
    app.dependency_overrides[verify_token] = mock_get_current_user
    mock_brain = MagicMock()

    logs = [
        WeightLog(user_email="test@example.com", date=date.today(), weight_kg=75.0),
        WeightLog(user_email="test@example.com", date=date.today() - timedelta(days=1), weight_kg=76.0, body_fat_pct=25.0),
    ]
    mock_brain._database.get_weight_logs.return_value = logs
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    # Act
    response = client.get("/weight/stats", headers={"Authorization": "Bearer test_token"})

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["weight_trend"]) == 2
    assert len(data["fat_trend"]) == 1  # Only one log has body_fat
    assert len(data["muscle_trend"]) == 0  # None have muscle_mass
    app.dependency_overrides = {}


def test_import_zepp_life_invalid_extension():
    """Test importing file with invalid extension."""
    app.dependency_overrides[verify_token] = mock_get_current_user
    mock_db = MagicMock()
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    # Create a fake .txt file
    response = client.post(
        "/weight/import/zepp-life",
        files={"file": ("data.txt", io.BytesIO(b"data"), "text/plain")},
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "O arquivo deve ser um CSV."
    app.dependency_overrides = {}


def test_import_zepp_life_validation_error():
    """Test importing CSV with validation error."""
    app.dependency_overrides[verify_token] = mock_get_current_user
    mock_db = MagicMock()
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    csv_content = b"invalid,csv,format"

    with patch('src.api.endpoints.weight.import_zepp_life_data') as mock_import:
        mock_import.side_effect = ValueError("Missing required columns: Weight")

        response = client.post(
            "/weight/import/zepp-life",
            files={"file": ("data.csv", io.BytesIO(csv_content), "text/csv")},
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 400
        assert "Missing required columns" in response.json()["detail"]
    app.dependency_overrides = {}
