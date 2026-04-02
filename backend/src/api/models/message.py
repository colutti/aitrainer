"""
This module contains the models for chat message requests.
"""

from pydantic import BaseModel, Field


class MessageRequest(BaseModel):
    """
    Represents a request containing a user's message.

    Attributes:
        user_message (str): The message provided by the user (max 5000 chars).
    """

    user_message: str = Field(..., min_length=1, max_length=5000)
    image_base64: str | None = Field(default=None, max_length=8_000_000)
    image_mime_type: str | None = Field(
        default=None, pattern=r"^image/(jpeg|png|webp)$"
    )
