"""
Stripe payment and webhook endpoints.
"""
from datetime import datetime, timezone
import stripe
from fastapi import APIRouter, Header, Request, HTTPException
from src.core.config import settings
from src.api.endpoints.user import CurrentUser, AITrainerBrainDep
from src.services.stripe import create_checkout_session, create_customer_portal_session
from src.api.models.stripe import CheckoutSessionRequest, PortalSessionRequest
from src.core.logs import logger

router = APIRouter()


@router.post("/create-checkout-session")
async def checkout_session(
    request: CheckoutSessionRequest,
    user_email: CurrentUser,
    brain: AITrainerBrainDep,
):
    """Create a Stripe checkout session for a user."""
    profile = brain.get_user_profile(user_email)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        url = create_checkout_session(
            profile, request.price_id, request.success_url, request.cancel_url
        )
        return {"url": url}
    except Exception as e:
        logger.error("Error creating checkout session: %s", e)
        raise HTTPException(status_code=500, detail="Error creating checkout session") from e


@router.post("/create-portal-session")
async def portal_session(
    request: PortalSessionRequest, user_email: CurrentUser, brain: AITrainerBrainDep
):
    """Create a Stripe customer portal session for a user."""
    profile = brain.get_user_profile(user_email)
    if not profile or not profile.stripe_customer_id:
        raise HTTPException(status_code=400, detail="User has no Stripe customer ID")

    try:
        url = create_customer_portal_session(profile.stripe_customer_id, request.return_url)
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

    # Only assign a paid plan if the status is active or trialing
    if status in ["active", "trialing"]:
        if price_id == settings.STRIPE_PRICE_ID_BASIC:
            plan = "Basic"
        elif price_id == settings.STRIPE_PRICE_ID_PRO:
            plan = "Pro"
        elif price_id == settings.STRIPE_PRICE_ID_PREMIUM:
            plan = "Premium"
        else:
            logger.warning("Unknown Stripe price ID received: %s. Fallback to Free.", price_id)
    else:
        logger.info("Subscription status %s received for customer %s. Set to Free.", status, customer_id)

    profile = brain.database.users.find_by_stripe_customer_id(customer_id)
    
    # Fallback to metadata if customer ID mapping doesn't exist yet (race condition)
    if not profile:
        user_email = subscription.get("metadata", {}).get("user_email")
        if user_email:
            logger.info("Customer %s not found in DB. Falling back to metadata email: %s", customer_id, user_email)
            profile = brain.get_user_profile(user_email)
            # If found by email, ensure we link the customer ID now
            if profile:
                brain.update_user_profile_fields(user_email, {"stripe_customer_id": customer_id})

    if profile:
        c_ts = subscription.get("current_period_start", datetime.now().timestamp())
        cycle_start = datetime.fromtimestamp(c_ts, tz=timezone.utc)
        cycle_start_iso = cycle_start.isoformat()

        # Check if we need to reset the counter
        # 1. Plan changed (upgrade/downgrade)
        # 2. Billing cycle start changed (new month)
        # 3. Was Free, now is something else
        plan_changed = profile.subscription_plan != plan
        cycle_changed = profile.current_billing_cycle_start != cycle_start_iso
        
        updates = {
            "stripe_subscription_id": subscription["id"],
            "stripe_subscription_status": status,
            "subscription_plan": plan,
            "current_billing_cycle_start": cycle_start_iso,
            "custom_message_limit": None,
        }
        
        if plan_changed or cycle_changed:
            logger.info("Resetting message counter for user %s. Plan changed: %s, Cycle changed: %s", 
                        profile.email, plan_changed, cycle_changed)
            updates["messages_sent_this_month"] = 0

        brain.update_user_profile_fields(profile.email, updates)
    else:
        logger.error("Could not find user profile for customer_id: %s or metadata email", customer_id)


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
