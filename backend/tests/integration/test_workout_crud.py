from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from bson import ObjectId

client = TestClient(app)

def test_workout_crud_operations():
    """
    Test creating, listing and deleting workouts using direct dependency overrides.
    """
    user_email = "test@example.com"
    mock_db = MagicMock()
    
    # Overrides
    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_mongo_database] = lambda: mock_db
    
    try:
        # 1. Create Workout
        workout_obj_id = ObjectId()
        workout_id = str(workout_obj_id)
        payload = {
            "date": "2026-03-17T10:00:00",
            "workout_type": "Strength",
            "exercises": [
                {
                    "name": "Bench Press",
                    "sets": 2,
                    "reps_per_set": [10, 10],
                    "weights_per_set": [60.0, 60.0]
                }
            ],
            "duration_minutes": 45,
            "source": "manual"
        }
        
        # Mock DB response
        mock_db.save_workout_log.return_value = workout_obj_id
        mock_db.get_workout_by_id.return_value = {
            "_id": workout_obj_id,
            "user_email": user_email,
            "date": "2026-03-17T10:00:00",
            "workout_type": "Strength",
            "exercises": payload["exercises"],
            "duration_minutes": 45,
            "source": "manual"
        }
        
        response = client.post("/workout", json=payload)
        assert response.status_code == 200
        assert response.json()["id"] == workout_id
        
        # 2. List Workouts
        mock_db.get_workouts_paginated.return_value = ([mock_db.get_workout_by_id.return_value], 1)
        
        list_response = client.get("/workout/list?page=1&page_size=10")
        assert list_response.status_code == 200
        assert len(list_response.json()["workouts"]) == 1
        
        # 3. Delete Workout
        mock_db.delete_workout_log.return_value = True
        
        delete_response = client.delete(f"/workout/{workout_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "Workout deleted successfully"
        
    finally:
        app.dependency_overrides.clear()
