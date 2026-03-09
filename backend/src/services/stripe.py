import stripe
from src.core.config import settings
from src.api.models.user_profile import UserProfile
from src.core.logs import logger

stripe.api_key = settings.STRIPE_API_KEY

def create_checkout_session(user: UserProfile, price_id: str, success_url: str, cancel_url: str) -> str:
    """
    Creates a Stripe Checkout session for a user.
    """
    try:
        session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            customer_email=user.email if not user.stripe_customer_id else None,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                },
            ],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_email": user.email
            }
        )
        return session.url
    except Exception as e:
        logger.error(f"Error creating Stripe checkout session: {e}")
        raise e

def create_customer_portal_session(customer_id: str, return_url: str) -> str:
    """
    Creates a Stripe Customer Portal session.
    """
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session.url
    except Exception as e:
        logger.error(f"Error creating Stripe portal session: {e}")
        raise e
