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

# ==================== WEBHOOK MODELS ====================

class WebhookPayload(BaseModel):
    """Payload sent by Hevy webhook."""
    id: str
    payload: dict

class WebhookConfigResponse(BaseModel):
    """Response for webhook configuration."""
    has_webhook: bool
    webhook_url: Optional[str] = None
    auth_header: Optional[str] = None # Masked for display

class WebhookGenerateResponse(BaseModel):
    """Response when generating webhook credentials."""
    webhook_url: str
    auth_header: str # FULL secret to show user once

# ==================== WEBHOOK PROCESSING ====================

async def process_webhook_async(
    user_email: str,
    api_key: str,
    workout_id: str,
    hevy_service: HevyService
):
    """
    Background task to process Hevy webhook.
    Fetches workout, transforms and saves.
    """
    from src.core.logs import logger
    logger.info(f"[Webhook BG] Processing workout {workout_id} for {user_email}")
    
    try:
        # 1. Fetch from Hevy
        hevy_workout = await hevy_service.fetch_workout_by_id(api_key, workout_id)
        if not hevy_workout:
            logger.error(f"[Webhook BG] Workout {workout_id} not found in Hevy")
            return
            
        # 2. Transform
        workout_log = hevy_service.transform_to_workout_log(hevy_workout, user_email)
        if not workout_log:
            logger.error(f"[Webhook BG] Failed to transform workout {workout_id}")
            return
            
        # 3. Save (deduplication handled by repository/service)
        hevy_service.workout_repository.save_log(workout_log)
        logger.info(f"[Webhook BG] Successfully synced workout {workout_id} for {user_email}")
        
    except Exception as e:
        logger.error(f"[Webhook BG] Error: {e}")

# ==================== WEBHOOK ENDPOINTS ====================
# IMPORTANT: Static routes MUST be declared BEFORE parameterized routes!
# Otherwise FastAPI will match /webhook/generate as /webhook/{user_token}

from fastapi import BackgroundTasks, Header, Request
import secrets

@router.get("/webhook/config")
def get_webhook_config(
    user_email: CurrentUser,
    brain: BrainDep
) -> WebhookConfigResponse:
    """Returns current webhook configuration."""
    profile = brain.get_user_profile(user_email)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    token = getattr(profile, "hevy_webhook_token", None)
    secret = getattr(profile, "hevy_webhook_secret", None)
    
    if not token:
        return WebhookConfigResponse(has_webhook=False)
        
    # Build URL (using a placeholder domain if not configured)
    base_url = "https://aitrainer-backend.onrender.com"
    webhook_url = f"{base_url}/api/integrations/hevy/webhook/{token}"
    
    # Mask secret: Bearer ****abcd
    masked_auth = f"Bearer ****{secret[-4:]}" if secret else None
    
    return WebhookConfigResponse(
        has_webhook=True,
        webhook_url=webhook_url,
        auth_header=masked_auth
    )

@router.post("/webhook/generate")
def generate_webhook_credentials(
    user_email: CurrentUser,
    brain: BrainDep
) -> WebhookGenerateResponse:
    """Generates a new webhook token and secret."""
    try:
        from src.core.logs import logger
        
        profile = brain.get_user_profile(user_email)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
            
        token = secrets.token_urlsafe(16)
        secret = secrets.token_urlsafe(24)
        
        profile.hevy_webhook_token = token
        profile.hevy_webhook_secret = secret
        
        logger.info(f"Generating webhook for {user_email}. Token: {token[:4]}...")
        brain.save_user_profile(profile)
        logger.info("Webhook credentials saved successfully.")
        
        base_url = "https://aitrainer-backend.onrender.com"
        webhook_url = f"{base_url}/api/integrations/hevy/webhook/{token}"
        
        return WebhookGenerateResponse(
            webhook_url=webhook_url,
            auth_header=f"Bearer {secret}"
        )
    except HTTPException:
        raise
    except Exception as e:
        from src.core.logs import logger
        logger.exception(f"CRITICAL UNHANDLED ERROR in generate_webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.delete("/webhook")
def revoke_webhook(
    user_email: CurrentUser,
    brain: BrainDep
):
    """Revokes current webhook credentials."""
    profile = brain.get_user_profile(user_email)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    profile.hevy_webhook_token = None
    profile.hevy_webhook_secret = None
    brain.save_user_profile(profile)
    
    return {"message": "Webhook credentials revoked"}

# Parameterized route MUST come LAST
@router.post("/webhook/{user_token}", include_in_schema=False)
async def receive_hevy_webhook(
    user_token: str,
    body: WebhookPayload,
    background_tasks: BackgroundTasks,
    brain: BrainDep,
    hevy_service: HevyServiceDep,
    authorization: Optional[str] = Header(None)
):
    """
    Receives webhook from Hevy. Identifies user by token and validates auth header.
    Responds immediately and processes in background.
    """
    from src.core.logs import logger
    
    # 1. Find user by token
    user_profile = brain._database.users.find_by_webhook_token(user_token)
    if not user_profile:
        logger.warning(f"[Webhook] Invalid token attempt: {user_token[:8]}...")
        raise HTTPException(status_code=404, detail="Invalid token")
        
    # 2. Validate Authorization
    if user_profile.hevy_webhook_secret:
        expected = f"Bearer {user_profile.hevy_webhook_secret}"
        if authorization != expected:
            logger.warning(f"[Webhook] Unauthorized attempt for {user_profile.email}")
            raise HTTPException(status_code=401, detail="Invalid authorization")
            
    # 3. Extract workout ID
    workout_id = body.payload.get("workoutId")
    if not workout_id:
        raise HTTPException(status_code=400, detail="Missing workoutId")
        
    # 4. Queue background task
    background_tasks.add_task(
        process_webhook_async,
        user_email=user_profile.email,
        api_key=user_profile.hevy_api_key,
        workout_id=workout_id,
        hevy_service=hevy_service
    )
    
    return {"status": "queued"}
