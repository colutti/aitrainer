import sys
from pydantic import ValidationError, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.logs import logger


PROMPT_TEMPLATE = """
Você é um Treinador Pessoal de elite e Nutricionista.
Sua base é a ciência, mas sua entrega depende da sua personalidade única
configurada abaixo.

=== SEU PERFIL (DO TREINADOR) ===
{trainer_profile}

=== PERFIL DO ALUNO ===
{user_profile}

=== DIRETRIZES DE RESPOSTA ===
1. FIT: Crie treinos estruturados e progressivos.
Sempre dê 1 dica de segurança/forma por exercício.
2. NUTRI: Calcule TDEE/Macros estimados.
Sugira refeições reais (regra 80/20), não apenas números.
3. ESTILO: Responda de forma concisa (chat).
Use o histórico para manter contexto.
4. REGRA DE OURO: Nunca dê planos genéricos.
Ajuste tudo aos dados do aluno.

=======================================
=== MEMÓRIAS RELEVANTES (Conversas passadas entre treinador (voce) e aluno (usuario)) ===
{relevant_memories}

=======================================
=== MENSAGENS MAIS RECENTES (Entre treinador (voce) e aluno (usuario)) ===
{chat_history_summary}

=======================================
=== NOVA MENSAGEM DO ALUNO ===

"""

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

    # ====== GEMINI STUFF ======
    GEMINI_API_KEY: str
    LLM_MODEL_NAME: str
    EMBEDDER_MODEL_NAME: str
    LLM_TEMPERATURE: float = 0.2  # Default value for LLM temperature
    EMBEDDING_MODEL_DIMS: int = 768  # Default value for embedding model dimensions
    PROMPT_TEMPLATE: str = PROMPT_TEMPLATE

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
        return {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "host": self.QDRANT_HOST,
                    "port": self.QDRANT_PORT,
                    "collection_name": self.QDRANT_COLLECTION_NAME,
                    "embedding_model_dims": 768,
                    # "api_key": self.QDRANT_API_KEY if self.QDRANT_API_KEY else None,
                },
            },
            "llm": {
                "provider": "gemini",
                "config": {
                    "model": self.LLM_MODEL_NAME,
                    "temperature": 0.2,
                    "max_tokens": 2000,
                    "top_p": 1.0
                }
            },
            "embedder": {
                "provider": "gemini",
                "config": {
                    "model": self.EMBEDDER_MODEL_NAME,
                }
            }
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
