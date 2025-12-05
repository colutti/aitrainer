from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from backend.database import validate_user

from .config import SECRET_KEY

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
    if not validate_user(email, password):
        raise ValueError("Invalid credentials")
    payload = {"sub": email, "exp": datetime.now(timezone.utc) + timedelta(hours=2)}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
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

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        return email

    except InvalidTokenError as exception:
        raise credentials_exception from exception


def user_logout():
    """
    Handles user logout. This is a placeholder for logout functionality.

    Since JWT tokens are stateless, logout can be handled on the client side by deleting the token.

    Returns:
        None
    """
    # No server-side action needed for JWT logout
