from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.services.auth import verify_token
from src.core.deps import get_hevy_service, get_ai_trainer_brain
from src.services.hevy_service import HevyService
from src.services.trainer import AITrainerBrain
from src.api.models.user_profile import UserProfile

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
HevyServiceDep = Annotated[HevyService, Depends(get_hevy_service)]
BrainDep = Annotated[AITrainerBrain, Depends(get_ai_trainer_brain)]

class ValidateRequest(BaseModel):
    api_key: str

class HevyConfigRequest(BaseModel):
    api_key: Optional[str] = None
    enabled: bool

class ImportRequest(BaseModel):
    from_date: Optional[datetime] = None
    mode: str = Field("skip_duplicates", pattern="^(skip_duplicates|overwrite)$")

@router.post("/validate")
async def validate_key(
    request: ValidateRequest,
    hevy_service: HevyServiceDep
):
    """Validates a Hevy API key."""
    is_valid = await hevy_service.validate_api_key(request.api_key)
    result = {"valid": is_valid}
    
    if is_valid:
        # If valid, also fetch count to display immediately
        count = await hevy_service.get_workout_count(request.api_key)
        result["count"] = count
        
    return result

@router.post("/config")
def save_config(
    request: HevyConfigRequest,
    user_email: CurrentUser,
    brain: BrainDep
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
    return {"message": "Configuration saved"}

@router.get("/status")
def get_status(
    user_email: CurrentUser,
    brain: BrainDep
):
    """Returns current integration status."""
    profile = brain.get_user_profile(user_email)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
        
    return {
        "enabled": getattr(profile, "hevy_enabled", False),
        "has_key": bool(getattr(profile, "hevy_api_key", None)),
        # Mask key for frontend
        "api_key_masked": f"****{profile.hevy_api_key[-4:]}" if getattr(profile, "hevy_api_key", None) else None,
        "last_sync": getattr(profile, "hevy_last_sync", None)
    }

@router.get("/count")
async def get_workout_count(
    user_email: CurrentUser,
    brain: BrainDep,
    hevy_service: HevyServiceDep
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
    user_email: CurrentUser,
    brain: BrainDep,
    hevy_service: HevyServiceDep
):
    """Triggers import of workouts from Hevy."""
    profile = brain.get_user_profile(user_email)
    if not profile or not profile.hevy_api_key:
        raise HTTPException(status_code=400, detail="Hevy API key not configured")
        
    result = await hevy_service.import_workouts(
        user_email=user_email,
        api_key=profile.hevy_api_key,
        from_date=request.from_date,
        mode=request.mode
    )
    
    profile.hevy_last_sync = datetime.now()
    brain.save_user_profile(profile)
        
    return result
