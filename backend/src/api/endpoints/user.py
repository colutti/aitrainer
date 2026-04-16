"""
This module contains the API endpoints for user management.
"""

import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydantic_core import ValidationError

from src.api.models.auth import FirebaseLoginRequest
from src.api.models.user_profile import UserProfile, UserProfileInput
from src.core.config import settings
from src.core.deps import get_mongo_database
from src.core.demo_access import WritableCurrentUser
from src.core.firebase import ensure_firebase_initialized
from src.core.limiter import limiter, RATE_LIMITING_ENABLED
from src.core.logs import logger
from src.services.auth import user_logout, oauth2_scheme, verify_token, create_token
from src.services.database import MongoDatabase

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
DatabaseDep = Annotated[MongoDatabase, Depends(get_mongo_database)]


# Conditional rate limit decorator
def rate_limit_login(func):
    """Decorator to apply rate limiting only if enabled in settings."""
    if RATE_LIMITING_ENABLED and limiter:
        return limiter.limit(settings.RATE_LIMIT_LOGIN)(func)
    return func


def verify_id_token(token: str) -> dict:
    """
    Verifies the Firebase ID token and returns the decoded payload.
    Separated for easier testing.
    Includes a retry mechanism for 'Token used too early' (clock skew).
    """
    import firebase_admin.auth  # type: ignore # pylint: disable=import-outside-toplevel

    ensure_firebase_initialized()

    try:
        return firebase_admin.auth.verify_id_token(token)
    except ValueError as e:
        if "Token used too early" in str(e):
            logger.info("Token used too early (clock skew). Retrying in 3s...")
            time.sleep(3.1)
            return firebase_admin.auth.verify_id_token(token)
        raise e


def are_new_user_signups_enabled() -> bool:
    """Return whether public signups and new-user creation are enabled."""
    return settings.ENABLE_NEW_USER_SIGNUPS


def is_e2e_test_auth_enabled() -> bool:
    """Return whether E2E auth bootstrap endpoint is enabled."""
    return settings.ENABLE_E2E_TEST_AUTH


@router.post("/login")
@rate_limit_login
def login(
    request: Request,  # pylint: disable=unused-argument
    data: FirebaseLoginRequest,
    db: DatabaseDep,
) -> dict:
    """
    Authenticates a user with a Firebase ID token.
    This replaces both conventional and social login.
    """
    try:
        # Verify the Firebase ID token
        decoded_token = verify_id_token(data.token)
        email = decoded_token.get("email")

        if not email:
            raise HTTPException(
                status_code=400, detail="Token does not contain an email"
            )
        if not decoded_token.get("email_verified", False):
            raise HTTPException(
                status_code=403,
                detail="Please verify your email before logging in",
            )

        display_name = decoded_token.get("name", "")
        photo_base64 = decoded_token.get("picture", "")

        # Check if user already exists
        existing_profile = db.get_user_profile(email)

        if existing_profile:
            # Update missing identity fields
            updates = {}
            if not existing_profile.display_name and display_name:
                updates["display_name"] = display_name
            if not existing_profile.photo_base64 and photo_base64:
                updates["photo_base64"] = photo_base64

            if updates:
                db.update_user_profile_fields(email, updates)

            logger.info("User logged in (existing): %s", email)
        else:
            if not are_new_user_signups_enabled():
                logger.info(
                    "Blocked new user creation while signups are disabled: %s", email
                )
                raise HTTPException(status_code=403, detail="new_signups_disabled")

            # Create a new user with default free plan settings
            user_profile = UserProfile(
                email=email,
                role="user",
                gender="Masculino",
                age=30,
                weight=70.0,
                height=170,
                goal_type="maintain",
                subscription_plan="Free",
                display_name=display_name,
                photo_base64=photo_base64,
                onboarding_completed=False,
            )
            db.save_user_profile(user_profile)
            logger.info("New user created via login: %s", email)

            logger.info("User logged in (newly created): %s", email)

        # Return standard JWT token
        token = create_token(email)
        return {"token": token}

    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-exception-caught
        if exc.__class__.__name__ == "InvalidIdTokenError" or isinstance(exc, ValueError):
            logger.warning("Invalid Firebase authentication provided: %s", exc)
            raise HTTPException(status_code=401, detail="Invalid token") from exc
        logger.error("Error during login: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/public-config")
def public_config() -> dict:
    """Return public feature toggles needed by unauthenticated frontend flows."""
    return {"enable_new_user_signups": are_new_user_signups_enabled()}


@router.post("/social-login")
@rate_limit_login
def social_login(
    request: Request, data: FirebaseLoginRequest, db: DatabaseDep
) -> dict:
    """Legacy alias for /login using tokens."""
    return login(request, data, db)


@router.get("/profile")
def get_profile(user_email: CurrentUser, db: DatabaseDep) -> UserProfile:
    """
    Retrieve the profile information for the authenticated user.
    """
    user_profile = db.get_user_profile(user_email)
    if not user_profile:
        logger.warning(
            "Attempted to retrieve non-existent user profile for email: %s", user_email
        )
        raise HTTPException(status_code=404, detail="User profile not found")
    return user_profile


@router.get("/me")
def get_current_user(user_email: CurrentUser, db: DatabaseDep) -> dict:
    """
    Returns basic information about the currently authenticated user.
    """
    user_profile = db.get_user_profile(user_email)
    if not user_profile:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "email": user_profile.email,
        "role": user_profile.role,
        "name": user_profile.display_name,
        "photo_base64": user_profile.photo_base64,
        "onboarding_completed": getattr(user_profile, "onboarding_completed", True),
        "subscription_plan": user_profile.subscription_plan,
        "is_demo": user_profile.is_demo,
        "custom_message_limit": user_profile.custom_message_limit,
        "custom_trial_days": user_profile.custom_trial_days,
        "messages_sent_today": user_profile.messages_sent_today,
        "trial_remaining_days": user_profile.trial_remaining_days,
        "current_daily_limit": user_profile.current_daily_limit,
        "current_plan_limit": user_profile.current_plan_limit,
        "effective_remaining_messages": user_profile.effective_remaining_messages,
        "has_stripe_customer": bool(user_profile.stripe_customer_id),
    }


@router.post("/update_profile")
def update_profile(
    profile_data: UserProfileInput,
    user_email: WritableCurrentUser,
    db: DatabaseDep,
) -> JSONResponse:
    """
    Updates the user profile with the provided information.
    """
    try:
        # Fetch existing profile first to preserve system fields (Hevy, etc.)
        existing_profile = db.get_user_profile(user_email)

        if existing_profile:
            # Update existing profile with new data
            update_data = profile_data.model_dump(exclude_unset=True)
            g_old = existing_profile.goal_type
            w_old = existing_profile.weekly_rate
            goal_changed = (
                "goal_type" in update_data and update_data["goal_type"] != g_old
            ) or ("weekly_rate" in update_data and update_data["weekly_rate"] != w_old)
            updated_profile = existing_profile.model_copy(update=update_data)
            logger.info(
                "Saving user profile for %s. Onboarding completed: %s",
                user_email,
                updated_profile.onboarding_completed,
            )
            db.save_user_profile(updated_profile)
            if goal_changed:
                db.update_user_profile_fields(
                    user_email,
                    {"tdee_last_check_in": None, "tdee_last_target": None},
                )
        else:
            # Fallback: Create new profile if weirdly not found
            logger.warning(
                "Creating new profile during update for %s (unexpected)", user_email
            )
            profile = UserProfile(
                **profile_data.model_dump(exclude_unset=True), email=user_email
            )
            db.save_user_profile(profile)

        logger.info("User profile updated for email: %s", user_email)
        return JSONResponse(content={"message": "Profile updated successfully"})
    except ValueError as e:
        logger.error("Validation error in update_profile: %s", str(e))
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        logger.error("Error in update_profile: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e


class UpdateIdentityRequest(BaseModel):
    """User identity update (display name and profile photo)."""

    display_name: str | None = None
    photo_base64: str | None = None


class E2ETestLoginRequest(BaseModel):
    """Request model for containerized E2E login bootstrap."""

    email: str = "bot-real@fityq.it"
    display_name: str = "Real QA Bot"
    onboarding_completed: bool = True
    is_demo: bool = False


@router.post("/update_identity")
def update_identity(
    data: UpdateIdentityRequest,
    user_email: WritableCurrentUser,
    db: DatabaseDep,
) -> JSONResponse:
    """
    Updates the user's display name and/or profile photo.

    Uses a targeted partial update ($set on identity fields only) to avoid race
    conditions with concurrent update_profile calls. Previously used full
    read-modify-write which could overwrite concurrent changes to goal_type,
    weekly_rate, etc. when both endpoints were called in parallel.
    """
    existing_profile = db.get_user_profile(user_email)

    if not existing_profile:
        logger.warning(
            "Attempted to update identity for non-existent user: %s", user_email
        )
        raise HTTPException(status_code=404, detail="User profile not found")

    # Use targeted partial update to avoid overwriting concurrent profile changes.
    # Only touch identity fields (display_name, photo_base64) — never profile fields.
    update_data = data.model_dump(exclude_unset=True)
    if update_data:
        db.update_user_profile_fields(user_email, update_data)

    logger.info("User identity updated for email: %s", user_email)
    return JSONResponse(content={"message": "Identity updated successfully"})


@router.post("/e2e-login")
def e2e_login(data: E2ETestLoginRequest, db: DatabaseDep) -> dict:
    """
    Creates or refreshes a deterministic E2E user and returns a platform JWT.
    Enabled only in the containerized test environment.
    """
    if not is_e2e_test_auth_enabled():
        raise HTTPException(status_code=404, detail="Not found")

    existing_profile = None
    try:
        existing_profile = db.get_user_profile(data.email)
    except ValidationError as exc:
        logger.warning(
            "Recovered malformed E2E profile for %s: %s", data.email, exc
        )

    if existing_profile:
        existing_profile.display_name = data.display_name
        existing_profile.subscription_plan = "Free"
        existing_profile.onboarding_completed = data.onboarding_completed
        existing_profile.is_demo = data.is_demo
        db.save_user_profile(existing_profile)
    else:
        profile = UserProfile(
            email=data.email,
            role="user",
            gender="Masculino",
            age=30,
            weight=80.0,
            height=180,
            goal_type="maintain",
            subscription_plan="Free",
            display_name=data.display_name,
            onboarding_completed=data.onboarding_completed,
            is_demo=data.is_demo,
        )
        db.save_user_profile(profile)

    token = create_token(data.email)
    return {"token": token, "email": data.email}


class TelegramNotificationSettings(BaseModel):
    """Telegram notification configuration settings."""

    telegram_notify_on_workout: bool | None = None
    telegram_notify_on_nutrition: bool | None = None
    telegram_notify_on_weight: bool | None = None


@router.post("/telegram-notifications")
def update_telegram_notifications(
    settings_data: TelegramNotificationSettings,
    user_email: WritableCurrentUser,
    db: DatabaseDep,
) -> JSONResponse:
    """
    Updates the user's Telegram notification preferences.
    """
    existing_profile = db.get_user_profile(user_email)

    if not existing_profile:
        logger.warning(
            "Attempted to update notifications for non-existent user: %s", user_email
        )
        raise HTTPException(status_code=404, detail="User profile not found")

    # Update only the fields that were provided (not None)
    update_data = settings_data.model_dump(exclude_unset=True)
    updated_profile = existing_profile.model_copy(update=update_data)
    db.save_user_profile(updated_profile)

    logger.info("Telegram notification settings updated for user: %s", user_email)
    return JSONResponse(
        content={"message": "Notification settings updated successfully"}
    )


@router.post("/refresh")
def refresh(user_email: CurrentUser) -> dict[str, str]:
    """
    Exchange a valid JWT for a new one with a fresh 2-hour expiration.

    Called proactively by the frontend before the token expires,
    ensuring active users are never disconnected due to token expiry.
    """
    new_token = create_token(user_email)
    logger.info("Token refreshed for user")
    return {"token": new_token}


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
