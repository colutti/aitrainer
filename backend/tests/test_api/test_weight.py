from datetime import date, timedelta
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_ai_trainer_brain
from src.api.models.weight_log import WeightLog

client = TestClient(app)

def mock_get_current_user():
    return "test@example.com"

def test_log_weight():
    # Arrange
    app.dependency_overrides[verify_token] = mock_get_current_user
    mock_brain = MagicMock()
    mock_brain.db.save_weight_log.return_value = ("123", True)
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
    
    payload = {
        "user_email": "test@example.com",
        "date": str(date.today()),
        "weight_kg": 75.5,
        "notes": "Morning weight"
    }
    
    # Act
    response = client.post(
        "/weight",
        json=payload,
        headers={"Authorization": "Bearer test_token"}
    )
    
    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": "Weight logged successfully",
        "id": "123",
        "is_new": True,
        "date": str(date.today())
    }
    mock_brain.db.save_weight_log.assert_called_once()
    
    # Clean up
    app.dependency_overrides = {}

def test_get_weight_logs():
    # Arrange
    app.dependency_overrides[verify_token] = mock_get_current_user
    mock_brain = MagicMock()
    mock_brain.db.get_weight_logs.return_value = [
        WeightLog(user_email="test@example.com", date=date.today(), weight_kg=75.5),
        WeightLog(user_email="test@example.com", date=date.today() - timedelta(days=1), weight_kg=76.0),
    ]
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
    
    # Act
    response = client.get(
        "/weight",
        headers={"Authorization": "Bearer test_token"}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["weight_kg"] == 75.5
    assert data[1]["weight_kg"] == 76.0
    
    # Clean up
    app.dependency_overrides = {}
