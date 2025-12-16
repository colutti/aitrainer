from .config import settings
from mem0 import Memory
from .logs import logger
from langchain_google_genai import ChatGoogleGenerativeAI
from .database import MongoDatabase


def get_mem0_client() -> Memory:
    memory = Memory.from_config(settings.MEM0_CONFIG)
    return memory


def get_llm():
    logger.info("Instantiating Gemini LLM with model: %s", settings.LLM_MODEL_NAME)
    return ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL_NAME,
        google_api_key=settings.GEMINI_API_KEY or "",
        temperature=0.7,
    )


def get_mongo_database():
    return MongoDatabase()
