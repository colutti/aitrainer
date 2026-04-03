"""Telegram integration endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from fastapi.responses import JSONResponse

from src.core.demo_access import WritableCurrentUser
from src.services.auth import verify_token
from src.core.config import settings
from src.core.subscription import can_use_telegram
from src.core.deps import (
    get_telegram_repository,
    get_telegram_service,
    get_ai_trainer_brain,
)
from src.core.logs import logger
from src.services.trainer import AITrainerBrain
from src.repositories.telegram_repository import TelegramRepository
from src.api.models.telegram_link import TelegramStatus, LinkingCodeResponse

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
TelegramRepoDep = Annotated[TelegramRepository, Depends(get_telegram_repository)]
BrainDep = Annotated[AITrainerBrain, Depends(get_ai_trainer_brain)]


def _assert_telegram_allowed(user_email: str, brain: BrainDep) -> None:
    profile = brain.get_user_profile(user_email)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    if not can_use_telegram(getattr(profile, "subscription_plan", None)):
        raise HTTPException(status_code=403, detail="TELEGRAM_NOT_ALLOWED_FOR_PLAN")


@router.post("/generate-code", response_model=LinkingCodeResponse)
def generate_code(
    user_email: WritableCurrentUser, repo: TelegramRepoDep, brain: BrainDep
) -> LinkingCodeResponse:
    """Generate a 6-character linking code."""
    _assert_telegram_allowed(user_email, brain)
    code = repo.create_linking_code(user_email)
    return LinkingCodeResponse(code=code, expires_in_seconds=600)


@router.get("/status", response_model=TelegramStatus)
def get_status(
    user_email: CurrentUser, repo: TelegramRepoDep, brain: BrainDep
) -> TelegramStatus:
    """Get current Telegram link status."""
    _assert_telegram_allowed(user_email, brain)
    link = repo.get_link_by_email(user_email)
    if not link:
        return TelegramStatus(linked=False)

    # Get user profile to fetch notification preferences
    profile = brain.get_user_profile(user_email)

    notification_settings = {
        "telegram_notify_on_workout": getattr(
            profile, "telegram_notify_on_workout", True
        )
        if profile
        else True,
        "telegram_notify_on_nutrition": getattr(
            profile, "telegram_notify_on_nutrition", False
        )
        if profile
        else False,
        "telegram_notify_on_weight": getattr(
            profile, "telegram_notify_on_weight", False
        )
        if profile
        else False,
    }

    return TelegramStatus(
        linked=True,
        telegram_username=link.telegram_username,
        linked_at=link.linked_at,
        **notification_settings,
    )


@router.post("/unlink")
def unlink(
    user_email: WritableCurrentUser, repo: TelegramRepoDep, brain: BrainDep
) -> JSONResponse:
    """Remove Telegram link."""
    _assert_telegram_allowed(user_email, brain)
    repo.delete_link(user_email)
    return JSONResponse(content={"message": "Unlinked successfully"})


@router.post("/webhook", include_in_schema=False)
async def telegram_webhook(
    request: Request, x_telegram_bot_api_secret_token: str = Header(None)
) -> JSONResponse:
    """
    Receive updates from Telegram.
    Validates secret token header.
    """
    # Validate secret
    if settings.TELEGRAM_WEBHOOK_SECRET and not settings.ENABLE_E2E_TEST_AUTH:
        if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
            logger.warning("Invalid Telegram webhook secret")
            raise HTTPException(status_code=403, detail="Invalid secret")

    try:
        body = await request.json()

        # Get service and process
        service = get_telegram_service()
        await service.handle_update(body)

        return JSONResponse(content={"ok": True})

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Telegram webhook error: %s", e)
        # Always return 200 to Telegram to avoid retries
        return JSONResponse(content={"ok": True})
