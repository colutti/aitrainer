"""
This module contains the dependency injection for the application.
"""
import functools
from mem0 import Memory

from src.core.config import settings
from src.services.database import MongoDatabase
from src.services.llm_client import LLMClient
from src.services.trainer import AITrainerBrain


@functools.lru_cache()
def get_mem0_client() -> Memory:
    """
    Returns a MEM0 client.
    """
    memory = Memory.from_config(settings.get_mem0_config())
    return memory


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


def get_ai_trainer_brain() -> AITrainerBrain:
    """
    Returns an AI trainer brain.
    """
    llm_client = get_llm_client()
    memory_client = get_mem0_client()
    database = get_mongo_database()
    return AITrainerBrain(llm_client=llm_client, memory=memory_client, database=database)
