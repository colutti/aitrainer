"""
Invite model for user onboarding system.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class InviteCreate(BaseModel):
    """
    Request model for creating a new invite.
    """
    email: EmailStr = Field(..., description="Email address for the invite")
    expires_hours: int = Field(
        default=72,
        ge=1,
        le=168,
        description="Number of hours until invite expires (1-168 hours)"
    )


class Invite(BaseModel):
    """
    Complete invite model stored in database.
    """
    token: str = Field(..., description="Unique UUID4 token for the invite")
    email: EmailStr = Field(..., description="Email address associated with invite")
    created_at: datetime = Field(..., description="Timestamp when invite was created")
    expires_at: datetime = Field(..., description="Timestamp when invite expires")
    used: bool = Field(default=False, description="Whether invite has been used")
    used_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when invite was used"
    )


class InviteResponse(BaseModel):
    """
    Response model when creating an invite.
    """
    invite_token: str = Field(..., description="The unique invite token")
    onboarding_url: str = Field(..., description="Complete URL for onboarding")
    expires_at: datetime = Field(..., description="Expiration timestamp")
