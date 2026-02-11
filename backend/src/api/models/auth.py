"""
This module contains the models for authentication requests.
"""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """
    Represents a login request containing user credentials.

    Attributes:
        email (str): The user's email address.
        password (str): The user's password.
    """

    email: str
    password: str
