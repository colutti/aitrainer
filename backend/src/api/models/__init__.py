from .sender import Sender
from .user_profile import UserProfileInput, UserProfile
from .trainer_profile import TrainerProfileInput, TrainerProfile
from .auth import LoginRequest
from .message import MessageRequest
from .chat_history import ChatHistory

__all__ = [
    "Sender",
    "UserProfileInput",
    "UserProfile",
    "TrainerProfileInput",
    "TrainerProfile",
    "LoginRequest",
    "MessageRequest",
    "ChatHistory",
]
