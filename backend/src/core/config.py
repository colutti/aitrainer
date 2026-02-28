"""
This module contains the configuration settings for the application.
"""

import logging
import os

from pydantic import ValidationError, field_validator, model_validator, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from src.core.logs import logger
from src.prompts.prompt_template import PROMPT_TEMPLATE
from src.prompts.mem0_prompt import MEM0_FACT_EXTRACTION_PROMPT


class Settings(BaseSettings):
    """
    Settings class for the application, using pydantic-settings.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", frozen=True
    )

    @classmethod
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """
        Customizes configuration source priority.
        """
        if os.getenv("RUNNING_IN_CONTAINER") == "true":
            return init_settings, env_settings, dotenv_settings, file_secret_settings

        # Local scripts default safety
        return init_settings, dotenv_settings, env_settings, file_secret_settings

    # ====== API CONFIGURATION ======
    SECRET_KEY: str = Field(default="dummy_secret_key")
    API_SERVER_PORT: int = 8000

    MAX_SHORT_TERM_MEMORY_MESSAGES: int = 20
    COMPACTION_THRESHOLD: int = 60  # Must be > MAX_SHORT_TERM_MEMORY_MESSAGES (the active window size)
    MAX_LONG_TERM_MEMORY_MESSAGES: int = Field(default=50)
    SUMMARY_MAX_TOKEN_LIMIT: int = 200
    ALLOWED_ORIGINS: str | list[str] = Field(default="*")
    LOG_LEVEL: str = "INFO"
    RATE_LIMIT_LOGIN: str = "5/minute"
    MAX_PROMPT_LOGS: int = 20

    # ====== BETTERSTACK INTEGRATION ======
    BETTERSTACK_API_TOKEN: str = ""
    BETTERSTACK_SOURCE_ID: str = ""

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        """
        Validates and parses ALLOWED_ORIGINS.
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        return v  # type: ignore

    @model_validator(mode="after")
    def validate_compaction_config(self) -> "Settings":
        """Ensures COMPACTION_THRESHOLD is always above the active window size."""
        if self.COMPACTION_THRESHOLD <= self.MAX_SHORT_TERM_MEMORY_MESSAGES:
            raise ValueError(
                f"COMPACTION_THRESHOLD ({self.COMPACTION_THRESHOLD}) must be greater than "
                f"MAX_SHORT_TERM_MEMORY_MESSAGES ({self.MAX_SHORT_TERM_MEMORY_MESSAGES}). "
                "Compaction would never fire otherwise."
            )
        return self

    # ====== AI PROVIDER SELECTION ======
    AI_PROVIDER: str = "gemini"

    # ====== GEMINI STUFF ========
    GEMINI_API_KEY: str = ""
    GEMINI_LLM_MODEL: str = "gemini-1.5-flash"
    GEMINI_EMBEDDER_MODEL: str = "gemini-embedding-001"
    LLM_TEMPERATURE: float = 0.4
    EMBEDDING_MODEL_DIMS: int = 768
    PROMPT_TEMPLATE: str = PROMPT_TEMPLATE

    # ====== OLLAMA STUFF ======
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_LLM_MODEL: str = "llama3-groq-tool-use:8b"
    OLLAMA_EMBEDDER_MODEL: str = "nomic-embed-text:latest"

    # ====== OPENAI STUFF ======
    OPENAI_API_KEY: str = ""
    OPENAI_LLM_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDER_MODEL: str = "text-embedding-3-small"

    # ====== MONGO STUFF ======
    DB_NAME: str = Field(default="aitrainer")
    MONGO_URI: str = Field(default="mongodb://localhost:27017")

    @field_validator("MONGO_URI", mode="before")
    @classmethod
    def strip_quotes(cls, v: str) -> str:
        """Strips quotes from the MONGO_URI string."""
        if isinstance(v, str):
            return v.strip('"')
        return v

    # ====== QDRANT AND MEM0 STUFF ======
    # pylint: disable=no-member
    QDRANT_HOST: str = Field(default="localhost")
    QDRANT_PORT: int = Field(default=6333)
    QDRANT_COLLECTION_NAME: str = Field(default="aitrainer_memories")
    QDRANT_API_KEY: str = Field(default="local_dummy_key")

    # ====== MEM0 MEMORY OPTIMIZATION ======
    MEM0_CRITICAL_LIMIT: int = 4
    MEM0_SEMANTIC_LIMIT: int = 5
    MEM0_RECENT_LIMIT: int = 3
    MEM0_SEMANTIC_DEDUP_THRESHOLD: float = 0.85
    MEM0_MAX_CONTEXT_SIZE: int = 1024
    MEM0_DATE_THRESHOLD_DAYS: int = 7

    # ====== TELEGRAM STUFF ======
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""

    def get_mem0_config(self) -> dict:
        """
        Generates the configuration dictionary for Mem0.
        """
        llm_config = {
            "provider": self.AI_PROVIDER,
            "config": {
                "temperature": self.LLM_TEMPERATURE,
                "max_tokens": 2000,
            },
        }

        embedder_config = {"provider": self.AI_PROVIDER, "config": {}}
        embedding_dims = self.EMBEDDING_MODEL_DIMS

        if self.AI_PROVIDER == "gemini":
            llm_config["config"].update(
                {
                    "model": self.GEMINI_LLM_MODEL,
                    "api_key": self.GEMINI_API_KEY,
                }
            )
            embedder_config["config"].update(
                {
                    "model": self.GEMINI_EMBEDDER_MODEL,
                    "api_key": self.GEMINI_API_KEY,
                }
            )
        elif self.AI_PROVIDER == "ollama":
            llm_config["config"].update(
                {
                    "model": self.OLLAMA_LLM_MODEL,
                    "ollama_base_url": self.OLLAMA_BASE_URL,
                }
            )
            embedder_config["config"].update(
                {
                    "model": self.OLLAMA_EMBEDDER_MODEL,
                    "embedding_dims": embedding_dims,
                    "ollama_base_url": self.OLLAMA_BASE_URL,
                }
            )
        elif self.AI_PROVIDER == "openai":
            llm_config["config"].update(
                {
                    "model": self.OPENAI_LLM_MODEL,
                    "api_key": self.OPENAI_API_KEY,
                }
            )
            embedder_config["config"].update(
                {
                    "model": self.OPENAI_EMBEDDER_MODEL,
                    "api_key": self.OPENAI_API_KEY,
                    "embedding_dims": embedding_dims,
                }
            )

        qdrant_config = {
            "collection_name": self.QDRANT_COLLECTION_NAME,
            "embedding_model_dims": embedding_dims,
            "api_key": self.QDRANT_API_KEY
            if self.QDRANT_API_KEY != "local_dummy_key"
            else None,
        }

        if self.QDRANT_HOST.startswith("http"):
            if str(self.QDRANT_PORT) not in self.QDRANT_HOST:
                qdrant_config["url"] = f"{self.QDRANT_HOST}:{self.QDRANT_PORT}"
            else:
                qdrant_config["url"] = self.QDRANT_HOST
        else:
            qdrant_config["host"] = self.QDRANT_HOST
            qdrant_config["port"] = self.QDRANT_PORT

        return {
            "vector_store": {
                "provider": "qdrant",
                "config": qdrant_config,
            },
            "llm": llm_config,
            "embedder": embedder_config,
            "custom_prompt": MEM0_FACT_EXTRACTION_PROMPT,
            "version": "v1.1",
        }


# Instanciação segura
try:
    settings = Settings()  # type: ignore
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
except ValidationError as validation_error:
    logger.critical("CRITICAL ERROR: Missing environment variables in .env file!")
    logger.critical(validation_error)
