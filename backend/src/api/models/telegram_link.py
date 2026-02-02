"""Models for Telegram integration."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TelegramLink(BaseModel):
    """Persistent link between Telegram chat and user account."""

    chat_id: int
    user_email: str
    linked_at: datetime
    telegram_username: Optional[str] = None


class TelegramLinkCode(BaseModel):
    """Temporary linking code with TTL."""

    code: str
    user_email: str
    created_at: datetime
    expires_at: datetime


class TelegramStatus(BaseModel):
    """Response for /status endpoint."""

    linked: bool
    telegram_username: Optional[str] = None
    linked_at: Optional[datetime] = None
    telegram_notify_on_workout: bool = True
    telegram_notify_on_nutrition: bool = False
    telegram_notify_on_weight: bool = False


class LinkingCodeResponse(BaseModel):
    """Response for /generate-code endpoint."""

    code: str
    expires_in_seconds: int = 600
