"""
Stripe payment and webhook endpoints.
"""

from datetime import datetime, timezone
import stripe
from fastapi import APIRouter, Header, Request, HTTPException
from src.api.endpoints.user import AITrainerBrainDep
from src.core.config import settings
from src.core.demo_access import WritableCurrentUser
from src.services.stripe import create_checkout_session, create_customer_portal_session
from src.api.models.stripe import CheckoutSessionRequest, PortalSessionRequest
from src.core.logs import logger

router = APIRouter()


@router.post("/create-checkout-session")
async def checkout_session(
    request: CheckoutSessionRequest,
    user_email: WritableCurrentUser,
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
        raise HTTPException(
            status_code=500, detail="Error creating checkout session"
        ) from e


@router.post("/create-portal-session")
async def portal_session(
    request: PortalSessionRequest,
    user_email: WritableCurrentUser,
    brain: AITrainerBrainDep,
):
    """Create a Stripe customer portal session for a user."""
    profile = brain.get_user_profile(user_email)
    if not profile or not profile.stripe_customer_id:
        raise HTTPException(status_code=400, detail="User has no Stripe customer ID")

    try:
        url = create_customer_portal_session(
            profile.stripe_customer_id, request.return_url
        )
        return {"url": url}
    except Exception as e:
        logger.error("Error creating portal session: %s", e)
        raise HTTPException(
            status_code=500, detail="Error creating portal session"
        ) from e


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

    event_object = event.get("data", {}).get("object", {})
    logger.info(
        "Stripe Webhook received: type=%s event_id=%s customer=%s subscription=%s",
        event.get("type"),
        event.get("id"),
        event_object.get("customer"),
        event_object.get("id"),
    )

    if event["type"] == "checkout.session.completed":
        _handle_checkout_completed(event["data"]["object"], brain)
    elif event["type"] in [
        "customer.subscription.created",
        "customer.subscription.updated",
    ]:
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


def _get_subscription_plan(subscription):
    """Determines the subscription plan based on the price ID."""
    status = subscription.get("status")
    if status not in ["active", "trialing"]:
        return "Free"

    items = subscription.get("items", {}).get("data", [])
    if not items:
        return "Free"

    price_id = items[0]["price"]["id"]
    pro_price_ids = {
        settings.STRIPE_PRICE_ID_PRO,
        settings.STRIPE_PRICE_ID_PRO_USD,
        settings.STRIPE_PRICE_ID_PRO_BRL,
        settings.STRIPE_PRICE_ID_PRO_EUR,
    }
    pro_price_ids.discard("")
    if price_id in pro_price_ids:
        return "Pro"

    logger.warning("Unknown Stripe price ID received: %s. Fallback to Free.", price_id)
    return "Free"


def _find_profile_for_subscription(subscription, brain):
    """Finds user profile by customer ID or metadata email."""
    customer_id = subscription.get("customer")
    profile = brain.database.users.find_by_stripe_customer_id(customer_id)

    if not profile:
        user_email = subscription.get("metadata", {}).get("user_email")
        if user_email:
            logger.info(
                "Customer %s not in DB. Fallback to metadata email: %s",
                customer_id,
                user_email,
            )
            profile = brain.get_user_profile(user_email)
            if profile:
                brain.update_user_profile_fields(
                    user_email, {"stripe_customer_id": customer_id}
                )
    return profile


def _handle_subscription_updated(subscription, brain):
    """Handle subscription created/updated event."""
    customer_id = subscription.get("customer")
    status = subscription.get("status")

    if not subscription.get("items") or not subscription["items"].get("data"):
        logger.warning("Subscription %s has no items", subscription["id"])
        return

    plan = _get_subscription_plan(subscription)
    profile = _find_profile_for_subscription(subscription, brain)

    if not profile:
        logger.error(
            "Could not find profile for customer_id: %s or metadata email", customer_id
        )
        return

    c_ts = subscription.get("current_period_start", datetime.now().timestamp())
    cycle_start = datetime.fromtimestamp(c_ts, tz=timezone.utc)
    cycle_start_iso = cycle_start.isoformat()

    previous_cycle = profile.current_billing_cycle_start
    previous_cycle_dt = None
    if previous_cycle:
        if isinstance(previous_cycle, datetime):
            previous_cycle_dt = (
                previous_cycle.replace(tzinfo=timezone.utc)
                if previous_cycle.tzinfo is None
                else previous_cycle.astimezone(timezone.utc)
            )
        elif isinstance(previous_cycle, str):
            normalized_cycle = previous_cycle.replace("Z", "+00:00")
            previous_cycle_dt = datetime.fromisoformat(normalized_cycle)

    if previous_cycle_dt and cycle_start < previous_cycle_dt:
        logger.warning(
            "Ignoring stale subscription cycle for customer %s. Incoming: %s, Existing: %s",
            customer_id,
            cycle_start_iso,
            previous_cycle_dt.isoformat(),
        )
        cycle_start_iso = previous_cycle_dt.isoformat()
        cycle_changed = False
    else:
        cycle_changed = previous_cycle != cycle_start_iso

    plan_changed = profile.subscription_plan != plan

    updates = {
        "stripe_subscription_id": subscription["id"],
        "stripe_subscription_status": status,
        "subscription_plan": plan,
        "current_billing_cycle_start": cycle_start_iso,
        "custom_message_limit": None,
    }
    if plan == "Pro":
        updates["trial_ends_at"] = None

    if plan_changed or cycle_changed:
        logger.info(
            "Resetting counters for user %s. Plan changed: %s, Cycle changed: %s",
            profile.email,
            plan_changed,
            cycle_changed,
        )
        updates["messages_sent_this_month"] = 0
        updates["photos_sent_this_month"] = 0

        # Ensure trainer is allowed for the new plan
        brain.ensure_trainer_allowed(profile.email, plan)

    brain.update_user_profile_fields(profile.email, updates)


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
                "photos_sent_this_month": 0,
                "messages_sent_this_month": 0,
            },
        )
        # Reset trainer to Breno if they were using someone else
        brain.ensure_trainer_allowed(profile.email, "Free")
