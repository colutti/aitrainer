"""
Rate limiter configuration for the API.
"""
from typing import Any

limiter: Any

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address

    limiter = Limiter(key_func=get_remote_address)
    RATE_LIMITING_ENABLED = True
except ImportError:
    # slowapi not installed - create a dummy limiter
    limiter = None
    RATE_LIMITING_ENABLED = False
