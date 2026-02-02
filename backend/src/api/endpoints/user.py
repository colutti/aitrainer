"""
This module contains the API endpoints for user management.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from src.services.auth import user_login, user_logout, oauth2_scheme, verify_token
from src.core.deps import get_ai_trainer_brain
from src.core.logs import logger
from src.core.config import settings
from src.core.limiter import limiter, RATE_LIMITING_ENABLED
from src.api.models.auth import LoginRequest
from src.api.models.user_profile import UserProfile, UserProfileInput
from src.services.trainer import AITrainerBrain
from pydantic import BaseModel

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
AITrainerBrainDep = Annotated[AITrainerBrain, Depends(get_ai_trainer_brain)]


# Conditional rate limit decorator
def rate_limit_login(func):
    if RATE_LIMITING_ENABLED and limiter:
        return limiter.limit(settings.RATE_LIMIT_LOGIN)(func)
    return func


@router.post("/login")
@rate_limit_login
def login(request: Request, data: LoginRequest) -> dict:
    """
    Authenticates a user with the provided email and password.

    Args:
        request (Request): FastAPI request object (required for rate limiting).
        data (LoginRequest): The login request body containing email and password.

    Returns:
        dict: A dictionary containing the authentication token upon successful login.
            - If authentication fails, raises HTTPException (401 Unauthorized).
            - If authentication succeeds, returns {"token": <JWT token>}.

    Logs:
        - Logs failed login attempts and successful logins.
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

    Args:
        user_email (str): The authenticated user's email.
        brain (AITrainerBrain): The AI trainer brain dependency.

    Returns:
        UserProfile: The user's profile data.

    Raises:
        HTTPException: If the user profile is not found (404).
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
    Used by frontend to determine user role (admin or user).

    Args:
        user_email (str): The authenticated user's email.
        brain (AITrainerBrain): The AI trainer brain dependency.

    Returns:
        dict: User info containing email and role.

    Raises:
        HTTPException: If the user profile is not found (404).
    """
    user_profile = brain.get_user_profile(user_email)
    if not user_profile:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "email": user_profile.email,
        "role": user_profile.role
    }


@router.post("/update_profile")
def update_profile(
    profile_data: UserProfileInput, user_email: CurrentUser, brain: AITrainerBrainDep
) -> JSONResponse:
    """
    Updates the user profile with the provided information,
    ensuring the update is associated with the authenticated user.

    Args:
        profile_data (UserProfileInput): The user profile data to update.
        user_email (str): The authenticated user's email, injected by dependency.

    Returns:
        JSONResponse: A response indicating the profile was updated successfully.
    """
    # Fetch existing profile first to preserve system fields (Hevy, etc.)
    existing_profile = brain.get_user_profile(user_email)

    if existing_profile:
        # Update existing profile with new data
        # model_dump(exclude_unset=True) ensures we only update fields provided in request
        update_data = profile_data.model_dump(exclude_unset=True)
        updated_profile = existing_profile.model_copy(update=update_data)
        brain.save_user_profile(updated_profile)
    else:
        # Fallback: Create new profile if weirdly not found (shouldn't happen for auth user)
        # Note: This will use defaults for system fields
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

    Args:
        settings_data: The notification settings to update.
        user_email: The authenticated user's email.
        brain: The AI trainer brain dependency.

    Returns:
        JSONResponse: A response indicating the settings were updated successfully.

    Raises:
        HTTPException: If the user profile is not found (404).
    """
    existing_profile = brain.get_user_profile(user_email)

    if not existing_profile:
        logger.warning("Attempted to update notifications for non-existent user: %s", user_email)
        raise HTTPException(status_code=404, detail="User profile not found")

    # Update only the fields that were provided (not None)
    update_data = settings_data.model_dump(exclude_unset=True)
    updated_profile = existing_profile.model_copy(update=update_data)
    brain.save_user_profile(updated_profile)

    logger.info("Telegram notification settings updated for user: %s", user_email)
    return JSONResponse(content={"message": "Notification settings updated successfully"})


@router.post("/logout")
def logout(
    user_email: CurrentUser, token: str = Depends(oauth2_scheme)
) -> JSONResponse:
    """
    Logs out the current user by calling the user_logout function
    and returns a JSON response indicating success.

    Returns:
        JSONResponse: A response object with a message confirming successful logout.
    """
    user_logout(token)
    logger.info("User logged out: %s", user_email)
    return JSONResponse(content={"message": "Logged out successfully"})
