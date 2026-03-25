"""Stripe integration service."""

import stripe
from stripe.checkout import Session as CheckoutSession  # type: ignore
from stripe.billing_portal import Session as PortalSession  # type: ignore

try:
    from stripe.error import StripeError  # type: ignore
except ImportError:
    # Some versions might have it elsewhere or not easily accessible via Pyright
    from stripe import StripeError  # type: ignore # pylint: disable=ungrouped-imports
from src.core.config import settings
from src.api.models.user_profile import UserProfile
from src.core.logs import logger

stripe.api_key = settings.STRIPE_API_KEY  # type: ignore


def create_checkout_session(
    user: UserProfile, price_id: str, success_url: str, cancel_url: str
) -> str:
    """
    Creates a Stripe Checkout session for a user.
    """
    try:
        session = CheckoutSession.create(
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
            metadata={"user_email": user.email},
            subscription_data={"metadata": {"user_email": user.email}},
        )
        return str(session.url)
    except (ValueError, TypeError, AttributeError, StripeError) as e:
        logger.error("Error creating Stripe checkout session: %s", e)
        raise


def create_customer_portal_session(customer_id: str, return_url: str) -> str:
    """
    Creates a Stripe Customer Portal session.
    """
    try:
        session = PortalSession.create(
            customer=customer_id,
            return_url=return_url,
        )
        return str(session.url)
    except (ValueError, TypeError, AttributeError, StripeError) as e:
        logger.error("Error creating Stripe portal session: %s", e)
        raise
