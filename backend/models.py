from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """
    Data class to hold user configuration and profile data.
    """

    gender: str = Field(
        ..., description="Gênero do usuário", pattern="^(Masculino|Feminino)$"
    )
    age: int = Field(..., ge=18, le=100, description="Idade entre 18 e 100 anos")
    weight: float = Field(
        ..., ge=30.0, le=500.0, description="Peso em kg entre 30 e 500"
    )
    height: int = Field(..., ge=100, le=250, description="Altura em cm entre 100 e 250")
    goal: str = Field(..., min_length=5, description="Objetivo do usuário")
    email: str = Field(..., description="E-mail do usuário")


# Input do usuário para atualização do perfil do treinador
class TrainerProfileInput(BaseModel):
    """
    Campos editáveis do perfil do treinador (input do usuário).
    """
    humour: str = Field(
        ...,
        description="Personalidade do treinador",
        pattern="^(Motivacional|Rígido|Amigavel|Sarcástico)$",
    )
    name: str = Field(..., description="Nome do treinador")
    gender: str = Field(
        ..., description="Gênero do treinador", pattern="^(Masculino|Feminino)$"
    )
    style: str = Field(
        ...,
        description="Estilo do treinador",
        pattern="^(Científico|Holístico|Bootcamp Militar)$",
    )

# Perfil completo do treinador (inclui user_email)


class TrainerProfile(TrainerProfileInput):
    """
    TrainerProfile model representando o perfil completo (inclui user_email).
    """
    user_email: str = Field(..., description="E-mail do usuário")


class LoginRequest(BaseModel):
    """
    Represents a login request containing user credentials.

    Attributes:
        email (str): The user's email address.
        password (str): The user's password.
    """
    email: str
    password: str


class MessageRequest(BaseModel):
    """
    Represents a request containing a user's message.

    Attributes:
        user_message (str): The message provided by the user.
    """
    user_message: str
