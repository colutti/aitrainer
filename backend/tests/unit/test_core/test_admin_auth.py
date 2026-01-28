"""Tests for admin authentication and authorization."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from src.core.auth import verify_admin, AdminUser


@pytest.fixture
def mock_db():
    """Create mock MongoDB database."""
    db_mock = MagicMock()
    db_mock.users = MagicMock()
    return db_mock


@pytest.fixture
def admin_user():
    """Create mock admin user."""
    user = MagicMock()
    user.role = "admin"
    user.email = "admin@test.com"
    return user


@pytest.fixture
def regular_user():
    """Create mock regular user."""
    user = MagicMock()
    user.role = "user"
    user.email = "user@test.com"
    return user


class TestVerifyAdmin:
    """Test admin verification function."""

    def test_verify_admin_success(self, mock_db, admin_user):
        """Test successful admin verification."""
        mock_db.users.get_profile.return_value = admin_user

        result = verify_admin("admin@test.com", mock_db)

        assert result == "admin@test.com"
        mock_db.users.get_profile.assert_called_once_with("admin@test.com")

    def test_verify_admin_non_admin_user_returns_403(self, mock_db, regular_user):
        """Test non-admin user returns 403 Forbidden."""
        mock_db.users.get_profile.return_value = regular_user

        with pytest.raises(HTTPException) as exc_info:
            verify_admin("user@test.com", mock_db)

        assert exc_info.value.status_code == 403
        assert "Admin access required" in exc_info.value.detail

    def test_verify_admin_user_not_found_returns_404(self, mock_db):
        """Test non-existent user returns 404 Not Found."""
        mock_db.users.get_profile.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            verify_admin("nonexistent@test.com", mock_db)

        assert exc_info.value.status_code == 404
        assert "User not found" in exc_info.value.detail

    def test_verify_admin_user_missing_role_field(self, mock_db):
        """Test user without role field raises AttributeError gracefully."""
        user_without_role = MagicMock(spec=[])  # No role attribute
        mock_db.users.get_profile.return_value = user_without_role

        # Should raise AttributeError when accessing role
        with pytest.raises(AttributeError):
            verify_admin("user@test.com", mock_db)

    def test_verify_admin_with_expired_token_handled_by_verify_token(self, mock_db):
        """Test that expired tokens are handled by verify_token dependency."""
        # This test documents that verify_admin depends on verify_token
        # verify_token should raise HTTPException with 401 before reaching verify_admin
        mock_db.users.get_profile.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            verify_admin("user@test.com", mock_db)

        # verify_admin handles missing user (doesn't get expired token case)
        assert exc_info.value.status_code == 404

    def test_verify_admin_db_connection_error(self, mock_db):
        """Test database connection error handling."""
        mock_db.users.get_profile.side_effect = Exception("MongoDB connection failed")

        with pytest.raises(Exception) as exc_info:
            verify_admin("admin@test.com", mock_db)

        assert "MongoDB connection failed" in str(exc_info.value)

    def test_verify_admin_empty_email_string(self, mock_db):
        """Test with empty email string."""
        mock_db.users.get_profile.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            verify_admin("", mock_db)

        assert exc_info.value.status_code == 404

    def test_admin_user_type_alias_exists(self):
        """Test that AdminUser type alias is properly defined."""
        # AdminUser should be Annotated[str, Depends(verify_admin)]
        assert AdminUser is not None
        # Type alias validation - just ensure it's importable
        from src.core.auth import AdminUser as TestAdminUser
        assert TestAdminUser is not None


class TestAdminAuthIntegration:
    """Integration tests for admin authentication flow."""

    def test_verify_admin_multiple_calls_different_users(self, mock_db, admin_user, regular_user):
        """Test verify_admin with multiple different users."""
        # First call - admin
        mock_db.users.get_profile.return_value = admin_user
        result1 = verify_admin("admin@test.com", mock_db)
        assert result1 == "admin@test.com"

        # Second call - regular user
        mock_db.users.get_profile.return_value = regular_user
        with pytest.raises(HTTPException) as exc_info:
            verify_admin("user@test.com", mock_db)
        assert exc_info.value.status_code == 403

    def test_verify_admin_case_sensitive_role_check(self, mock_db):
        """Test that role check is case-sensitive."""
        user_with_wrong_role_case = MagicMock(role="Admin")  # Capital A
        mock_db.users.get_profile.return_value = user_with_wrong_role_case

        with pytest.raises(HTTPException) as exc_info:
            verify_admin("user@test.com", mock_db)

        assert exc_info.value.status_code == 403

    def test_verify_admin_special_email_formats(self, mock_db, admin_user):
        """Test verify_admin with various email formats."""
        special_emails = [
            "admin+test@test.com",
            "admin.name@test.co.uk",
            "123@test.com",
        ]

        for email in special_emails:
            mock_db.users.get_profile.return_value = admin_user
            result = verify_admin(email, mock_db)
            assert result == email
            mock_db.users.get_profile.assert_called_with(email)
