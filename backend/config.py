import sys

from pydantic import ValidationError, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .prompt_template import PROMPT_TEMPLATE


class Settings(BaseSettings):
    """
    Settings

    Configuration class for application settings, loaded from environment variables and .env files.

    Attributes:
        GEMINI_API_KEY (str): API key for Gemini service.
        SECRET_KEY (str): Secret key for application security.
        DB_NAME (str): Name of the database.
        MONGO_INITDB_ROOT_USERNAME (str): MongoDB root username.
        MONGO_INITDB_ROOT_PASSWORD (str): MongoDB root password.
        MONGO_HOST (str): MongoDB host address.
        MONGO_PORT (int): MongoDB port number.
        API_SERVER_PORT (int): Port number for the API server.
        MODEL_NAME (str): Name of the AI model to use (default: "gemini-pro-latest").
        SUMMARY_MODEL_NAME (str): Name of the AI model to use for generating conversation summaries (default: "gemini-1.5-flash").
        PROMPT_TEMPLATE (str): Template string for generating prompts, including trainer and student profiles, personality modulators, and response guidelines.

    Properties:
        MONGO_URI (str): Computed MongoDB connection URI in the format:
            where values are taken from the corresponding attributes.

    Notes:
        - Loads configuration from a .env file with UTF-8 encoding.
        - Ignores extra environment variables not defined in the class.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    GEMINI_API_KEY: str
    SECRET_KEY: str
    DB_NAME: str
    MONGO_INITDB_ROOT_USERNAME: str
    MONGO_INITDB_ROOT_PASSWORD: str
    MONGO_HOST: str
    MONGO_PORT: int
    API_SERVER_PORT: int

    MODEL_NAME: str = "gemini-pro-latest"
    SUMMARY_MODEL_NAME: str = "gemini-1.5-flash"

    PROMPT_TEMPLATE: str = PROMPT_TEMPLATE

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
    print("❌ ERRO CRÍTICO: Variáveis de ambiente faltando no arquivo .env!")
    print(e)
    sys.exit(1)
