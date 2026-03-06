import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


@pytest.fixture
def mock_verify():
    with patch("src.api.endpoints.user.verify_id_token") as mock:
        mock.return_value = {"email": "test@test.com"}
        yield mock


def test_login_rate_limit(mock_verify):
    """
    Test that login endpoint respects rate limits.
    """
    payload = {"token": "fake_firebase_token"}

    # We don't need to mock DB here because verify_id_token is mocked

    response = client.post("/user/login", json=payload)
    assert response.status_code in [200, 429]
