from datetime import date, timedelta
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from src.api.models.weight_log import WeightLog
from src.api.models.nutrition_log import NutritionLog

client = TestClient(app)


def mock_get_current_user():
    return "test@example.com"


def test_get_metabolism_summary():
    # Arrange
    app.dependency_overrides[verify_token] = mock_get_current_user
    mock_db = MagicMock()

    today = date.today()
    start_date = today - timedelta(days=20)

    # Mock data directly returning from DB calls in service
    weights = [
        WeightLog(
            user_email="test@example.com",
            date=start_date + timedelta(days=i),
            weight_kg=70.0,
        )
        for i in range(21)
    ]
    nutrition = [
        NutritionLog(
            user_email="test@example.com",
            date=start_date + timedelta(days=i),
            calories=2500,
            protein_grams=150,
            carbs_grams=250,
            fat_grams=80,
        )
        for i in range(21)
    ]

    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition
    mock_db.get_user_profile.return_value = MagicMock(weekly_rate=0.5, goal_type="lose")

    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    # Act
    response = client.get(
        "/metabolism/summary?weeks=3", headers={"Authorization": "Bearer test_token"}
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["tdee"] == 2500
    assert data["confidence"] == "high"
    assert data["avg_calories"] == 2500

    # Clean up
    app.dependency_overrides = {}


def test_get_metabolism_summary_insufficient():
    # Arrange
    app.dependency_overrides[verify_token] = mock_get_current_user
    mock_db = MagicMock()
    mock_db.get_weight_logs_by_date_range.return_value = []
    mock_db.get_nutrition_logs_by_date_range.return_value = []

    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    # Act
    response = client.get(
        "/metabolism/summary", headers={"Authorization": "Bearer token"}
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["tdee"] == 0
    assert data["confidence"] == "none"

    app.dependency_overrides = {}
