"""
API endpoints for Hevy integration.
"""
import asyncio
import secrets
from datetime import datetime
from typing import Annotated, Optional, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.services.auth import verify_token
from src.core.deps import get_hevy_service, get_ai_trainer_brain, get_telegram_service
from src.services.hevy_service import HevyService
from src.services.trainer import AITrainerBrain
from src.core.logs import logger

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
HevyServiceDep = Annotated[HevyService, Depends(get_hevy_service)]
BrainDep = Annotated[AITrainerBrain, Depends(get_ai_trainer_brain)]


class WebhookDeps:  # pylint: disable=too-few-public-methods
    """Combines dependencies for Hevy webhook to reduce argument count."""

    def __init__(
        self,
        brain: BrainDep,
        hevy_service: HevyServiceDep,
        background_tasks: BackgroundTasks,
    ):
        self.brain = brain
        self.hevy_service = hevy_service
        self.background_tasks = background_tasks


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


async def _fetch_workout_with_retry(
    api_key: str, workout_id: str, hevy_service: HevyService
) -> Optional[dict]:
    """Helper to fetch workout with retries."""
    max_retries = 3
    retry_delay = 5
    for attempt in range(max_retries):
        if attempt > 0:
            logger.info(
                "[Webhook BG] Retrying in %ss (%d/%d)",
                retry_delay, attempt + 1, max_retries
            )
            await asyncio.sleep(retry_delay)
        hevy_workout = await hevy_service.fetch_workout_by_id(api_key, workout_id)
        if hevy_workout:
            return hevy_workout
    return None


async def _handle_workout_notification(user_email: str, workout_log: Any, brain: AITrainerBrain):
    """Handles Telegram notification after a workout is synced."""
    profile = brain.get_user_profile(user_email)
    if not profile:
        return

    telegram_link = brain.database.telegram.get_link_by_email(user_email)
    if not telegram_link:
        return

    if not getattr(profile, "telegram_notify_on_workout", True):
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
    logger.info("[Webhook BG] Requesting AI analysis for %s", user_email)
    analysis = await brain.analyze_workout_async(user_email, workout_summary)

    if not analysis or not analysis.strip():
        logger.warning("[Webhook BG] AI analysis empty for %s, skipping notification", user_email)
        return

    # Enviar via Telegram
    telegram_service = get_telegram_service()
    await telegram_service.send_notification(user_email, analysis)


async def process_webhook_async(
    user_email: str,
    api_key: Optional[str],
    workout_id: str,
    hevy_service: HevyService,
    brain: AITrainerBrain,
):
    """
    Background task to process Hevy webhook.
    Fetches workout, transforms and saves.
    """
    logger.info(
        "[Webhook BG] Starting background processing for user %s, workout %s",
        user_email, workout_id
    )

    if not api_key:
        logger.error("[Webhook BG] FAILED: Missing Hevy API key.")
        return

    try:
        hevy_workout = await _fetch_workout_with_retry(api_key, workout_id, hevy_service)
        if not hevy_workout:
            logger.error("[Webhook BG] Workout %s not found in Hevy", workout_id)
            return

        workout_log = hevy_service.transform_to_workout_log(hevy_workout, user_email)
        if not workout_log:
            logger.error("[Webhook BG] Failed to transform workout %s", workout_id)
            return

        hevy_service.workout_repository.save_log(workout_log)
        logger.info("[Webhook BG] SUCCESS: Workout %s synced for %s.", workout_id, user_email)

        try:
            await _handle_workout_notification(user_email, workout_log, brain)
        except Exception as notif_error:  # pylint: disable=broad-exception-caught
            logger.error("[Webhook BG] Notification error: %s", notif_error)

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("[Webhook BG] Error processing webhook: %s", e)


# ==================== WEBHOOK ENDPOINTS ====================


@router.get("/webhook/config")
def get_webhook_config(
    user_email: CurrentUser, brain: BrainDep, request: Request
):
    """Returns current webhook configuration."""
    profile = brain.get_user_profile(user_email)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    token = getattr(profile, "hevy_webhook_token", None)
    secret = getattr(profile, "hevy_webhook_secret", None)

    if not token:
        return {
            "hasWebhook": False,
            "webhookUrl": None,
            "authHeader": None,
        }

    # Build webhook URL dynamically from request (works locally and in production)
    # Check for X-Forwarded-Proto header set by Cloud Run / Nginx
    proto = request.headers.get("x-forwarded-proto", "http")

    # In production Cloud Run, request.base_url might be http, but we want to show https
    # Only force https if we're not on localhost
    base_url = str(request.base_url).rstrip("/")
    if "localhost" not in base_url and "127.0.0.1" not in base_url:
        base_url = base_url.replace("http://", "https://")
    elif proto == "https":
        base_url = base_url.replace("http://", "https://")

    webhook_url = f"{base_url}/integrations/hevy/webhook/{token}"
    masked_auth = f"Bearer ****{secret[-4:]}" if secret else None

    return {
        "hasWebhook": True,
        "webhookUrl": webhook_url,
        "authHeader": masked_auth,
    }


@router.post("/webhook/generate")
def generate_webhook_credentials(
    user_email: CurrentUser, brain: BrainDep, request: Request
):
    """Generates a new webhook token and secret."""
    try:
        profile = brain.get_user_profile(user_email)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Preserve existing credentials — only generate on first setup
        token = profile.hevy_webhook_token or secrets.token_urlsafe(16)
        secret = profile.hevy_webhook_secret or secrets.token_urlsafe(24)

        profile.hevy_webhook_token = token
        profile.hevy_webhook_secret = secret

        logger.info("Generating webhook for user")
        brain.save_user_profile(profile)

        # Build webhook URL dynamically from request (works locally and in production)
        proto = request.headers.get("x-forwarded-proto", "http")
        base_url = str(request.base_url).rstrip("/")
        if "localhost" not in base_url and "127.0.0.1" not in base_url:
            base_url = base_url.replace("http://", "https://")
        elif proto == "https":
            base_url = base_url.replace("http://", "https://")

        webhook_url = f"{base_url}/integrations/hevy/webhook/{token}"

        return {
            "webhookUrl": webhook_url,
            "authHeader": f"Bearer {secret}",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("CRITICAL UNHANDLED ERROR in generate_webhook: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}"
        ) from e


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


@router.get("/webhook/{user_token}", include_in_schema=False)
@router.post("/webhook/{user_token}", include_in_schema=False)
async def receive_hevy_webhook(
    user_token: str,
    request: Request,
    deps: Annotated[WebhookDeps, Depends(WebhookDeps)],
    body: Optional[WebhookPayload] = None,
):
    """
    Receives webhook from Hevy. Identifies user by token and validates auth header.
    Supports GET for verification and POST for payload.
    """
    # pylint: disable=no-member
    client_host = request.client.host if request.client else "unknown"
    method = request.method

    logger.info("--- [Hevy Webhook Start] ---")
    logger.info("Method: %s | Client IP: %s | URL: %s", method, client_host, request.url)

    authorization = request.headers.get("authorization")

    if method == "GET":
        profile = deps.brain.database.users.find_by_webhook_token(user_token)
        if not profile:
            return JSONResponse(status_code=404, content={"message": "Token not found"})
        return {"status": "ok", "message": "Hevy webhook endpoint is active"}

    if not body:
        try:
            body_json = await request.json()
            body = WebhookPayload(**body_json)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("[Webhook] MALFORMED PAYLOAD from %s: %s", client_host, e)
            raise HTTPException(status_code=400, detail="Malformed JSON payload") from e

    profile = deps.brain.database.users.find_by_webhook_token(user_token)
    if not profile:
        raise HTTPException(status_code=404, detail="Invalid token")

    if profile.hevy_webhook_secret:
        expected = f"Bearer {profile.hevy_webhook_secret}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail="Invalid authorization")

    workout_id = body.payload.get("workoutId")
    if not workout_id:
        raise HTTPException(status_code=400, detail="Missing workoutId")

    deps.background_tasks.add_task(
        process_webhook_async,
        user_email=profile.email,
        api_key=profile.hevy_api_key,
        workout_id=workout_id,
        hevy_service=deps.hevy_service,
        brain=deps.brain,
    )

    logger.info("[Webhook] SUCCESS: Queued for user %s", profile.email)
    return {"status": "queued"}
