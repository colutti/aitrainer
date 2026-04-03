"""
This module defines the subscription plans and their details.
"""

from enum import Enum
from pydantic import BaseModel


class SubscriptionPlan(str, Enum):
    """Enumeration of available subscription plans."""

    FREE = "Free"
    BASIC = "Basic"
    PRO = "Pro"


class PlanDetails(BaseModel):
    """Details and limits for a specific subscription plan."""

    name: str
    monthly_limit: int | None  # None for no monthly limit
    total_limit: int | None  # None for no total limit
    daily_limit: int | None
    validity_days: int | None
    allowed_trainers: list[str] | None
    price_usd: float
    image_input_enabled: bool = False
    integrations_enabled: bool = False
    telegram_enabled: bool = False
    imports_enabled: bool = False


SUBSCRIPTION_PLANS = {
    SubscriptionPlan.FREE: PlanDetails(
        name="Free",
        monthly_limit=None,
        total_limit=None,
        daily_limit=20,
        validity_days=7,
        allowed_trainers=["gymbro"],
        price_usd=0.0,
    ),
    SubscriptionPlan.BASIC: PlanDetails(
        name="Basic",
        monthly_limit=100,
        total_limit=None,
        daily_limit=None,
        validity_days=None,
        allowed_trainers=None,
        price_usd=4.99,
    ),
    SubscriptionPlan.PRO: PlanDetails(
        name="Pro",
        monthly_limit=300,
        total_limit=None,
        daily_limit=None,
        validity_days=None,
        allowed_trainers=None,
        price_usd=9.99,
        image_input_enabled=True,
        integrations_enabled=True,
        telegram_enabled=True,
        imports_enabled=True,
    ),
}

def get_plan_details(subscription_plan: str | None) -> PlanDetails:
    """Return normalized plan details, falling back to Free."""
    try:
        return SUBSCRIPTION_PLANS[SubscriptionPlan(subscription_plan)]
    except (ValueError, TypeError, KeyError):
        return SUBSCRIPTION_PLANS[SubscriptionPlan.FREE]


def can_use_image_input(subscription_plan: str | None) -> bool:
    """Return whether the current plan can submit image input to AI chat."""
    return get_plan_details(subscription_plan).image_input_enabled


def can_use_integrations(subscription_plan: str | None) -> bool:
    """Return whether the current plan can use app integrations."""
    return get_plan_details(subscription_plan).integrations_enabled


def can_use_telegram(subscription_plan: str | None) -> bool:
    """Return whether the current plan can use Telegram features."""
    return get_plan_details(subscription_plan).telegram_enabled


def can_use_imports(subscription_plan: str | None) -> bool:
    """Return whether the current plan can import external data."""
    return get_plan_details(subscription_plan).imports_enabled
