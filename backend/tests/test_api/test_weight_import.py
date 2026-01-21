from fastapi import UploadFile
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from src.api.models.import_result import ImportResult
from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_mongo_database

client = TestClient(app)

def test_import_zepp_life_endpoint():
    """Test the Zepp Life import endpoint."""
    
    mock_db = MagicMock()
    app.dependency_overrides[verify_token] = lambda: "test@test.com"
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    # Mock the service function
    with patch("src.api.endpoints.weight.import_zepp_life_data") as mock_import:
        mock_import.return_value = ImportResult(
            created=1,
            updated=0,
            errors=0,
            total_days=1,
            error_messages=[]
        )
        
        # Prepare file upload
        files = {"file": ("test.csv", "time,weight,fatRate\n2025-01-01,80,20", "text/csv")}
        
        response = client.post(
            "/weight/import/zepp-life",
            files=files,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["created"] == 1
        assert data["updated"] == 0
        
        # Verify service call
        mock_import.assert_called_once()
    
    app.dependency_overrides = {}

def test_import_zepp_life_invalid_file():
    """Test uploading a non-CSV file."""
    app.dependency_overrides[verify_token] = lambda: "test@test.com"
    
    files = {"file": ("test.txt", "some content", "text/plain")}
    response = client.post(
        "/weight/import/zepp-life",
        files=files
    )
    assert response.status_code == 400
    assert "CSV" in response.json()["detail"]
    
    app.dependency_overrides = {}
