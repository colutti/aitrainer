from pydantic import ValidationError, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from src.core.logs import logger
from src.prompts.prompt_template import PROMPT_TEMPLATE


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", frozen=True
    )

    @classmethod
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

        If running in a container (RUNNING_IN_CONTAINER=true):
            Prioritize Docker environment variables (env_settings) over .env file.
            Order: Init > Env > DotEnv

        If running locally (scripts):
            Prioritize .env file over shell environment variables to prevent accidents.
            Order: Init > DotEnv > Env
        """
        import os

        if os.getenv("RUNNING_IN_CONTAINER") == "true":
            return init_settings, env_settings, dotenv_settings, file_secret_settings

        # Local scripts default safety
        return init_settings, dotenv_settings, env_settings, file_secret_settings

    # ====== API CONFIGURATION ======
    SECRET_KEY: str
    API_SERVER_PORT: int = 8000

    MAX_SHORT_TERM_MEMORY_MESSAGES: int = 20  # Reduced for token efficiency, with lazy expansion
    MAX_LONG_TERM_MEMORY_MESSAGES: int
    SUMMARY_MAX_TOKEN_LIMIT: int = 200  # Trigger summarization when buffer exceeds this
    ALLOWED_ORIGINS: str | list[str]
    LOG_LEVEL: str = "INFO"
    RATE_LIMIT_LOGIN: str = "5/minute"  # Rate limit for login endpoint
    MAX_PROMPT_LOGS: int = 20  # Number of LLM prompts to keep per user

    # ====== BETTERSTACK INTEGRATION ======
    BETTERSTACK_API_TOKEN: str = ""
    BETTERSTACK_SOURCE_ID: str = ""

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        """
        Validates and parses ALLOWED_ORIGINS. Supports both JSON lists and comma-separated strings.
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        return v  # type: ignore

    # ====== AI PROVIDER SELECTION ======
    AI_PROVIDER: str = "gemini"  # Options: "ollama", "openai", "gemini"

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
    DB_NAME: str
    MONGO_URI: str
    
    @field_validator("MONGO_URI", mode="before")
    @classmethod
    def strip_quotes(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip('\"')
        return v

    # ====== QDRANT AND MEM0 STUFF ======
    QDRANT_HOST: str
    QDRANT_PORT: int
    QDRANT_COLLECTION_NAME: str
    QDRANT_API_KEY: str

    # ====== MEM0 MEMORY OPTIMIZATION ======
    MEM0_CRITICAL_LIMIT: int = 4  # Reduced from 10 for cost optimization
    MEM0_SEMANTIC_LIMIT: int = 5  # Reduced from 10 for cost optimization
    MEM0_RECENT_LIMIT: int = 3  # Reduced from 10 for cost optimization
    MEM0_SEMANTIC_DEDUP_THRESHOLD: float = 0.85  # Similarity threshold for deduplication
    MEM0_MAX_CONTEXT_SIZE: int = 1024  # Max bytes for memory context (1KB)
    MEM0_DATE_THRESHOLD_DAYS: int = 7  # Hide dates for memories < N days old

    # ====== TELEGRAM STUFF ======
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""

    def get_mem0_config(self):
        from src.prompts.mem0_prompt import MEM0_FACT_EXTRACTION_PROMPT

        llm_config = {
            "provider": self.AI_PROVIDER,
            "config": {
                "temperature": self.LLM_TEMPERATURE,
                "max_tokens": 2000,
            },
        }

        embedder_config = {"provider": self.AI_PROVIDER, "config": {}}

        # Set embedding dimensions based on provider
        embedding_dims = self.EMBEDDING_MODEL_DIMS  # Default: 768

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
            # Use 768 dims for compatibility with existing Qdrant collection
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
                    "embedding_dims": embedding_dims,  # 768 to match Qdrant
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
            # If the host contains protocol, treat it as a URL
            # If port is not already in the URL, append it
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

    # MONGO_URI previously computed field removed, now a direct variable


# Instanciação segura
try:
    settings = Settings()  # type: ignore
    # Sincroniza o nível de log definitivo a partir do que foi carregado no Settings
    import logging

    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
except ValidationError as e:
    from src.core.logs import logger

    logger.critical("CRITICAL ERROR: Missing environment variables in .env file!")
    logger.critical(e)
    # During tests, we might want to suppress exit or raise error
    # sys.exit(1)
    pass
