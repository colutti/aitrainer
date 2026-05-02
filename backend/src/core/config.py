"""
This module contains the configuration settings for the application.
"""

import logging
import os
from typing import Any

from pydantic import ValidationError, field_validator, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from src.core.logs import logger

_CRITICAL_RUNTIME_ENV_VARS = (
    "SECRET_KEY",
    "DB_NAME",
    "MONGO_URI",
    "QDRANT_HOST",
    "QDRANT_COLLECTION_NAME",
    "QDRANT_API_KEY",
    "OPENROUTER_API_KEY",
    "OPENROUTER_BASE_URL",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_WEBHOOK_SECRET",
    "STRIPE_API_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "STRIPE_PRICE_ID_BASIC",
    "STRIPE_PRICE_ID_PRO",
)


def validate_required_runtime_config(current_settings: Any) -> None:
    """Fail fast when required runtime config is missing or placeholder-like."""
    missing = []
    placeholder = []
    for key in _CRITICAL_RUNTIME_ENV_VARS:
        value = getattr(current_settings, key, "")
        if not isinstance(value, str) or not value.strip():
            missing.append(key)
            continue
        if "CHANGE_ME" in value or "change_me" in value:
            placeholder.append(key)

    errors = []
    if missing:
        errors.append(f"missing required runtime vars: {', '.join(missing)}")
    if placeholder:
        errors.append(f"placeholder runtime vars: {', '.join(placeholder)}")
    if errors:
        raise ValueError("; ".join(errors))


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
    SECRET_KEY: str = Field(default="")
    API_SERVER_PORT: int = 8000

    MAX_SHORT_TERM_MEMORY_MESSAGES: int = 50
    MAX_LONG_TERM_MEMORY_MESSAGES: int = Field(default=50)
    LLM_STREAM_TIMEOUT_SECONDS: int = Field(default=120)
    LLM_STREAM_INACTIVITY_TIMEOUT_SECONDS: int = Field(default=45)
    LLM_AGENT_RECURSION_LIMIT: int = Field(default=20)
    AI_TRAINER_THREADPOOL_WORKERS: int = Field(default=4)
    WARMUP_AI_ON_STARTUP: bool = Field(default=False)
    ENABLE_EXPERIMENTAL_CONVERSATION_GRAPH: bool = Field(default=True)
    ALLOWED_ORIGINS: str | list[str] = Field(default="*")
    LOG_LEVEL: str = "INFO"
    RATE_LIMIT_LOGIN: str = "5/minute"
    MAX_PROMPT_LOGS: int = 20
    LANGSMITH_TRACING: bool = False
    LANGSMITH_TRACING_ENABLED: bool = False
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_WORKSPACE_ID: str = ""
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGSMITH_PROJECT: str = ""
    LANGSMITH_ENVIRONMENT: str = "local"
    LANGSMITH_SAMPLE_RATE: float = 1.0

    # ====== BETTERSTACK INTEGRATION ======
    BETTERSTACK_API_TOKEN: str = ""
    BETTERSTACK_SOURCE_ID: str = ""

    # ====== FIREBASE INTEGRATION ======
    FIREBASE_CREDENTIALS: str | None = None
    FIREBASE_CLOCK_SKEW_SECONDS: int = 60
    ENABLE_E2E_TEST_AUTH: bool = False
    ENABLE_NEW_USER_SIGNUPS: bool = False

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        """
        Validates and parses ALLOWED_ORIGINS.
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        return v  # type: ignore

    # ====== OPENROUTER ======
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_CHAT_MODEL: str = ""
    OPENROUTER_PROMPT_PRESET: str = ""
    OPENROUTER_EMBED_MODEL: str = "openai/text-embedding-3-small"
    OPENROUTER_EMBED_DIMENSIONS: int = 768
    PROMPT_CONTEXT_CONTRACT_VERSION: str = "prompt_context_v1"

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
    QDRANT_API_KEY: str = Field(default="")

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

    # ====== STRIPE ======
    STRIPE_API_KEY: str = ""
    STRIPE_API_BASE: str = "https://api.stripe.com"
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_BASIC: str = ""
    STRIPE_PRICE_ID_PRO: str = ""
    STRIPE_PRICE_ID_PREMIUM: str = ""

# Instanciação segura
try:
    settings = Settings()  # type: ignore
    validate_required_runtime_config(settings)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
except (ValidationError, ValueError) as validation_error:
    logger.critical("CRITICAL ERROR: Missing environment variables in .env file!")
    logger.critical(validation_error)
