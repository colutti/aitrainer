"""
This module contains the models for authentication requests.
"""

from pydantic import BaseModel


class FirebaseLoginRequest(BaseModel):
    """
    Data class for Firebase login requests.
    """

    token: str


# For backward compatibility during migration if needed, but we'll aim to replace it
class LoginRequest(FirebaseLoginRequest):
    """Legacy alias for LoginRequest, now using token."""
