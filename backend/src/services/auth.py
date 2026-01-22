"""
This module contains the authentication and authorization logic for the application.
"""

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.core.deps import get_mongo_database
from src.core.config import settings
from src.core.logs import logger

# Debug JWT import
logger.info("JWT module path: %s", getattr(jwt, "__file__", "unknown"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


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

    # Check if token is blocklisted in MongoDB
    if get_mongo_database().is_token_blocklisted(token):
        logger.warning("Attempted to use a blocked token.")
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            logger.warning("Token payload missing 'sub' claim (email).")
            raise credentials_exception
        return email

    except jwt.InvalidTokenError as exception:
        logger.warning("Invalid JWT token provided: %s", exception)
        raise credentials_exception from exception


def user_logout(token: str) -> None:
    """
    Logs out a user by adding their token to the MongoDB blocklist.

    The token will be automatically removed from the blocklist when it expires,
    thanks to MongoDB's TTL index on the blocklist collection.

    Args:
        token (str): The JWT token to invalidate.
    """
    try:
        # Decode token to get expiration time
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        else:
            # Default to 2 hours from now if no exp claim
            expires_at = datetime.now(timezone.utc) + timedelta(hours=2)
    except jwt.InvalidTokenError:
        # If token is invalid, use default expiration
        expires_at = datetime.now(timezone.utc) + timedelta(hours=2)

    get_mongo_database().add_token_to_blocklist(token, expires_at)
    logger.info("Token added to MongoDB blocklist for logout.")
