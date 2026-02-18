"""
Onboarding API endpoints.
"""

from datetime import date, datetime, timezone
import bcrypt
from fastapi import APIRouter, HTTPException, Query
from src.api.models.onboarding import (
    OnboardingCompleteRequest,
    OnboardingCompleteResponse,
    OnboardingValidateResponse,
)
from src.api.models.user_profile import UserProfile
from src.api.models.trainer_profile import TrainerProfile
from src.api.models.weight_log import WeightLog
from src.core.deps import get_mongo_database
from src.core.logs import logger
from src.services.auth import user_login

router = APIRouter()


@router.get("/validate", response_model=OnboardingValidateResponse)
def validate_invite_token(
    token: str = Query(..., description="Invite token to validate"),
):
    """
    Validates an invite token.

    Args:
        token: The invite token from the URL query parameter.

    Returns:
        OnboardingValidateResponse with validation status.

    Status Codes:
        200: Token is valid
        404: Token not found
        410: Token expired
        409: Token already used
    """
    # pylint: disable=no-member
    db = get_mongo_database()
    invite_repo = db.invites

    invite = invite_repo.get_by_token(token)

    if not invite:
        logger.info("Invite token not found: %s", token)
        raise HTTPException(
            status_code=404, detail={"valid": False, "reason": "not_found"}
        )

    if invite.used:
        logger.info("Invite token already used: %s", token)
        raise HTTPException(
            status_code=409, detail={"valid": False, "reason": "already_used"}
        )

    now = datetime.now(timezone.utc)
    invite_expires_at = invite.expires_at
    if invite_expires_at.tzinfo is None:
        invite_expires_at = invite_expires_at.replace(tzinfo=timezone.utc)

    if invite_expires_at < now:
        logger.info("Invite token expired: %s", token)
        raise HTTPException(
            status_code=410, detail={"valid": False, "reason": "expired"}
        )

    logger.info("Invite token validated successfully: %s for %s", token, invite.email)
    return OnboardingValidateResponse(valid=True, email=invite.email, reason=None)


@router.post("/complete", response_model=OnboardingCompleteResponse)
def complete_onboarding(request: OnboardingCompleteRequest):
    """
    Completes the onboarding process by creating user and trainer profiles.

    Args:
        request: Onboarding completion data including token and user info.

    Returns:
        OnboardingCompleteResponse with JWT token.

    Raises:
        HTTPException: If token is invalid, expired, or already used.
    """
    # pylint: disable=no-member
    db = get_mongo_database()
    invite_repo = db.invites

    # Validate token again (defensive)
    invite = invite_repo.get_by_token(request.token)

    if not invite:
        logger.warning("Onboarding attempt with invalid token: %s", request.token)
        raise HTTPException(status_code=404, detail="Invalid invite token")

    if invite.used:
        logger.warning("Onboarding attempt with used token: %s", request.token)
        raise HTTPException(status_code=409, detail="Invite already used")

    now = datetime.now(timezone.utc)
    invite_expires_at = invite.expires_at
    if invite_expires_at.tzinfo is None:
        invite_expires_at = invite_expires_at.replace(tzinfo=timezone.utc)

    if invite_expires_at < now:
        logger.warning("Onboarding attempt with expired token: %s", request.token)
        raise HTTPException(status_code=410, detail="Invite expired")

    email = invite.email

    # Check if user already exists (defensive)
    if db.get_user_profile(email):
        logger.error("User already exists during onboarding: %s", email)
        raise HTTPException(status_code=409, detail="User already exists")

    # Hash password
    password_hash = bcrypt.hashpw(request.password.encode(), bcrypt.gensalt()).decode()

    # Create user profile
    user_profile = UserProfile(
        email=email,
        password_hash=password_hash,
        role="user",
        gender=request.gender,
        age=request.age,
        weight=request.weight,
        height=request.height,
        goal_type=request.goal_type,
        weekly_rate=request.weekly_rate,
        # Mandatory fields for Mypy/Pyright
        # Optional/Default fields
        goal=None,
        target_weight=None,
    )

    # Create trainer profile
    trainer_profile = TrainerProfile(
        user_email=email, trainer_type=request.trainer_type
    )

    # Save to database
    db.save_user_profile(user_profile)
    db.save_trainer_profile(trainer_profile)

    # Criar primeiro registro de peso (histórico desde o onboarding)
    initial_log = WeightLog(
        user_email=email,
        date=date.today(),
        weight_kg=request.weight,
        trend_weight=request.weight,  # Primeiro log: trend = peso real
    )
    db.weight.save_log(initial_log)

    # Mark invite as used
    invite_repo.mark_as_used(request.token)

    logger.info("Onboarding completed successfully for: %s", email)

    # Generate JWT token (auto-login)
    jwt_token = user_login(email, request.password)

    return OnboardingCompleteResponse(
        token=jwt_token, message="Conta criada com sucesso!"
    )
