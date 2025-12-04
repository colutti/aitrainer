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


class TrainerProfile(BaseModel):
    user_email: str = Field(..., description="E-mail do usuário")
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


class LoginRequest(BaseModel):
    email: str
    password: str


class MessageRequest(BaseModel):
    user_message: str
