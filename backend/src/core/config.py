import sys
from pydantic import ValidationError, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.logs import logger
from src.prompts.prompt_template import PROMPT_TEMPLATE

class Settings(BaseSettings):
    """
    Settings configuration class for application environment variables and service connections.

    Attributes:
        SECRET_KEY (str): Secret key for API authentication.
        API_SERVER_PORT (int): Port number for the API server.
        MAX_SHORT_TERM_MEMORY_MESSAGES (int): Maximum number of short-term memory messages.
        MAX_LONG_TERM_MEMORY_MESSAGES (int): Maximum number of long-term memory messages.

        GEMINI_API_KEY (str): API key for Gemini service.
        LLM_MODEL_NAME (str): Name of the large language model to use.
        EMBEDDER_MODEL_NAME (str): Name of the embedder model to use.
        PROMPT_TEMPLATE (str): Template string for prompts.

        DB_NAME (str): Name of the MongoDB database.
        MONGO_INITDB_ROOT_USERNAME (str): MongoDB root username.
        MONGO_INITDB_ROOT_PASSWORD (str): MongoDB root password.
        MONGO_HOST (str): MongoDB host address.
        MONGO_PORT (int): MongoDB port number.

        QDRANT_HOST (str): Qdrant vector store host address.
        QDRANT_PORT (int): Qdrant vector store port number.
        QDRANT_COLLECTION_NAME (str): Name of the Qdrant collection.
        QDRANT_API_KEY (str): API key for Qdrant.

    Properties:
        MEM0_CONFIG (dict): Configuration dictionary for MEM0, including vector store, LLM, and embedder settings.
        MONGO_URI (str): Computed MongoDB connection URI string.
    """
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ====== API CONFIGURATION ======
    SECRET_KEY: str
    API_SERVER_PORT: int
    MAX_SHORT_TERM_MEMORY_MESSAGES: int
    MAX_LONG_TERM_MEMORY_MESSAGES: int

    # ====== AI PROVIDER SELECTION ======
    AI_PROVIDER: str = "gemini"  # Options: "ollama", "openai", "gemini"

    # ====== GEMINI STUFF ======
    GEMINI_API_KEY: str = ""
    LLM_MODEL_NAME: str = "gemini-1.5-flash"
    EMBEDDER_MODEL_NAME: str = "text-embedding-004"
    LLM_TEMPERATURE: float = 0.2
    EMBEDDING_MODEL_DIMS: int = 768
    PROMPT_TEMPLATE: str = PROMPT_TEMPLATE

    # ====== OLLAMA STUFF ======
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_LLM_MODEL: str = "llama3-groq-tool-use:8b"
    OLLAMA_EMBEDDER_MODEL: str = "nomic-embed-text:latest"

    # ====== OPENAI STUFF ======
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL_NAME: str = "gpt-4o-mini"

    # ====== MONGO STUFF ======
    DB_NAME: str
    MONGO_INITDB_ROOT_USERNAME: str
    MONGO_INITDB_ROOT_PASSWORD: str
    MONGO_HOST: str
    MONGO_PORT: int

    # ====== QDRANT AND MEM0 STUFF ======
    QDRANT_HOST: str
    QDRANT_PORT: int
    QDRANT_COLLECTION_NAME: str
    QDRANT_API_KEY: str

    def get_mem0_config(self):
        llm_config = {
            "provider": self.AI_PROVIDER,
            "config": {
                "temperature": self.LLM_TEMPERATURE,
                "max_tokens": 2000,
            }
        }

        embedder_config = {
            "provider": self.AI_PROVIDER,
            "config": {}
        }

        # Set embedding dimensions based on provider
        embedding_dims = self.EMBEDDING_MODEL_DIMS  # Default: 768

        if self.AI_PROVIDER == "gemini":
            llm_config["config"].update({
                "model": self.LLM_MODEL_NAME,
                "api_key": self.GEMINI_API_KEY,
            })
            embedder_config["config"].update({
                "model": self.EMBEDDER_MODEL_NAME,
                "api_key": self.GEMINI_API_KEY,
            })
        elif self.AI_PROVIDER == "ollama":
            llm_config["config"].update({
                "model": self.OLLAMA_LLM_MODEL,
                "ollama_base_url": self.OLLAMA_BASE_URL,
            })
            embedder_config["config"].update({
                "model": self.OLLAMA_EMBEDDER_MODEL,
                "embedding_dims": embedding_dims,
                "ollama_base_url": self.OLLAMA_BASE_URL,
            })
        elif self.AI_PROVIDER == "openai":
            # Use 768 dims for compatibility with existing Qdrant collection
            llm_config["config"].update({
                "model": self.OPENAI_MODEL_NAME,
                "api_key": self.OPENAI_API_KEY,
            })
            embedder_config["config"].update({
                "model": "text-embedding-3-small",
                "api_key": self.OPENAI_API_KEY,
                "embedding_dims": embedding_dims,  # 768 to match Qdrant
            })

        return {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "host": self.QDRANT_HOST,
                    "port": self.QDRANT_PORT,
                    "collection_name": self.QDRANT_COLLECTION_NAME,
                    "embedding_model_dims": embedding_dims,
                },
            },
            "llm": llm_config,
            "embedder": embedder_config
        }

    @computed_field
    @property
    def MONGO_URI(self) -> str:  # pylint: disable=invalid-name
        """
        Constructs and returns the MongoDB connection URI string.

        Returns:
            str: The MongoDB URI in the format:
                'mongodb://<username>:<password>@<host>:<port>/'
            where <username>, <password>, <host>, and <port> are obtained from
            the corresponding instance attributes:
                - MONGO_INITDB_ROOT_USERNAME
                - MONGO_INITDB_ROOT_PASSWORD
                - MONGO_HOST
                - MONGO_PORT
        """
        return f"mongodb://{self.MONGO_INITDB_ROOT_USERNAME}:{self.MONGO_INITDB_ROOT_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}/"


# Instanciação segura
try:
    settings = Settings()  # type: ignore
except ValidationError as e:
    from src.core.logs import logger
    logger.critical("CRITICAL ERROR: Missing environment variables in .env file!")
    logger.critical(e)
    sys.exit(1)
