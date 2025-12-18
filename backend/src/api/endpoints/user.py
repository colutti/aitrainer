"""
This module contains the API endpoints for user management.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from src.services.auth import user_login, user_logout, oauth2_scheme, verify_token
from src.core.deps import get_ai_trainer_brain
from src.core.logs import logger
from src.api.models.auth import LoginRequest
from src.api.models.user_profile import UserProfile, UserProfileInput
from src.services.trainer import AITrainerBrain

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
AITrainerBrainDep = Annotated[AITrainerBrain, Depends(get_ai_trainer_brain)]

@router.post("/login")
def login(data: LoginRequest) -> dict:
    """
    Authenticates a user with the provided email and password.

    Args:
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
        logger.warning("Attempted to retrieve non-existent user profile for email: %s", user_email)
        raise HTTPException(status_code=404, detail="User profile not found")
    return user_profile


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
    # Create the UserProfile object, including the user_email from the token
    profile = UserProfile(**profile_data.model_dump(), email=user_email)
    brain.save_user_profile(profile)
    logger.info("User profile updated for email: %s", user_email)
    return JSONResponse(content={"message": "Profile updated successfully"})


@router.get("/logout")
def logout(user_email: CurrentUser, token: str = Depends(oauth2_scheme)) -> JSONResponse:
    """
    Logs out the current user by calling the user_logout function
    and returns a JSON response indicating success.

    Returns:
        JSONResponse: A response object with a message confirming successful logout.
    """
    user_logout(token)
    logger.info("User logged out: %s", user_email)
    return JSONResponse(content={"message": "Logged out successfully"})
