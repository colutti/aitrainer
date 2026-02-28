from enum import Enum
from pydantic import BaseModel

class SubscriptionPlan(str, Enum):
    FREE = "Free"
    BASIC = "Basic"
    PRO = "Pro"
    PREMIUM = "Premium"

class PlanDetails(BaseModel):
    name: str
    monthly_limit: int | None  # None for no monthly limit
    total_limit: int | None   # None for no total limit
    price_usd: float

SUBSCRIPTION_PLANS = {
    SubscriptionPlan.FREE: PlanDetails(
        name="Free",
        monthly_limit=None,
        total_limit=20,
        price_usd=0.0
    ),
    SubscriptionPlan.BASIC: PlanDetails(
        name="Basic",
        monthly_limit=100,
        total_limit=None,
        price_usd=4.99
    ),
    SubscriptionPlan.PRO: PlanDetails(
        name="Pro",
        monthly_limit=300,
        total_limit=None,
        price_usd=9.99
    ),
    SubscriptionPlan.PREMIUM: PlanDetails(
        name="Premium",
        monthly_limit=1000,
        total_limit=None,
        price_usd=19.99
    ),
}
