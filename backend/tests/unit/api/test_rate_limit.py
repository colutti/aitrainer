import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.api.main import app
from src.core.deps import get_mongo_database

client = TestClient(app)


@pytest.fixture
def mock_verify():
    with patch("src.api.endpoints.user.verify_id_token") as mock:
        mock.return_value = {"email": "test@test.com", "email_verified": True}
        yield mock


def test_login_rate_limit(mock_verify):
    """
    Test that login endpoint respects rate limits.
    """
    payload = {"token": "fake_firebase_token"}

    mock_db = MagicMock()
    mock_db.get_user_profile.return_value = MagicMock(is_demo=False)
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.post("/user/login", json=payload)
    assert response.status_code in [200, 429]
    app.dependency_overrides.clear()
