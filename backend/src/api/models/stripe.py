"""
Stripe model definitions.
"""

from pydantic import BaseModel, Field


class CheckoutSessionRequest(BaseModel):
    """Request model for creating a Stripe checkout session."""

    price_id: str = Field(..., description="Stripe Price ID")
    success_url: str = Field(..., description="URL to redirect on success")
    cancel_url: str = Field(..., description="URL to redirect on cancellation")


class PortalSessionRequest(BaseModel):
    """Request model for creating a Stripe customer portal session."""

    return_url: str = Field(..., description="URL to redirect back from the portal")
