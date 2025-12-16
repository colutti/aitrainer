"""
This module contains the API endpoints for trainer management.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from src.services.auth import verify_token
from src.core.deps import get_ai_trainer_brain
from src.api.models.trainer_profile import TrainerProfile, TrainerProfileInput
from src.services.trainer import AITrainerBrain

from src.core.logs import logger

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
AITrainerBrainDep = Annotated[AITrainerBrain, Depends(get_ai_trainer_brain)]


@router.post("/update_trainer_profile")
def update_trainer_profile(
    profile_data: TrainerProfileInput, user_email: CurrentUser, brain: AITrainerBrainDep
) -> JSONResponse:
    """
    Updates the trainer profile with the provided information,
    ensuring the update is associated with the authenticated user.

    Args:
       profile_data (TrainerProfileInput): The editable data for the trainer profile.
       user_email (CurrentUser): The authenticated user's email.

    Returns:
     JSONResponse: A response indicating the profile was updated successfully.
    """
    # Creates the complete TrainerProfile object, including user_email
    profile = TrainerProfile(**profile_data.model_dump(), user_email=user_email)
    brain.save_trainer_profile(profile)
    logger.info("Trainer profile updated for user: %s", user_email)
    return JSONResponse(content={"message": "Profile updated successfully"})


@router.get("/trainer_profile")
def get_trainer_profile(
    user_email: CurrentUser, brain: AITrainerBrainDep
) -> TrainerProfile:
    """
    Retrieves the trainer profile associated with the authenticated user.

    Args:
     user_email (CurrentUser): The authenticated user information,
     injected by dependency (verify_token).

    Returns:
    TrainerProfile: The trainer profile associated with the authenticated user.
    """
    trainer_profile = brain.get_trainer_profile(user_email)
    if not trainer_profile:
        logger.warning("Attempted to retrieve non-existent trainer profile for email: %s", user_email)
        raise HTTPException(status_code=404, detail="Trainer profile not found")
    return trainer_profile
