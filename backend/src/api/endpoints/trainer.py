"""
API endpoints for managing trainer profiles.
"""

from fastapi import APIRouter, Depends, HTTPException
from src.api.models.trainer_profile import TrainerProfileInput, TrainerProfile
from src.services.trainer import AITrainerBrain
from src.core.deps import get_ai_trainer_brain
from src.services.auth import verify_token
from src.trainers.registry import TrainerRegistry
from src.core.subscription import SubscriptionPlan, SUBSCRIPTION_PLANS

router = APIRouter()


@router.put("/update_trainer_profile", response_model=TrainerProfile)
async def update_trainer_profile(
    profile_input: TrainerProfileInput,
    user_email: str = Depends(verify_token),
    brain: AITrainerBrain = Depends(get_ai_trainer_brain),
):
    """
    Updates the user's trainer profile preference.
    Validates against the user's subscription plan.
    """
    # Check plan limits
    user_profile = brain.get_user_profile(user_email)
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    try:
        plan = SubscriptionPlan(user_profile.subscription_plan)
    except (ValueError, AttributeError):
        plan = SubscriptionPlan.FREE

    plan_details = SUBSCRIPTION_PLANS[plan]
    allowed = plan_details.allowed_trainers

    if allowed and profile_input.trainer_type not in allowed:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Trainer '{profile_input.trainer_type}' is not available "
                f"in the {plan.value} plan"
            ),
        )

    profile = TrainerProfile(user_email=user_email, **profile_input.model_dump())
    brain.save_trainer_profile(profile)
    return profile


@router.get("/trainer_profile", response_model=TrainerProfile)
async def get_trainer_profile(
    user_email: str = Depends(verify_token),
    brain: AITrainerBrain = Depends(get_ai_trainer_brain),
):
    """
    Retrieves the user's current trainer profile.
    Ensures it respects the user's current subscription plan.
    """
    return brain.get_or_create_trainer_profile(user_email)


@router.get("/available_trainers")
async def get_available_trainers(_user_email: str = Depends(verify_token)):
    """
    Returns a list of all available trainer cards for the frontend.
    """
    registry = TrainerRegistry()
    return registry.list_trainers_for_api()
