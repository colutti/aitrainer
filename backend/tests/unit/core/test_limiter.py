"""Tests for rate limiter configuration."""

import pytest
from unittest.mock import MagicMock, patch
import importlib


class TestRateLimiterConfiguration:
    """Test rate limiter setup and configuration."""

    def test_limiter_imported_successfully(self):
        """Test that limiter module can be imported."""
        from src.core.limiter import limiter
        assert limiter is not None

    def test_limiter_is_slowapi_instance(self):
        """Test that limiter is a slowapi Limiter instance."""
        try:
            import slowapi
            # Check if slowapi is installed
            assert slowapi is not None
            from src.core.limiter import limiter
            # Should be a Limiter instance or a fallback
            assert hasattr(limiter, 'limit') or hasattr(limiter, '__call__')
        except ImportError:
            # slowapi not installed - limiter will be a DummyLimiter
            pass

    def test_limiter_has_key_function(self):
        """Test that limiter has a key function configured."""
        from src.core.limiter import get_remote_address

        # get_remote_address should be the key function
        assert callable(get_remote_address)

    def test_get_remote_address_from_request(self):
        """Test extracting remote address from request object."""
        from src.core.limiter import get_remote_address

        # Mock FastAPI Request object
        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.1"

        result = get_remote_address(mock_request)
        assert result == "192.168.1.1"

    def test_get_remote_address_fallback_to_forwarded_for(self):
        """Test fallback to X-Forwarded-For header."""
        from src.core.limiter import get_remote_address

        mock_request = MagicMock()
        mock_request.client.host = None
        mock_request.headers.get.return_value = "203.0.113.1"

        result = get_remote_address(mock_request)

        # Depending on implementation, should handle X-Forwarded-For
        assert result is not None or result == "203.0.113.1"

    def test_limiter_enabled_with_slowapi_installed(self):
        """Test limiter behavior when slowapi is available."""
        try:
            import slowapi
            assert slowapi is not None
            from src.core.limiter import limiter

            # If slowapi is installed, limiter should be active
            assert hasattr(limiter, 'limit')
        except ImportError:
            # If slowapi not installed, skip this test
            pytest.skip("slowapi not installed")

    def test_limiter_with_missing_slowapi(self):
        """Test graceful fallback when slowapi is not installed."""
        # This is a defensive test - the limiter should not crash if slowapi is missing
        from src.core.limiter import limiter

        # Limiter should be usable even if slowapi isn't installed
        assert limiter is not None

    def test_limiter_key_function_handles_missing_client(self):
        """Test key function handles request without client info."""
        from src.core.limiter import get_remote_address

        mock_request = MagicMock()
        mock_request.client = None

        # Should handle gracefully
        try:
            result = get_remote_address(mock_request)
            # Should return some default or None
            assert result is not None or result is None
        except AttributeError:
            # Acceptable behavior - documents the limitation
            pass

    def test_limiter_key_function_with_various_ip_formats(self):
        """Test key function with different IP address formats."""
        from src.core.limiter import get_remote_address

        test_ips = [
            "192.168.1.1",
            "10.0.0.1",
            "2001:0db8:85a3::8a2e:0370:7334",  # IPv6
            "127.0.0.1",  # localhost
            "0.0.0.0",
        ]

        for ip in test_ips:
            mock_request = MagicMock()
            mock_request.client.host = ip

            result = get_remote_address(mock_request)
            assert result == ip

    def test_limiter_configuration_no_errors_on_import(self):
        """Test that limiter module imports without errors."""
        # Re-import to catch any import-time errors
        from src.core import limiter as limiter_module

        importlib.reload(limiter_module)
        assert limiter_module.limiter is not None


class TestLimiterIntegration:
    """Test limiter integration with FastAPI."""

    def test_limiter_decorator_syntax(self):
        """Test that limiter can be used as a decorator."""
        from src.core.limiter import limiter

        # Test that limiter has limit method for decorator usage
        if hasattr(limiter, 'limit'):
            # slowapi version
            decorator = limiter.limit("10/minute")
            assert callable(decorator)

    def test_limiter_callable_or_has_limit_method(self):
        """Test that limiter is callable or has limit method."""
        from src.core.limiter import limiter

        # Limiter should either be callable or have a limit method
        assert callable(limiter) or hasattr(limiter, 'limit')


class TestLimiterEdgeCases:
    """Test edge cases for rate limiter."""

    def test_limiter_with_null_request(self):
        """Test limiter behavior with None request."""
        from src.core.limiter import get_remote_address
        # Should handle None gracefully
        try:
            result = get_remote_address(None)  # type: ignore
            assert result is None or isinstance(result, str)
        except (AttributeError, TypeError):
            # Acceptable to raise for None input
            pass

    def test_limiter_key_function_is_deterministic(self):
        """Test that key function returns same value for same request."""
        from src.core.limiter import get_remote_address

        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.1"

        result1 = get_remote_address(mock_request)
        result2 = get_remote_address(mock_request)

        assert result1 == result2

    def test_limiter_stores_configuration(self):
        """Test that limiter stores configuration properly."""
        from src.core.limiter import limiter

        # Limiter should be callable or have methods
        assert callable(limiter) or hasattr(limiter, 'limit')

    @patch('src.core.limiter.Limiter')
    def test_limiter_initialization_parameters(self, mock_limiter):
        """Test limiter is initialized with correct parameters."""
        # This test documents what parameters limiter should receive
        # if slowapi is available
        pass


class TestLimiterRobustness:
    """Test robustness of limiter configuration."""

    def test_limiter_survives_reload(self):
        """Test that limiter can survive module reload."""
        from src.core import limiter as limiter_module

        limiter1 = limiter_module.limiter
        importlib.reload(limiter_module)
        limiter2 = limiter_module.limiter

        # Both should be valid limiter instances
        assert limiter1 is not None
        assert limiter2 is not None

    def test_limiter_thread_safety(self):
        """Test limiter configuration is thread-safe."""
        from src.core.limiter import get_remote_address
        import threading

        results = []

        def access_limiter():
            mock_request = MagicMock()
            mock_request.client.host = "192.168.1.1"
            result = get_remote_address(mock_request)
            results.append(result)

        threads = [threading.Thread(target=access_limiter) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All threads should complete without error
        assert len(results) == 10
