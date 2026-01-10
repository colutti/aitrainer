from fastapi import APIRouter, Depends, HTTPException
from src.api.models.trainer_profile import TrainerProfileInput, TrainerProfile
from src.services.trainer import AITrainerBrain
from src.services.trainer import AITrainerBrain
from src.core.deps import get_ai_trainer_brain
from src.services.auth import verify_token
from src.trainers.registry import TrainerRegistry
from src.trainers.registry import TrainerRegistry

router = APIRouter()

@router.put("/update_trainer_profile", response_model=TrainerProfile)
async def update_trainer_profile(
    profile_input: TrainerProfileInput,
    user_email: str = Depends(verify_token),
    brain: AITrainerBrain = Depends(get_ai_trainer_brain)
):
    """
    Updates the user's trainer profile preference.
    """
    profile = TrainerProfile(user_email=user_email, **profile_input.model_dump())
    brain.save_trainer_profile(profile)
    return profile

@router.get("/trainer_profile", response_model=TrainerProfile)
async def get_trainer_profile(
    user_email: str = Depends(verify_token),
    brain: AITrainerBrain = Depends(get_ai_trainer_brain)
):
    """
    Retrieves the user's current trainer profile.
    """
    profile = brain.get_trainer_profile(user_email)
    if not profile:
        # Return default if not found
        return TrainerProfile(user_email=user_email, trainer_type="atlas")
    return profile

@router.get("/available_trainers")
async def get_available_trainers(
    user_email: str = Depends(verify_token)
):
    """
    Returns a list of all available trainer cards for the frontend.
    """
    registry = TrainerRegistry()
    return registry.list_trainers_for_api()
