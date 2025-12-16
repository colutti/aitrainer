"""
This module contains the dependency injection for the application.
"""
import functools
from mem0 import Memory
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import settings
from src.core.logs import logger
from src.services.database import MongoDatabase
from src.services.trainer import AITrainerBrain


def get_mem0_client() -> Memory:
    """
    Returns a MEM0 client.
    """
    memory = Memory.from_config(settings.get_mem0_config())
    return memory


def get_llm():
    """
    Returns a Google Generative AI chat model.
    """
    logger.info("Instantiating Gemini LLM with model: %s", settings.LLM_MODEL_NAME)
    return ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL_NAME,
        google_api_key=settings.GEMINI_API_KEY or "",
        temperature=settings.LLM_TEMPERATURE,
    )


...

@functools.lru_cache()
def get_mongo_database():
    """
    Returns a MongoDB database client.
    """
    return MongoDatabase()


def get_ai_trainer_brain():
    """
    Returns an AI trainer brain.
    """
    llm = get_llm()
    memory_client = get_mem0_client()
    database = get_mongo_database()
    return AITrainerBrain(llm=llm, memory=memory_client, database=database)
