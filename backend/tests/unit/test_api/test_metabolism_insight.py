import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_ai_trainer_brain
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.services.trainer import AITrainerBrain
import src.api.endpoints.metabolism as metabolism_module

# Mock Dependencies
def mock_verify_token():
    return "test@test.com"

mock_brain = MagicMock(spec=AITrainerBrain)

async def override_get_brain():
    return mock_brain

class TestMetabolismInsight:
    @pytest.fixture
    def client(self):
        """Fixture to provide a TestClient with authorized user override."""
        app.dependency_overrides[verify_token] = mock_verify_token
        app.dependency_overrides[get_ai_trainer_brain] = override_get_brain
        
        with TestClient(app) as c:
            yield c
        
        # Cleanup
        app.dependency_overrides.clear()

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Reset mocks before each test."""
        mock_brain.reset_mock()

    def test_insight_stream_success(self, client, monkeypatch):
        """
        Test that VALID stats trigger a stream from the brain.
        """
        # Mock TDEE Service to return valid stats
        mock_tdee_service = MagicMock(spec=AdaptiveTDEEService)
        mock_tdee_service.calculate_tdee.return_value = {
            "logs_count": 10,
            "tdee": 2000,
            "status": "maintenance",
        }

        # Monkeypatch the class used in the endpoint
        monkeypatch.setattr(
            metabolism_module,
            "AdaptiveTDEEService",
            MagicMock(return_value=mock_tdee_service),
        )

        # Mock Brain to return an iterator
        def stream_generator(*args, **kwargs):
            yield "Analysis Part 1"
            yield "Analysis Part 2"

        mock_brain.generate_insight_stream.side_effect = stream_generator

        response = client.get("/metabolism/insight?weeks=3")

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        assert "Analysis Part 1" in response.text
        assert "Analysis Part 2" in response.text

        mock_tdee_service.calculate_tdee.assert_called_once()
        mock_brain.generate_insight_stream.assert_called_once()

    def test_insight_insufficient_data(self, client, monkeypatch):
        """
        Test that INSUFFICIENT data returns a specific static message (streamed).
        """
        mock_tdee_service = MagicMock(spec=AdaptiveTDEEService)
        mock_tdee_service.calculate_tdee.return_value = {
            "logs_count": 1,  # Too few
            "tdee": 0,
            "confidence": "none",
        }

        monkeypatch.setattr(
            metabolism_module,
            "AdaptiveTDEEService",
            MagicMock(return_value=mock_tdee_service),
        )

        response = client.get("/metabolism/insight?weeks=3")

        assert response.status_code == 200
        assert "Dados insuficientes" in response.text

        # Verify brain was NOT called
        mock_brain.generate_insight_stream.assert_not_called()
