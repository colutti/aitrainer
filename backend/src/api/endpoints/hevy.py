"""
API endpoints for Hevy integration.
"""

from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.core.demo_access import WritableCurrentUser
from src.services.auth import verify_token
from src.core.deps import get_hevy_service, get_ai_trainer_brain
from src.services.hevy_service import HevyService
from src.services.trainer import AITrainerBrain
router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
HevyServiceDep = Annotated[HevyService, Depends(get_hevy_service)]
BrainDep = Annotated[AITrainerBrain, Depends(get_ai_trainer_brain)]


class ValidateRequest(BaseModel):
    """Request model for validating API key."""

    api_key: str


class HevyConfigRequest(BaseModel):
    """Request model for Hevy configuration."""

    api_key: Optional[str] = None
    enabled: bool = True


class ImportRequest(BaseModel):
    """Request model for triggering import."""

    from_date: Optional[datetime] = None

    mode: str = Field("skip_duplicates", pattern="^(skip_duplicates|overwrite)$")


@router.post("/validate")
async def validate_key(request: ValidateRequest, hevy_service: HevyServiceDep):
    """Validates a Hevy API key."""
    is_valid = await hevy_service.validate_api_key(request.api_key)

    if is_valid:
        # If valid, also fetch count to display immediately
        count = await hevy_service.get_workout_count(request.api_key)
        return {"valid": is_valid, "count": count}

    return {"valid": is_valid}


@router.post("/config")
def save_config(
    request: HevyConfigRequest, user_email: WritableCurrentUser, brain: BrainDep
):
    """Updates Hevy integration configuration."""
    profile = brain.get_user_profile(user_email)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    # Update Integration fields
    if request.api_key is not None:
        # If empty string is passed, we clear the key
        profile.hevy_api_key = request.api_key if request.api_key != "" else None

    profile.hevy_enabled = request.enabled

    brain.save_user_profile(profile)

    # Return updated status
    api_key = profile.hevy_api_key
    api_key_masked = f"****{api_key[-4:]}" if api_key else None
    return {
        "enabled": profile.hevy_enabled,
        "hasKey": bool(api_key),
        "apiKeyMasked": api_key_masked,
        "lastSync": str(profile.hevy_last_sync) if profile.hevy_last_sync else None,
    }


@router.get("/status")
def get_status(user_email: CurrentUser, brain: BrainDep):
    """Returns current integration status."""
    profile = brain.get_user_profile(user_email)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    api_key = getattr(profile, "hevy_api_key", None)
    api_key_masked = f"****{api_key[-4:]}" if api_key else None

    return {
        "enabled": getattr(profile, "hevy_enabled", False),
        "hasKey": bool(api_key),
        "apiKeyMasked": api_key_masked,
        "lastSync": getattr(profile, "hevy_last_sync", None),
    }


@router.get("/count")
async def get_workout_count(
    user_email: CurrentUser, brain: BrainDep, hevy_service: HevyServiceDep
):
    """Get count of available workouts from Hevy."""
    profile = brain.get_user_profile(user_email)
    if not profile or not profile.hevy_api_key:
        raise HTTPException(status_code=400, detail="Hevy API key not configured")

    count = await hevy_service.get_workout_count(profile.hevy_api_key)
    return {"count": count}


@router.post("/import")
async def import_workouts(
    request: ImportRequest,
    user_email: WritableCurrentUser,
    brain: BrainDep,
    hevy_service: HevyServiceDep,
):
    """Triggers import of workouts from Hevy."""
    profile = brain.get_user_profile(user_email)
    if not profile or not profile.hevy_api_key:
        raise HTTPException(status_code=400, detail="Hevy API key not configured")

    result = await hevy_service.import_workouts(
        user_email=user_email,
        api_key=profile.hevy_api_key,
        from_date=request.from_date,
        mode=request.mode,
    )

    profile.hevy_last_sync = datetime.now()
    brain.save_user_profile(profile)

    return result
