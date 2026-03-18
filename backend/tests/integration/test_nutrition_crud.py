from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from bson import ObjectId
from datetime import datetime

client = TestClient(app)

def test_nutrition_crud_operations():
    """
    Test creating, listing and deleting nutrition logs using direct overrides.
    """
    user_email = "test@example.com"
    mock_db = MagicMock()
    
    # Overrides
    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_mongo_database] = lambda: mock_db
    
    try:
        # 1. Create Nutrition Log
        log_obj_id = ObjectId()
        log_id = str(log_obj_id)
        payload = {
            "date": "2026-03-17T10:00:00",
            "calories": 2500,
            "protein_grams": 150.0,
            "carbs_grams": 300.0,
            "fat_grams": 70.0,
            "fiber_grams": 30.0,
            "source": "manual"
        }
        
        # Mock DB response
        mock_db.save_nutrition_log.return_value = (log_obj_id, True)
        mock_db.get_nutrition_by_id.return_value = {
            "_id": log_obj_id,
            "user_email": user_email,
            "date": datetime.fromisoformat(payload["date"]),
            "calories": 2500,
            "protein_grams": 150.0,
            "carbs_grams": 300.0,
            "fat_grams": 70.0,
            "fiber_grams": 30.0,
            "source": "manual"
        }
        
        response = client.post("/nutrition/log", json=payload)
        assert response.status_code == 200
        assert response.json()["id"] == log_id
        
        # 2. List Nutrition Logs
        mock_db.get_nutrition_paginated.return_value = ([mock_db.get_nutrition_by_id.return_value], 1)
        
        list_response = client.get("/nutrition/list?page=1&page_size=10")
        assert list_response.status_code == 200
        assert len(list_response.json()["logs"]) == 1
        
        # 3. Delete Nutrition Log
        mock_db.delete_nutrition_log.return_value = True
        
        delete_response = client.delete(f"/nutrition/{log_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "Nutrition log deleted successfully"
        
    finally:
        app.dependency_overrides.clear()
