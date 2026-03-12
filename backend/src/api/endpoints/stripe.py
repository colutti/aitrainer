"""
Stripe payment and webhook endpoints.
"""
from datetime import datetime, timezone
import stripe
from fastapi import APIRouter, Header, Request, HTTPException
from src.core.config import settings
from src.api.endpoints.user import CurrentUser, AITrainerBrainDep
from src.services.stripe import create_checkout_session, create_customer_portal_session
from src.core.logs import logger

router = APIRouter()


@router.post("/create-checkout-session")
async def checkout_session(
    price_id: str,
    success_url: str,
    cancel_url: str,
    user_email: CurrentUser,
    brain: AITrainerBrainDep,
):
    """Create a Stripe checkout session for a user."""
    profile = brain.get_user_profile(user_email)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        url = create_checkout_session(profile, price_id, success_url, cancel_url)
        return {"url": url}
    except Exception as e:
        logger.error("Error creating checkout session: %s", e)
        raise HTTPException(status_code=500, detail="Error creating checkout session") from e


@router.post("/create-portal-session")
async def portal_session(
    return_url: str, user_email: CurrentUser, brain: AITrainerBrainDep
):
    """Create a Stripe customer portal session for a user."""
    profile = brain.get_user_profile(user_email)
    if not profile or not profile.stripe_customer_id:
        raise HTTPException(status_code=400, detail="User has no Stripe customer ID")

    try:
        url = create_customer_portal_session(profile.stripe_customer_id, return_url)
        return {"url": url}
    except Exception as e:
        logger.error("Error creating portal session: %s", e)
        raise HTTPException(status_code=500, detail="Error creating portal session") from e


@router.post("/webhook")
async def stripe_webhook(
    request: Request, brain: AITrainerBrainDep, stripe_signature: str = Header(None)
):
    """Handle Stripe webhooks."""
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.error("STRIPE_WEBHOOK_SECRET is not configured")
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(  # type: ignore
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return {"status": "invalid payload"}
    except stripe.error.SignatureVerificationError as exc:  # type: ignore
        raise HTTPException(status_code=400, detail="Invalid signature") from exc

    logger.info("Stripe Webhook received: %s", event["type"])

    if event["type"] == "checkout.session.completed":
        _handle_checkout_completed(event["data"]["object"], brain)
    elif event["type"] in ["customer.subscription.created", "customer.subscription.updated"]:
        _handle_subscription_updated(event["data"]["object"], brain)
    elif event["type"] == "customer.subscription.deleted":
        _handle_subscription_deleted(event["data"]["object"], brain)

    return {"status": "success"}


def _handle_checkout_completed(session, brain):
    """Handle checkout.session.completed event."""
    user_email = session.get("metadata", {}).get("user_email")
    customer_id = session.get("customer")
    if user_email:
        brain.update_user_profile_fields(
            user_email, {"stripe_customer_id": customer_id}
        )


def _handle_subscription_updated(subscription, brain):
    """Handle subscription created/updated event."""
    customer_id = subscription.get("customer")
    status = subscription.get("status")

    if not subscription.get("items") or not subscription["items"].get("data"):
        logger.warning("Subscription %s has no items", subscription["id"])
        return

    price_id = subscription["items"]["data"][0]["price"]["id"]
    plan = "Free"
    if price_id == settings.STRIPE_PRICE_ID_BASIC:
        plan = "Basic"
    elif price_id == settings.STRIPE_PRICE_ID_PRO:
        plan = "Pro"
    elif price_id == settings.STRIPE_PRICE_ID_PREMIUM:
        plan = "Premium"
    else:
        logger.warning("Unknown Stripe price ID received: %s. Fallback to Free.", price_id)

    profile = brain.database.users.find_by_stripe_customer_id(customer_id)
    if profile:
        c_ts = subscription.get("current_period_start", datetime.now().timestamp())
        cycle_start = datetime.fromtimestamp(c_ts, tz=timezone.utc)

        brain.update_user_profile_fields(
            profile.email,
            {
                "stripe_subscription_id": subscription["id"],
                "stripe_subscription_status": status,
                "subscription_plan": plan,
                "current_billing_cycle_start": cycle_start.isoformat(),
                "custom_message_limit": None,
            },
        )


def _handle_subscription_deleted(subscription, brain):
    """Handle customer.subscription.deleted event."""
    customer_id = subscription.get("customer")
    profile = brain.database.users.find_by_stripe_customer_id(customer_id)
    if profile:
        brain.update_user_profile_fields(
            profile.email,
            {
                "stripe_subscription_status": "canceled",
                "subscription_plan": "Free",
                "stripe_subscription_id": None,
            },
        )
