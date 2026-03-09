import stripe
from fastapi import APIRouter, Header, Request, HTTPException, Depends
from src.core.config import settings
from src.api.endpoints.user import CurrentUser, AITrainerBrainDep
from src.services.stripe import create_checkout_session, create_customer_portal_session
from src.core.logs import logger
from datetime import datetime, timezone

router = APIRouter()

@router.post("/create-checkout-session")
async def checkout_session(
    price_id: str,
    success_url: str,
    cancel_url: str,
    user_email: CurrentUser,
    brain: AITrainerBrainDep
):
    profile = brain.get_user_profile(user_email)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        url = create_checkout_session(profile, price_id, success_url, cancel_url)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-portal-session")
async def portal_session(
    return_url: str,
    user_email: CurrentUser,
    brain: AITrainerBrainDep
):
    profile = brain.get_user_profile(user_email)
    if not profile or not profile.stripe_customer_id:
        raise HTTPException(status_code=400, detail="User has no Stripe customer ID")
    
    try:
        url = create_customer_portal_session(profile.stripe_customer_id, return_url)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    brain: AITrainerBrainDep,
    stripe_signature: str = Header(None)
):
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return {"status": "invalid payload"}
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    logger.info(f"Stripe Webhook received: {event['type']}")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_email = session.get("metadata", {}).get("user_email")
        customer_id = session.get("customer")
        if user_email:
            brain.update_user_profile_fields(user_email, {"stripe_customer_id": customer_id})

    elif event["type"] in ["customer.subscription.created", "customer.subscription.updated"]:
        subscription = event["data"]["object"]
        customer_id = subscription.get("customer")
        status = subscription.get("status")
        price_id = subscription["items"]["data"][0]["price"]["id"]
        
        # Map Price ID to Plan
        plan = "Free"
        if price_id == settings.STRIPE_PRICE_ID_BASIC:
            plan = "Basic"
        elif price_id == settings.STRIPE_PRICE_ID_PRO:
            plan = "Pro"
        elif price_id == settings.STRIPE_PRICE_ID_PREMIUM:
            plan = "Premium"
        else:
            logger.warning(f"Unknown Stripe price ID received: {price_id}. Enforcing 'Free' fallback.")
            
        user = brain.database.users.find_one({"stripe_customer_id": customer_id})
        if user:
            # Note: We must be careful about trials here. If status == 'trialing', we might want 
            # to handle trial expirations via Stripe instead of local Mongo custom_trial_days logic
            brain.update_user_profile_fields(user["email"], {
                "stripe_subscription_id": subscription["id"],
                "stripe_subscription_status": status,
                "subscription_plan": plan,
                "current_billing_cycle_start": datetime.now(timezone.utc).isoformat(),
                "custom_message_limit": None # Clear custom limits when plan changes
            })

    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        customer_id = subscription.get("customer")
        user = brain.database.users.find_one({"stripe_customer_id": customer_id})
        if user:
            brain.update_user_profile_fields(user["email"], {
                "stripe_subscription_status": "canceled",
                "subscription_plan": "Free"
            })

    return {"status": "success"}
