"""
This module contains the API endpoints for user management.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.services.auth import user_login, user_logout, oauth2_scheme, verify_token
from src.core.deps import get_ai_trainer_brain
from src.core.logs import logger
from src.core.config import settings
from src.core.limiter import limiter, RATE_LIMITING_ENABLED
from src.api.models.auth import LoginRequest
from src.api.models.user_profile import UserProfile, UserProfileInput
from src.services.trainer import AITrainerBrain

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
AITrainerBrainDep = Annotated[AITrainerBrain, Depends(get_ai_trainer_brain)]


# Conditional rate limit decorator
def rate_limit_login(func):
    """Decorator to apply rate limiting only if enabled in settings."""
    if RATE_LIMITING_ENABLED and limiter:
        return limiter.limit(settings.RATE_LIMIT_LOGIN)(func)
    return func


@router.post("/login")
@rate_limit_login
def login(request: Request, data: LoginRequest) -> dict:  # pylint: disable=unused-argument
    """
    Authenticates a user with the provided email and password.
    """
    try:
        token = user_login(data.email, data.password)
        logger.info("User logged in successfully: %s", data.email)
        return {"token": token}
    except ValueError as exc:
        logger.info("Failed login attempt for email: %s", data.email)
        raise HTTPException(status_code=401, detail="Invalid credentials") from exc


@router.get("/profile")
def get_profile(user_email: CurrentUser, brain: AITrainerBrainDep) -> UserProfile:
    """
    Retrieve the profile information for the authenticated user.
    """
    user_profile = brain.get_user_profile(user_email)
    if not user_profile:
        logger.warning(
            "Attempted to retrieve non-existent user profile for email: %s", user_email
        )
        raise HTTPException(status_code=404, detail="User profile not found")
    return user_profile


@router.get("/me")
def get_current_user(user_email: CurrentUser, brain: AITrainerBrainDep) -> dict:
    """
    Returns basic information about the currently authenticated user.
    """
    user_profile = brain.get_user_profile(user_email)
    if not user_profile:
        raise HTTPException(status_code=404, detail="User not found")

    return {"email": user_profile.email, "role": user_profile.role}


@router.post("/update_profile")
def update_profile(
    profile_data: UserProfileInput, user_email: CurrentUser, brain: AITrainerBrainDep
) -> JSONResponse:
    """
    Updates the user profile with the provided information.
    """
    # Fetch existing profile first to preserve system fields (Hevy, etc.)
    existing_profile = brain.get_user_profile(user_email)

    if existing_profile:
        # Update existing profile with new data
        update_data = profile_data.model_dump(exclude_unset=True)
        updated_profile = existing_profile.model_copy(update=update_data)
        brain.save_user_profile(updated_profile)
    else:
        # Fallback: Create new profile if weirdly not found
        logger.warning(
            "Creating new profile during update for %s (unexpected)", user_email
        )
        profile = UserProfile(**profile_data.model_dump(), email=user_email)
        brain.save_user_profile(profile)

    logger.info("User profile updated for email: %s", user_email)
    return JSONResponse(content={"message": "Profile updated successfully"})


class TelegramNotificationSettings(BaseModel):
    """Telegram notification configuration settings."""

    telegram_notify_on_workout: bool | None = None
    telegram_notify_on_nutrition: bool | None = None
    telegram_notify_on_weight: bool | None = None


@router.post("/telegram-notifications")
def update_telegram_notifications(
    settings_data: TelegramNotificationSettings,
    user_email: CurrentUser,
    brain: AITrainerBrainDep,
) -> JSONResponse:
    """
    Updates the user's Telegram notification preferences.
    """
    existing_profile = brain.get_user_profile(user_email)

    if not existing_profile:
        logger.warning(
            "Attempted to update notifications for non-existent user: %s", user_email
        )
        raise HTTPException(status_code=404, detail="User profile not found")

    # Update only the fields that were provided (not None)
    update_data = settings_data.model_dump(exclude_unset=True)
    updated_profile = existing_profile.model_copy(update=update_data)
    brain.save_user_profile(updated_profile)

    logger.info("Telegram notification settings updated for user: %s", user_email)
    return JSONResponse(
        content={"message": "Notification settings updated successfully"}
    )


@router.post("/logout")
def logout(
    user_email: CurrentUser, token: str = Depends(oauth2_scheme)
) -> JSONResponse:
    """
    Logs out the current user by calling the user_logout function.
    """
    user_logout(token)
    logger.info("User logged out: %s", user_email)
    return JSONResponse(content={"message": "Logged out successfully"})
