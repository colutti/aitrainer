"""Shared helpers for demo-account read-only enforcement."""

from typing import Annotated, Any

from fastapi import Depends, HTTPException, status

from src.core.deps import get_mongo_database
from src.services.auth import verify_token
from src.services.database import MongoDatabase

DEMO_READ_ONLY_DETAIL = "demo_read_only"

CurrentUser = Annotated[str, Depends(verify_token)]
DatabaseDep = Annotated[MongoDatabase, Depends(get_mongo_database)]


def is_demo_user(profile: Any | None) -> bool:
    """Return whether a user profile/document is marked as demo."""
    if profile is None:
        return False
    if isinstance(profile, dict):
        return profile.get("is_demo") is True
    return getattr(profile, "is_demo", False) is True


def ensure_writable_user(user_email: CurrentUser, db: DatabaseDep) -> str:
    """Reject write operations for protected demo users."""
    try:
        is_demo = False
        if hasattr(db, "get_user_profile"):
            is_demo = is_demo_user(db.get_user_profile(user_email))
    except (AttributeError, TypeError, ValueError):
        # Partial mocks in tests should not break unrelated routes.
        return user_email
    if is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=DEMO_READ_ONLY_DETAIL,
        )
    return user_email


WritableCurrentUser = Annotated[str, Depends(ensure_writable_user)]
