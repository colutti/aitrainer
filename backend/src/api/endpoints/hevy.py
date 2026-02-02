from datetime import datetime
import secrets
from typing import Annotated, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from src.services.auth import verify_token
from src.core.deps import get_hevy_service, get_ai_trainer_brain
from src.services.hevy_service import HevyService
from src.services.trainer import AITrainerBrain

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
async def validate_key(request: ValidateRequest, hevy_service: HevyServiceDep):
    """Validates a Hevy API key."""
    is_valid = await hevy_service.validate_api_key(request.api_key)

    if is_valid:
        # If valid, also fetch count to display immediately
        count = await hevy_service.get_workout_count(request.api_key)
        return {"valid": is_valid, "count": count}

    return {"valid": is_valid}


@router.post("/config")
def save_config(request: HevyConfigRequest, user_email: CurrentUser, brain: BrainDep):
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
def get_status(user_email: CurrentUser, brain: BrainDep):
    """Returns current integration status."""
    profile = brain.get_user_profile(user_email)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    api_key = getattr(profile, "hevy_api_key", None)
    api_key_masked = f"****{api_key[-4:]}" if api_key else None

    return {
        "enabled": getattr(profile, "hevy_enabled", False),
        "has_key": bool(api_key),
        "api_key_masked": api_key_masked,
        "last_sync": getattr(profile, "hevy_last_sync", None),
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
    user_email: CurrentUser,
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


# ==================== WEBHOOK MODELS ====================


class WebhookPayload(BaseModel):
    """Payload sent by Hevy webhook."""

    id: str
    payload: dict


class WebhookConfigResponse(BaseModel):
    """Response for webhook configuration."""

    has_webhook: bool
    webhook_url: Optional[str] = None
    auth_header: Optional[str] = None  # Masked for display


class WebhookGenerateResponse(BaseModel):
    """Response when generating webhook credentials."""

    webhook_url: str
    auth_header: str  # FULL secret to show user once


# ==================== WEBHOOK PROCESSING ====================


async def process_webhook_async(
    user_email: str, api_key: str, workout_id: str, hevy_service: HevyService
):
    """
    Background task to process Hevy webhook.
    Fetches workout, transforms and saves.
    """
    from src.core.logs import logger
    from src.core.deps import get_ai_trainer_brain, get_telegram_service

    logger.info(f"[Webhook BG] Processing workout {workout_id} for {user_email}")
    
    if not api_key:
        logger.error(f"[Webhook BG] Missing Hevy API key for user {user_email}. Cannot fetch workout details.")
        return

    try:
        # 1. Fetch from Hevy with retry (handle potential race conditions)
        max_retries = 3
        retry_delay = 5  # seconds
        hevy_workout = None

        for attempt in range(max_retries):
            if attempt > 0:
                import asyncio
                logger.info(f"[Webhook BG] Retrying workout fetch in {retry_delay}s (Attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(retry_delay)

            hevy_workout = await hevy_service.fetch_workout_by_id(api_key, workout_id)
            if hevy_workout:
                break

        if not hevy_workout:
            logger.error(f"[Webhook BG] Workout {workout_id} not found in Hevy after {max_retries} attempts")
            return

        # 2. Transform
        workout_log = hevy_service.transform_to_workout_log(hevy_workout, user_email)
        if not workout_log:
            logger.error(f"[Webhook BG] Failed to transform workout {workout_id}")
            return

        # 3. Save (deduplication handled by repository/service)
        hevy_service.workout_repository.save_log(workout_log)
        logger.info(
            f"[Webhook BG] Successfully synced workout {workout_id} for {user_email}"
        )

        # === NOVA LÓGICA: Notificação Telegram ===
        try:
            brain = get_ai_trainer_brain()
            profile = brain.get_user_profile(user_email)

            # Verificar elegibilidade
            if not profile:
                logger.warning(f"[Webhook BG] No profile found for {user_email}")
                return

            # Verificar se Telegram está vinculado e habilitado
            telegram_repo = brain._database.db["telegram_links"]
            telegram_link = telegram_repo.find_one({"user_email": user_email})

            if not telegram_link:
                logger.debug(f"[Webhook BG] No Telegram link for {user_email}, skipping notification")
                return

            if not getattr(profile, "telegram_notify_on_workout", True):
                logger.debug(f"[Webhook BG] Telegram workout notifications disabled for {user_email}")
                return

            # Gerar resumo do treino
            exercises_summary = ", ".join([ex.name for ex in workout_log.exercises[:3]])
            if len(workout_log.exercises) > 3:
                exercises_summary += f" (+ {len(workout_log.exercises) - 3} outros)"

            workout_summary = (
                f"{workout_log.workout_type} em {workout_log.date.strftime('%d/%m/%Y')} - "
                f"{len(workout_log.exercises)} exercícios: {exercises_summary}"
            )

            # Gerar análise pela IA
            logger.info(f"[Webhook BG] Requesting AI analysis for {user_email}")
            analysis = await brain.analyze_workout_async(user_email, workout_summary)

            # Enviar via Telegram
            telegram_service = get_telegram_service()
            success = await telegram_service.send_notification(user_email, analysis)

            if success:
                logger.info(f"[Webhook BG] Telegram notification sent for workout {workout_id}")
            else:
                logger.warning(f"[Webhook BG] Failed to send Telegram notification")

        except Exception as notif_error:
            # Não propagar erro (treino já foi salvo)
            logger.error(f"[Webhook BG] Notification error (non-critical): {notif_error}")

    except Exception as e:
        logger.error(f"[Webhook BG] Error: {e}")


# ==================== WEBHOOK ENDPOINTS ====================
# IMPORTANT: Static routes MUST be declared BEFORE parameterized routes!
# Otherwise FastAPI will match /webhook/generate as /webhook/{user_token}



@router.get("/webhook/config")
def get_webhook_config(
    user_email: CurrentUser, brain: BrainDep
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
    webhook_url = f"{base_url}/integrations/hevy/webhook/{token}"

    # Mask secret: Bearer ****abcd
    masked_auth = f"Bearer ****{secret[-4:]}" if secret else None

    return WebhookConfigResponse(
        has_webhook=True, webhook_url=webhook_url, auth_header=masked_auth
    )


@router.post("/webhook/generate")
def generate_webhook_credentials(
    user_email: CurrentUser, brain: BrainDep
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
        webhook_url = f"{base_url}/integrations/hevy/webhook/{token}"

        return WebhookGenerateResponse(
            webhook_url=webhook_url, auth_header=f"Bearer {secret}"
        )
    except HTTPException:
        raise
    except Exception as e:
        from src.core.logs import logger

        logger.exception(f"CRITICAL UNHANDLED ERROR in generate_webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.delete("/webhook")
def revoke_webhook(user_email: CurrentUser, brain: BrainDep):
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
    authorization: Optional[str] = Header(None),
):
    """
    Receives webhook from Hevy. Identifies user by token and validates auth header.
    Responds immediately and processes in background.
    """
    from src.core.logs import logger

    logger.info(f"[Webhook] Received webhook from Hevy. Payload: {body.model_dump()}")

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
        hevy_service=hevy_service,
    )

    return {"status": "queued"}
