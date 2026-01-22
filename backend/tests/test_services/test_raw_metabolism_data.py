import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock
from src.services.raw_metabolism_data import RawMetabolismDataService
from src.api.models.weight_log import WeightLog
from src.api.models.nutrition_log import NutritionLog
from src.api.models.user_profile import UserProfile


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    return RawMetabolismDataService(mock_db)


def test_get_raw_data_formatting(service, mock_db):
    # Setup mock data
    today = date.today()
    user_email = "test@test.com"

    # Mock return values
    mock_db.get_weight_logs_by_date_range.return_value = [
        WeightLog(
            user_email=user_email,
            date=today - timedelta(days=2),
            weight_kg=80.0,
            body_fat_pct=20.0,
            muscle_mass_pct=40.0,
            source="manual",
        )
    ]

    mock_db.get_nutrition_logs_by_date_range.return_value = [
        NutritionLog(
            user_email=user_email,
            date=datetime.now(),
            calories=2000,
            protein_grams=150,
            carbs_grams=200,
            fat_grams=60,
        )
    ]

    profile = UserProfile(
        email=user_email,
        gender="Masculino",
        age=30,
        weight=85.0,
        height=180,
        goal_type="lose",
    )
    mock_db.get_user_profile.return_value = profile

    # Execute
    data = service.get_raw_data_for_insight(user_email)

    # Verify
    assert data.weight_logs
    w_table = service.format_weight_logs_table(data.weight_logs)
    assert "| Data | Peso | %Gord |" in w_table
