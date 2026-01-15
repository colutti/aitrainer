
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.endpoints import metabolism  # noqa: E402
from src.services.auth import verify_token
from src.core.deps import get_ai_trainer_brain
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.core.deps import get_mongo_database
from src.services.trainer import AITrainerBrain

# Mock Dependencies
def mock_verify_token():
    return "test@test.com"

mock_brain = MagicMock(spec=AITrainerBrain)

async def override_get_brain():
    return mock_brain

# Setup App Overrides
app.dependency_overrides[verify_token] = mock_verify_token
app.dependency_overrides[get_ai_trainer_brain] = override_get_brain

client = TestClient(app)

class TestMetabolismInsight:
    
    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        # Reset mock before each test
        mock_brain.reset_mock()
        
    def test_insight_stream_success(self, monkeypatch):
        """
        Test that VALID stats trigger a stream from the brain.
        """
        # Mock TDEE Service to return valid stats
        # We need to patch where it is instantiated in the endpoint
        mock_tdee_service = MagicMock(spec=AdaptiveTDEEService)
        mock_tdee_service.calculate_tdee.return_value = {
            "logs_count": 10,
            "tdee": 2000,
            "status": "maintenance"
        }
        
        # Monkeypatch the class used in the endpoint
        import src.api.endpoints.metabolism as metabolism_module
        monkeypatch.setattr(metabolism_module, "AdaptiveTDEEService", MagicMock(return_value=mock_tdee_service))
        
        # Mock Brain to return an iterator
        def stream_generator(email, stats):
            yield "Analysis Part 1"
            yield "Analysis Part 2"
            
        mock_brain.generate_insight_stream.side_effect = stream_generator
        
        response = client.get("/metabolism/insight?lookback_weeks=3")
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        assert "Analysis Part 1" in response.text
        assert "Analysis Part 2" in response.text
        
        mock_tdee_service.calculate_tdee.assert_called_once()
        mock_brain.generate_insight_stream.assert_called_once()
        
    def test_insight_insufficient_data(self, monkeypatch):
        """
        Test that INSUFFICIENT data returns a specific static message (streamed).
        """
        mock_tdee_service = MagicMock(spec=AdaptiveTDEEService)
        mock_tdee_service.calculate_tdee.return_value = {
            "logs_count": 1, # Too few
            "tdee": 0,
            "confidence": "none"
        }
        
        import src.api.endpoints.metabolism as metabolism_module
        monkeypatch.setattr(metabolism_module, "AdaptiveTDEEService", MagicMock(return_value=mock_tdee_service))
        
        response = client.get("/metabolism/insight?lookback_weeks=3")
        
        assert response.status_code == 200
        assert "Dados insuficientes" in response.text
        
        # Verify brain was NOT called
        mock_brain.generate_insight_stream.assert_not_called()
