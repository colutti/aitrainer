from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from src.api.models.import_result import ImportResult

client = TestClient(app)

def mock_get_current_user():
    return "test@example.com"

def test_import_endpoint_success():
    # Arrange
    app.dependency_overrides[verify_token] = mock_get_current_user
    mock_db = MagicMock()
    app.dependency_overrides[get_mongo_database] = lambda: mock_db
    
    with patch("src.api.endpoints.nutrition.import_nutrition_from_csv") as mock_import:
        mock_import.return_value = ImportResult(
            created=5, updated=2, errors=0, total_days=7
        )
        
        csv_content = b"Data,Calorias\n2024-01-01,100"
        files = {"file": ("test.csv", csv_content, "text/csv")}
        
        # Act
        response = client.post(
            "/nutrition/import/myfitnesspal",
            headers={"Authorization": "Bearer test_token"},
            files=files
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["created"] == 5
        assert data["updated"] == 2
        assert data["total_days"] == 7
        
        mock_import.assert_called_once()
        args = mock_import.call_args[0]
        assert args[0] == "test@example.com"
        assert args[1] == "Data,Calorias\n2024-01-01,100"
    
    app.dependency_overrides = {}


def test_import_endpoint_invalid_extension():
    app.dependency_overrides[verify_token] = mock_get_current_user
    mock_db = MagicMock()
    app.dependency_overrides[get_mongo_database] = lambda: mock_db
    
    files = {"file": ("test.txt", b"content", "text/plain")}
    response = client.post(
        "/nutrition/import/myfitnesspal",
        headers={"Authorization": "Bearer test_token"},
        files=files
    )
    assert response.status_code == 400
    assert "CSV" in response.json()["detail"]
    
    app.dependency_overrides = {}


def test_import_service_validation_error():
    app.dependency_overrides[verify_token] = mock_get_current_user
    mock_db = MagicMock()
    app.dependency_overrides[get_mongo_database] = lambda: mock_db
    
    with patch("src.api.endpoints.nutrition.import_nutrition_from_csv") as mock_import:
        mock_import.side_effect = ValueError("Missing columns")
        
        files = {"file": ("test.csv", b"content", "text/csv")}
        response = client.post(
            "/nutrition/import/myfitnesspal",
            headers={"Authorization": "Bearer test_token"},
            files=files
        )
        
        assert response.status_code == 400
        assert "Missing columns" in response.json()["detail"]
        
    app.dependency_overrides = {}
