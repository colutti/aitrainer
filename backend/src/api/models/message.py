"""
This module contains the models for chat message requests.
"""

from pydantic import BaseModel


class MessageRequest(BaseModel):
    """
    Represents a request containing a user's message.

    Attributes:
        user_message (str): The message provided by the user.
    """

    user_message: str
