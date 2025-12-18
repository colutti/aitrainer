"""
This module contains the authentication and authorization logic for the application.
"""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from src.core.deps import get_mongo_database
from src.core.config import settings

from src.core.logs import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
blocklist = set()


def user_login(email: str, password: str) -> str:
    """
    Authenticates a user and generates a JWT token upon successful login.

    Args:
        email (str): The user's email address.
        password (str): The user's password.

    Returns:
        str: A JWT token valid for 2 hours.

    Raises:
        ValueError: If the provided credentials are invalid.
    """
    if not get_mongo_database().validate_user(email, password):
        raise ValueError("Invalid credentials")
    payload = {"sub": email, "exp": datetime.now(timezone.utc) + timedelta(hours=2)}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token


def verify_token(token: str = Depends(oauth2_scheme)) -> str:
    """
    Verifies a JWT token and extracts the user's email.

    Args:
        token (str): The JWT token to verify, provided via dependency injection.

    Returns:
        str: The email address extracted from the token's payload.

    Raises:
        HTTPException: If the token is invalid or the email is not found in the payload.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token in blocklist:
        logger.warning("Attempted to use a blocked token: %s", token)
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            logger.warning("Token payload missing 'sub' claim (email).")
            raise credentials_exception
        return email

    except InvalidTokenError as exception:
        logger.warning("Invalid JWT token provided: %s", exception)
        raise credentials_exception from exception


def user_logout(token: str):
    """
    Handles user logout. This is a placeholder for logout functionality.

    Since JWT tokens are stateless, logout can be handled on the client side by deleting the token.

    Returns:
        None
    """
    logger.info("Token added to blocklist for logout.")
    blocklist.add(token)
