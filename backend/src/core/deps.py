"""
This module contains the dependency injection for the application.
"""

import functools
from mem0 import Memory  # type: ignore
from qdrant_client import QdrantClient

from src.core.config import settings
from src.services.database import MongoDatabase
from src.services.llm_client import LLMClient
from src.services.trainer import AITrainerBrain
from src.services.hevy_service import HevyService


@functools.lru_cache()
def get_mem0_client() -> Memory:
    """
    Returns a MEM0 client.
    """
    memory = Memory.from_config(settings.get_mem0_config())
    return memory


@functools.lru_cache()
def get_qdrant_client() -> QdrantClient:
    """
    Returns a Qdrant client for direct memory access with pagination.
    """
    if settings.QDRANT_HOST.startswith("http"):
        # If host contains protocol, it's a URL (like Qdrant Cloud)
        url = settings.QDRANT_HOST
        if str(settings.QDRANT_PORT) not in url:
            url = f"{url}:{settings.QDRANT_PORT}"

        return QdrantClient(url=url, api_key=settings.QDRANT_API_KEY)

    # Local/Self-hosted without protocol in host
    return QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
    )


@functools.lru_cache()
def get_llm_client() -> LLMClient:
    """
    Returns the configured LLM client (Gemini or Ollama).
    Uses factory method that reads settings.AI_PROVIDER.
    """
    return LLMClient.from_config()


@functools.lru_cache()
def get_mongo_database() -> MongoDatabase:
    """
    Returns a MongoDB database client.
    """
    return MongoDatabase()


@functools.lru_cache()
def get_ai_trainer_brain() -> AITrainerBrain:
    """
    Returns an AI trainer brain.
    """
    llm_client = get_llm_client()
    memory_client = get_mem0_client()
    database = get_mongo_database()
    return AITrainerBrain(
        llm_client=llm_client, memory=memory_client, database=database
    )


@functools.lru_cache()
def get_hevy_service() -> HevyService:
    """
    Returns a Hevy service instance.
    """
    database = get_mongo_database()
    return HevyService(workout_repository=database.workouts_repo)


def get_telegram_repository():
    """
    Returns a Telegram repository instance.
    """
    from src.repositories.telegram_repository import TelegramRepository

    database = get_mongo_database()
    return TelegramRepository(database.database)


def get_telegram_service():
    """
    Returns a Telegram bot service instance.
    """
    from src.services.telegram_service import TelegramBotService

    if not settings.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not configured")

    repository = get_telegram_repository()
    brain = get_ai_trainer_brain()

    return TelegramBotService(
        token=settings.TELEGRAM_BOT_TOKEN, repository=repository, brain=brain
    )
