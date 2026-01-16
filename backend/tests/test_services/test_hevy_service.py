import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from src.services.hevy_service import HevyService
from src.api.models.workout_log import WorkoutLog

@pytest.fixture
def mock_repo():
    repo = Mock()
    repo.collection = Mock()
    return repo

@pytest.fixture
def service(mock_repo):
    return HevyService(mock_repo)

@pytest.mark.asyncio
async def test_validate_api_key_valid(service):
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.get.return_value.status_code = 200
        
        valid = await service.validate_api_key("valid_key")
        assert valid is True

@pytest.mark.asyncio
async def test_get_workout_count(service):
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"workout_count": 42}
        
        mock_client.get.return_value = response
        
        count = await service.get_workout_count("key")
        assert count == 42

def test_transform_to_workout_log(service):
    hevy_data = {
        "title": "Leg Day",
        "start_time": "2023-10-01T10:00:00Z",
        "end_time": "2023-10-01T11:00:00Z",
        "exercises": [
            {
                "title": "Squat",
                "sets": [
                    {"weight_kg": 100, "reps": 5},
                    {"weight_kg": 100, "reps": 5}
                ]
            }
        ]
    }
    
    log = service.transform_to_workout_log(hevy_data, "user@example.com")
    assert isinstance(log, WorkoutLog)
    assert log.workout_type == "Leg Day"
    assert log.duration_minutes == 60
    assert len(log.exercises) == 1
    assert log.exercises[0].name == "Squat"
    assert log.exercises[0].sets == 2
    assert log.exercises[0].weights_per_set == [100.0, 100.0]

@pytest.mark.asyncio
async def test_import_workouts_flow(service, mock_repo):
    # Mock Fetch
    service.fetch_workouts = AsyncMock(return_value=[
        {"title": "W1", "start_time": "2023-10-01T10:00:00Z", "exercises": []}
    ])
    
    # Mock Transform
    service.transform_to_workout_log = Mock(return_value=WorkoutLog(
        user_email="user@test.com",
        date=datetime.now(), 
        workout_type="Test",
        exercises=[]
    ))
    
    # Mock Repo Find (not exists)
    mock_repo.collection.find_one.return_value = None
    mock_repo.collection.find.return_value = []
    
    result = await service.import_workouts("user@test.com", "key")
    
    assert result["imported"] == 1
    mock_repo.save_log.assert_called_once()

@pytest.mark.asyncio
async def test_get_routines(service):
    from src.api.models.routine import RoutineListResponse
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "page": 1,
            "page_count": 1,
            "routines": [{"title": "R1", "exercises": []}]
        }
        mock_client.get.return_value = response
        
        routines = await service.get_routines("key")
        assert isinstance(routines, RoutineListResponse)
        assert routines.routines[0].title == "R1"

@pytest.mark.asyncio
async def test_create_routine(service):
    from src.api.models.routine import HevyRoutine
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        
        response = Mock()
        response.status_code = 201
        response.json.return_value = {"routine": {"id": "new_id", "title": "New Routine", "exercises": []}}
        mock_client.post.return_value = response
        
        routine_data = HevyRoutine(title="New Routine", exercises=[])
        result = await service.create_routine("key", routine_data)
        
        assert result.id == "new_id"
        assert result.title == "New Routine"
