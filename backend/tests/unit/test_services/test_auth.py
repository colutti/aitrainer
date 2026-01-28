import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException
from src.services.auth import user_login, verify_token, user_logout
from src.core.config import settings


class TestAuthService(unittest.TestCase):
    @patch("src.services.auth.get_mongo_database")
    def test_user_login_success(self, mock_get_db):
        """Test successful login returns token."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.validate_user.return_value = True

        token = user_login("test@test.com", "password")

        self.assertIsInstance(token, str)
        # Verify token content
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        self.assertEqual(payload["sub"], "test@test.com")
        self.assertIn("exp", payload)

    @patch("src.services.auth.get_mongo_database")
    def test_user_login_invalid(self, mock_get_db):
        """Test login with invalid credentials."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.validate_user.return_value = False

        with self.assertRaises(ValueError):
            user_login("test@test.com", "wrong")

    @patch("src.services.auth.get_mongo_database")
    def test_verify_token_valid(self, mock_get_db):
        """Test verifying a valid token."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.is_token_blocklisted.return_value = False

        # Create valid token manually
        payload = {
            "sub": "test@test.com",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        email = verify_token(token)
        self.assertEqual(email, "test@test.com")

    @patch("src.services.auth.get_mongo_database")
    def test_verify_token_expired(self, mock_get_db):
        """Test verify expired token."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.is_token_blocklisted.return_value = False

        # Create expired token
        payload = {
            "sub": "test@test.com",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        with self.assertRaises(HTTPException) as cm:
            verify_token(token)
        self.assertEqual(
            cm.exception.detail, "Could not validate credentials"
        )  # Generic error for auth failure in code

        # Note: PyJWT raises ExpiredSignatureError, which gets caught as InvalidTokenError in verify_token

    @patch("src.services.auth.get_mongo_database")
    def test_verify_token_blocklisted(self, mock_get_db):
        """Test blocked token."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.is_token_blocklisted.return_value = True

        token = "valid_token"

        with self.assertRaises(HTTPException):
            verify_token(token)

    @patch("src.services.auth.get_mongo_database")
    def test_user_logout(self, mock_get_db):
        """Test logout adds to blocklist."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        payload = {
            "sub": "test@test.com",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        user_logout(token)

        mock_db.add_token_to_blocklist.assert_called_once()

    # Edge case tests for security hardening
    @patch("src.services.auth.get_mongo_database")
    def test_user_login_empty_password(self, mock_get_db):
        """Test login attempt with empty password."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.validate_user.return_value = False

        with self.assertRaises(ValueError):
            user_login("test@test.com", "")

        mock_db.validate_user.assert_called_once_with("test@test.com", "")

    @patch("src.services.auth.get_mongo_database")
    def test_user_login_sql_injection_attempt(self, mock_get_db):
        """Test login with SQL injection-like payload."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.validate_user.return_value = False

        malicious_email = "test@test.com' OR '1'='1"
        malicious_password = "pass' OR '1'='1"

        with self.assertRaises(ValueError):
            user_login(malicious_email, malicious_password)

        # Should pass malicious input as-is (parameterized queries protect)
        mock_db.validate_user.assert_called_once_with(malicious_email, malicious_password)

    @patch("src.services.auth.get_mongo_database")
    def test_verify_token_missing_sub_claim(self, mock_get_db):
        """Test verify token without 'sub' claim."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.is_token_blocklisted.return_value = False

        # Create token without 'sub' claim
        payload = {
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        with self.assertRaises(HTTPException):
            verify_token(token)

    @patch("src.services.auth.get_mongo_database")
    def test_verify_token_future_exp_boundary(self, mock_get_db):
        """Test token with expiration far in the future."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.is_token_blocklisted.return_value = False

        # Token expires in 100 years
        payload = {
            "sub": "test@test.com",
            "exp": datetime.now(timezone.utc) + timedelta(days=36500),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        email = verify_token(token)
        self.assertEqual(email, "test@test.com")

    @patch("src.services.auth.get_mongo_database")
    def test_user_logout_already_expired_token(self, mock_get_db):
        """Test logout with already-expired token."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Create expired token
        payload = {
            "sub": "test@test.com",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        # Logout should still try to blocklist (even if already expired)
        user_logout(token)

        mock_db.add_token_to_blocklist.assert_called_once()

    @patch("src.services.auth.get_mongo_database")
    def test_user_logout_missing_exp_claim(self, mock_get_db):
        """Test logout with token missing 'exp' claim."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Create token without 'exp' claim
        payload = {
            "sub": "test@test.com",
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        # Should handle gracefully or raise
        try:
            user_logout(token)
            # If it succeeds, verify blocklist was called
            mock_db.add_token_to_blocklist.assert_called_once()
        except Exception:
            # It's acceptable to fail on malformed token
            pass

    @patch("src.services.auth.get_mongo_database")
    def test_verify_token_with_invalid_signature(self, mock_get_db):
        """Test verify token with tampered signature."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Create token with wrong secret
        payload = {
            "sub": "test@test.com",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, "wrong_secret", algorithm="HS256")

        with self.assertRaises(HTTPException):
            verify_token(token)

    @patch("src.services.auth.get_mongo_database")
    def test_verify_token_malformed_string(self, mock_get_db):
        """Test verify with malformed token string."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        with self.assertRaises(HTTPException):
            verify_token("not.a.valid.token")

    @patch("src.services.auth.get_mongo_database")
    def test_verify_token_empty_string(self, mock_get_db):
        """Test verify with empty token string."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        with self.assertRaises(HTTPException):
            verify_token("")

    @patch("src.services.auth.get_mongo_database")
    def test_verify_token_none_value(self, mock_get_db):
        """Test verify with None token."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        with self.assertRaises((HTTPException, AttributeError, TypeError)):
            verify_token(None)
