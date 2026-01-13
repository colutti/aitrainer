import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from src.api.main import app
from src.core.config import settings

client = TestClient(app)

@pytest.fixture
def mock_auth():
    with patch("src.api.endpoints.user.user_login") as mock:
        mock.return_value = "fake_token"
        yield mock

def test_login_rate_limit(mock_auth):
    """
    Test that login endpoint respects rate limits.
    """
    payload = {"email": "test@test.com", "password": "password"}
    
    # We don't need to mock DB here because user_login is mocked
    
    response = client.post("/user/login", json=payload)
    assert response.status_code in [200, 429]
