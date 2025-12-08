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


    def get_profile_summary(self) -> str:
        """
        Gera um resumo do perfil do usuário para uso em prompts.

        Retorna:
            str: Resumo formatado do perfil do usuário.
        """
        return (
            f"- Gênero: {self.gender}\n"
            f"- Idade: {self.age} anos\n"
            f"- Peso: {self.weight}kg\n"
            f"- Altura: {self.height}cm\n"
            f"- Objetivo: {self.goal}\n"
        )


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

    def get_trainer_profile_summary(self) -> str:
        """
        Gera um resumo do perfil do treinador para uso em prompts.

        Retorna:
            str: Resumo formatado do perfil do treinador.
        """
        if self.humour == "Motivacional":
            humour_description = "Use um tom energético, com exclamações e emojis para motivar o aluno."
        elif self.humour == "Rígido":
            humour_description = "Adote um tom firme e direto, sem espaço para desculpas."
        elif self.humour == "Amigavel":
            humour_description = "Mantenha um tom casual e acolhedor, como um parceiro de treino."
        elif self.humour == "Sarcástico":
            humour_description = "Incorpore ironia inteligente e deboche leve em suas respostas."
        else:
            humour_description = "Mantenha um tom profissional e neutro."

        if self.style == "Científico":
            style_description = "Use termos técnicos e explique o 'porquê' dos exercícios."
        elif self.style == "Holístico":
            style_description = "Foque no bem-estar geral, mente-músculo e autocuidado."
        elif self.style == "Bootcamp Militar":
            style_description = "Use comandos curtos e diretos, com ênfase na disciplina."
        else:
            style_description = "Adote um estilo equilibrado e adaptável."

        return (

            f"- Nome: {self.name}\n"
            f"- Gênero: {self.gender}\n"
            f"- Estilo: {self.style} ({style_description})\n"
            f"- Humor: {self.humour} ({humour_description})\n"
        )



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


class ConversationSummary(BaseModel):
    """
    Represents the long-term memory summary of a user's conversation.

    Attributes:
        user_email (str): The user's email address (primary key/identifier).
        summary (str): The conversation summary text (long-term memory).
    """
    user_email: str = Field(..., description="User's email address")
    summary: str = Field(
        default="",
        description="Long-term memory summary of the conversation"
    )
