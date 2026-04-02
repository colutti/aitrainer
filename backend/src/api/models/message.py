"""
This module contains the models for chat message requests.
"""

import base64

from pydantic import BaseModel, Field, field_validator, model_validator

MAX_IMAGE_SIZE_BYTES = 3 * 1024 * 1024
MAX_IMAGES_PER_MESSAGE = 4
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


class MessageImageInput(BaseModel):
    """Single image payload for multimodal chat input."""

    base64_data: str = Field(alias="base64", min_length=1, max_length=8_000_000)
    mime_type: str = Field(pattern=r"^image/(jpeg|png|webp)$")

    @field_validator("mime_type")
    @classmethod
    def validate_mime_type(cls, value: str) -> str:
        """Ensure MIME type is one of the allowed image formats."""
        if value not in ALLOWED_IMAGE_MIME_TYPES:
            raise ValueError("INVALID_IMAGE_TYPE")
        return value

    @field_validator("base64_data")
    @classmethod
    def validate_base64_size(cls, value: str) -> str:
        """Validate base64 format and enforce max decoded image size."""
        try:
            decoded = base64.b64decode(value, validate=True)
        except (ValueError, TypeError) as exc:
            raise ValueError("INVALID_IMAGE_BASE64") from exc
        if len(decoded) > MAX_IMAGE_SIZE_BYTES:
            raise ValueError("IMAGE_TOO_LARGE")
        return value


class MessageRequest(BaseModel):
    """
    Represents a request containing a user's message.

    Attributes:
        user_message (str): The message provided by the user (max 5000 chars).
    """

    user_message: str = Field("", max_length=5000)
    images: list[MessageImageInput] | None = Field(default=None)
    # Backward compatibility for older frontend payload
    image_base64: str | None = Field(default=None, max_length=8_000_000)
    image_mime_type: str | None = Field(
        default=None, pattern=r"^image/(jpeg|png|webp)$"
    )

    @model_validator(mode="after")
    def normalize_and_validate(self):
        """Normalize legacy payload fields and enforce request constraints."""
        normalized = list(self.images or [])
        if self.image_base64 and self.image_mime_type:
            normalized.append(
                MessageImageInput(base64=self.image_base64, mime_type=self.image_mime_type)
            )
        if normalized and len(normalized) > MAX_IMAGES_PER_MESSAGE:
            raise ValueError("TOO_MANY_IMAGES")
        user_message = self.user_message if isinstance(self.user_message, str) else ""
        if not user_message.strip() and not normalized:
            raise ValueError("EMPTY_MESSAGE")
        self.images = normalized or None
        return self
