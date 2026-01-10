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
        payload = {"sub": "test@test.com", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
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
        payload = {"sub": "test@test.com", "exp": datetime.now(timezone.utc) - timedelta(minutes=5)}
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        
        with self.assertRaises(HTTPException) as cm:
            verify_token(token)
        self.assertEqual(cm.exception.detail, "Could not validate credentials") # Generic error for auth failure in code
        
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
        
        payload = {"sub": "test@test.com", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        
        user_logout(token)
        
        mock_db.add_token_to_blocklist.assert_called_once()
