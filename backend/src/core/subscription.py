"""Subscription catalog and effective capability helpers."""

from datetime import datetime, timedelta, timezone
from enum import Enum

from pydantic import BaseModel

TRIAL_DURATION_DAYS = 7


class SubscriptionPlan(str, Enum):
    """Enumeration of available subscription plans."""

    FREE = "Free"
    PRO = "Pro"


class PlanDetails(BaseModel):
    """Details and limits for a specific subscription plan."""

    name: str
    monthly_message_limit: int | None = None
    monthly_photo_limit: int | None = None
    allowed_trainers: list[str] | None = None
    price_usd: float = 0.0
    chat_enabled: bool = False
    image_input_enabled: bool = False
    integrations_enabled: bool = False
    telegram_enabled: bool = False
    imports_enabled: bool = False


SUBSCRIPTION_PLANS = {
    SubscriptionPlan.FREE: PlanDetails(
        name="Free",
        allowed_trainers=["gymbro"],
        price_usd=0.0,
        chat_enabled=False,
    ),
    SubscriptionPlan.PRO: PlanDetails(
        name="Pro",
        monthly_message_limit=500,
        monthly_photo_limit=15,
        allowed_trainers=None,
        price_usd=6.99,
        chat_enabled=True,
        image_input_enabled=True,
        integrations_enabled=True,
        telegram_enabled=True,
        imports_enabled=True,
    ),
}


def _normalize_plan(subscription_plan: str | None) -> SubscriptionPlan:
    try:
        return SubscriptionPlan(subscription_plan)
    except (ValueError, TypeError):
        return SubscriptionPlan.FREE


def default_trial_ends_at(now: datetime | None = None) -> datetime:
    """Return default trial end datetime for newly created free users."""
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current + timedelta(days=TRIAL_DURATION_DAYS)


def is_trial_active(trial_ends_at: datetime | None, now: datetime | None = None) -> bool:
    """Return whether trial is still active."""
    if not isinstance(trial_ends_at, datetime):
        return False
    current = now or datetime.now(timezone.utc)
    trial_end = (
        trial_ends_at.replace(tzinfo=timezone.utc)
        if trial_ends_at.tzinfo is None
        else trial_ends_at
    )
    return current < trial_end


def get_plan_details(subscription_plan: str | None) -> PlanDetails:
    """Return normalized base plan details, falling back to Free."""
    return SUBSCRIPTION_PLANS[_normalize_plan(subscription_plan)]


def get_effective_plan_details(
    subscription_plan: str | None,
    trial_ends_at: datetime | None = None,
) -> PlanDetails:
    """Return effective capabilities (Free trial behaves like Pro)."""
    plan = _normalize_plan(subscription_plan)
    if plan == SubscriptionPlan.PRO:
        return SUBSCRIPTION_PLANS[SubscriptionPlan.PRO]
    if is_trial_active(trial_ends_at):
        return SUBSCRIPTION_PLANS[SubscriptionPlan.PRO]
    return SUBSCRIPTION_PLANS[SubscriptionPlan.FREE]


def can_use_chat(subscription_plan: str | None, trial_ends_at: datetime | None = None) -> bool:
    """Return whether current effective plan can send chat messages."""
    return get_effective_plan_details(subscription_plan, trial_ends_at).chat_enabled


def can_use_image_input(
    subscription_plan: str | None, trial_ends_at: datetime | None = None
) -> bool:
    """Return whether current effective plan can submit image input to AI chat."""
    return get_effective_plan_details(
        subscription_plan, trial_ends_at
    ).image_input_enabled


def can_use_integrations(
    subscription_plan: str | None, trial_ends_at: datetime | None = None
) -> bool:
    """Return whether current effective plan can use integrations."""
    return get_effective_plan_details(
        subscription_plan, trial_ends_at
    ).integrations_enabled


def can_use_telegram(
    subscription_plan: str | None, trial_ends_at: datetime | None = None
) -> bool:
    """Return whether current effective plan can use Telegram features."""
    return get_effective_plan_details(subscription_plan, trial_ends_at).telegram_enabled


def can_use_imports(
    subscription_plan: str | None, trial_ends_at: datetime | None = None
) -> bool:
    """Return whether current effective plan can import external data."""
    return get_effective_plan_details(subscription_plan, trial_ends_at).imports_enabled
