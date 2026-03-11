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
