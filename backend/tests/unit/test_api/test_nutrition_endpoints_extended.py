"""
Extended comprehensive tests for nutrition endpoints.
Expands existing coverage with additional test cases for better code coverage.
Tests cover listing, statistics, imports, and deletion operations.
"""

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pytest
from datetime import date, timedelta
from io import BytesIO

from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from src.api.models.nutrition_log import NutritionWithId
from src.api.models.nutrition_stats import NutritionStats
from src.api.models.import_result import ImportResult


client = TestClient(app)


# Fixtures
@pytest.fixture
def sample_nutrition_log():
    return {
        "_id": "nut_001",
        "user_email": "test@example.com",
        "date": "2024-01-29T00:00:00",
        "calories": 2000,
        "protein_grams": 150.0,
        "carbs_grams": 250.0,
        "fat_grams": 70.0,
        "notes": "Good day"
    }


@pytest.fixture
def sample_nutrition_stats():
    from datetime import datetime
    from src.api.models.nutrition_stats import DailyMacros

    return NutritionStats(
        today=NutritionWithId(
            id="nut_today",
            user_email="test@example.com",
            date=datetime.fromisoformat("2024-01-29T00:00:00"),
            calories=2100,
            protein_grams=155.0,
            carbs_grams=260.0,
            fat_grams=75.0,
            notes="Today"
        ),
        weekly_adherence=[True, True, True, False, True, False, True],
        last_7_days=[
            DailyMacros(
                date=datetime.fromisoformat("2024-01-29T00:00:00"),
                calories=2100,
                protein=155.0,
                carbs=260.0,
                fat=75.0
            )
        ],
        avg_daily_calories=2050.0,
        avg_protein=150.0,
        total_logs=15
    )


# Test: GET /nutrition/list - Success Case
def test_list_nutrition_success(sample_nutrition_log):
    """Test retrieving paginated nutrition logs."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_nutrition_paginated.return_value = ([sample_nutrition_log], 1)
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/nutrition/list",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["logs"]) == 1
    assert data["total"] == 1
    assert data["page"] == 1
    assert data["page_size"] == 10

    app.dependency_overrides = {}


# Test: GET /nutrition/list - Multiple Pages
def test_list_nutrition_multiple_pages():
    """Test pagination with multiple pages."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()

    logs = [
        {"_id": f"nut_{i}", "user_email": "test@example.com",
         "date": str(date.today() - timedelta(days=i)), "calories": 2000,
         "protein_grams": 150.0, "carbs_grams": 250.0, "fat_grams": 70.0}
        for i in range(10)
    ]
    mock_db.get_nutrition_paginated.return_value = (logs, 25)
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/nutrition/list?page=1&page_size=10",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 25
    assert data["total_pages"] == 3
    assert data["page"] == 1

    app.dependency_overrides = {}


# Test: GET /nutrition/list - Filter by Days
def test_list_nutrition_filter_by_days():
    """Test filtering nutrition logs by recent days."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_nutrition_paginated.return_value = ([], 0)
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/nutrition/list?days=7",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    mock_db.get_nutrition_paginated.assert_called_once()
    call_kwargs = mock_db.get_nutrition_paginated.call_args[1]
    assert call_kwargs["days"] == 7

    app.dependency_overrides = {}


# Test: GET /nutrition/list - Unauthorized
def test_list_nutrition_unauthorized():
    """Test nutrition list without authentication."""
    response = client.get("/nutrition/list")
    assert response.status_code == 401


# Test: GET /nutrition/list - Database Error
def test_list_nutrition_database_error():
    """Test nutrition list when database error occurs."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_nutrition_paginated.side_effect = Exception("DB Connection Error")
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/nutrition/list",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 500
    assert "Failed to retrieve nutrition logs" in response.json()["detail"]

    app.dependency_overrides = {}


# Test: GET /nutrition/stats - Success Case
def test_get_nutrition_stats_success(sample_nutrition_stats):
    """Test retrieving nutrition statistics."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_nutrition_stats.return_value = sample_nutrition_stats
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/nutrition/stats",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["avg_daily_calories"] == 2050.0
    assert "last_7_days" in data
    assert data["avg_protein"] == 150.0

    app.dependency_overrides = {}


# Test: GET /nutrition/stats - Unauthorized
def test_get_nutrition_stats_unauthorized():
    """Test nutrition stats without authentication."""
    response = client.get("/nutrition/stats")
    assert response.status_code == 401


# Test: GET /nutrition/today - Success Case
def test_get_today_nutrition_success(sample_nutrition_log):
    """Test retrieving today's nutrition log."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    from datetime import datetime
    from src.api.models.nutrition_stats import DailyMacros

    mock_db.get_nutrition_stats.return_value = NutritionStats(
        today=NutritionWithId(**sample_nutrition_log),
        weekly_adherence=[True, True, True, False, True, False, True],
        last_7_days=[DailyMacros(
            date=datetime.fromisoformat("2024-01-29T00:00:00"),
            calories=2100,
            protein=155.0,
            carbs=260.0,
            fat=75.0
        )],
        avg_daily_calories=2000.0,
        avg_protein=150.0,
        total_logs=15
    )
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/nutrition/today",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data is not None

    app.dependency_overrides = {}


# Test: GET /nutrition/today - No Data
def test_get_today_nutrition_no_data():
    """Test retrieving today's nutrition when no data exists."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_nutrition_stats.return_value = NutritionStats(
        today=None,
        weekly_adherence=[False] * 7,
        last_7_days=[],
        avg_daily_calories=0.0,
        avg_protein=0.0,
        total_logs=0
    )
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/nutrition/today",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200

    app.dependency_overrides = {}


# Test: POST /nutrition/import/myfitnesspal - Success Case
@pytest.mark.asyncio
async def test_import_myfitnesspal_success():
    """Test successful CSV import from MyFitnessPal."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.bulk_insert_nutrition.return_value = None
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    with patch("src.api.endpoints.nutrition.import_nutrition_from_csv") as mock_import:
        mock_import.return_value = ImportResult(created=5, updated=0, errors=0, total_days=5)

        # Create a CSV file content
        csv_content = b"Date,Calories,Protein,Carbs,Fat\n2024-01-29,2000,150,250,70"

        response = client.post(
            "/nutrition/import/myfitnesspal",
            files={"file": ("test.csv", BytesIO(csv_content), "text/csv")},
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["created"] == 5
        assert data["updated"] == 0

    app.dependency_overrides = {}


# Test: POST /nutrition/import/myfitnesspal - Invalid File Type
@pytest.mark.asyncio
async def test_import_myfitnesspal_invalid_file():
    """Test import with non-CSV file."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.post(
        "/nutrition/import/myfitnesspal",
        files={"file": ("test.txt", BytesIO(b"invalid"), "text/plain")},
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 400

    app.dependency_overrides = {}


# Test: POST /nutrition/import/myfitnesspal - Unauthorized
@pytest.mark.asyncio
async def test_import_myfitnesspal_unauthorized():
    """Test import without authentication."""
    response = client.post(
        "/nutrition/import/myfitnesspal",
        files={"file": ("test.csv", BytesIO(b"data"), "text/csv")}
    )
    assert response.status_code == 401


# Test: DELETE /nutrition/{log_id} - Success Case
def test_delete_nutrition_success(sample_nutrition_log):
    """Test successful deletion of nutrition log."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_nutrition_by_id.return_value = sample_nutrition_log
    mock_db.delete_nutrition_log.return_value = True
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.delete(
        "/nutrition/nut_001",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "deleted successfully" in data["message"]

    app.dependency_overrides = {}


# Test: DELETE /nutrition/{log_id} - Not Found
def test_delete_nutrition_not_found():
    """Test deleting non-existent nutrition log."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_nutrition_by_id.return_value = None
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.delete(
        "/nutrition/nonexistent",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 404

    app.dependency_overrides = {}


# Test: DELETE /nutrition/{log_id} - Unauthorized Owner
def test_delete_nutrition_unauthorized_owner():
    """Test deleting nutrition log owned by another user."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_nutrition_by_id.return_value = {
        "user_email": "other@example.com",
        "_id": "nut_001"
    }
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.delete(
        "/nutrition/nut_001",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 403

    app.dependency_overrides = {}


# Test: DELETE /nutrition/{log_id} - Unauthorized (No Token)
def test_delete_nutrition_unauthorized():
    """Test deletion without authentication."""
    response = client.delete("/nutrition/nut_001")
    assert response.status_code == 401


# Test: GET /nutrition/list - Invalid Page Parameters
def test_list_nutrition_invalid_page_params():
    """Test with invalid pagination parameters."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    # Page 0 (should be minimum 1)
    response = client.get(
        "/nutrition/list?page=0",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 422  # Validation error

    app.dependency_overrides = {}
