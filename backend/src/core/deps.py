"""
This module contains the dependency injection for the application.
"""
import functools
from mem0 import Memory
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from src.core.config import settings
from src.core.logs import logger
from src.services.database import MongoDatabase
from src.services.trainer import AITrainerBrain


@functools.lru_cache()
def get_mem0_client() -> Memory:
    """
    Returns a MEM0 client.
    """
    memory = Memory.from_config(settings.get_mem0_config())
    return memory


@functools.lru_cache()
def get_llm() -> BaseChatModel:
    """
    Returns the configured chat model (Gemini or Ollama).
    """
    if settings.AI_PROVIDER == "ollama":
        logger.info("Instantiating Ollama LLM with model: %s at %s", 
                    settings.OLLAMA_LLM_MODEL, settings.OLLAMA_BASE_URL)
        return ChatOllama(
            model=settings.OLLAMA_LLM_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=settings.LLM_TEMPERATURE,
        )
    
    logger.info("Instantiating Gemini LLM with model: %s", settings.LLM_MODEL_NAME)
    return ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL_NAME,
        google_api_key=settings.GEMINI_API_KEY or "",
        temperature=settings.LLM_TEMPERATURE,
    )


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
    llm = get_llm()
    memory_client = get_mem0_client()
    database = get_mongo_database()
    return AITrainerBrain(llm=llm, memory=memory_client, database=database)

