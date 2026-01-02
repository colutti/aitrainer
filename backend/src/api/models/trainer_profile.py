from pydantic import BaseModel, Field

class TrainerProfileInput(BaseModel):
    """
    Editable fields of the trainer profile (user input).
    """

    humour: str = Field(
        ...,
        description="Trainer's personality",
        pattern="^(Motivacional|Rígido|Amigavel|Sarcástico)$",
    )
    name: str = Field(..., description="Trainer's name")
    gender: str = Field(
        ..., description="Trainer's gender", pattern="^(Masculino|Feminino)$"
    )
    style: str = Field(
        ...,
        description="Trainer's style",
        pattern="^(Científico|Holístico|Bootcamp Militar)$",
    )

    def get_trainer_profile_summary(self) -> str:
        """
        Generates a summary of the trainer's profile for use in prompts.

        Returns:
            str: Formatted summary of the trainer's profile as a markdown table.
        """
        if self.humour == "Motivacional":
            humour_description = (
                "Use um tom energético, com exclamações e emojis para motivar o aluno."
            )
        elif self.humour == "Rígido":
            humour_description = (
                "Adote um tom firme e direto, sem espaço para desculpas."
            )
        elif self.humour == "Amigavel":
            humour_description = (
                "Mantenha um tom casual e acolhedor, como um parceiro de treino."
            )
        elif self.humour == "Sarcástico":
            humour_description = (
                "Incorpore ironia inteligente e deboche leve em suas respostas."
            )
        else:
            humour_description = "Mantenha um tom profissional e neutro."

        if self.style == "Científico":
            style_description = (
                "Use termos técnicos e explique o 'porquê' dos exercícios."
            )
        elif self.style == "Holístico":
            style_description = "Foque no bem-estar geral, mente-músculo e autocuidado."
        elif self.style == "Bootcamp Militar":
            style_description = (
                "Use comandos curtos e diretos, com ênfase na disciplina."
            )
        else:
            style_description = "Adote um estilo equilibrado e adaptável."

        return (
            f"| Campo | Valor |\n"
            f"|-------|-------|\n"
            f"| Nome | {self.name} |\n"
            f"| Gênero | {self.gender} |\n"
            f"| Estilo | {self.style} |\n"
            f"| Descrição Estilo | {style_description} |\n"
            f"| Humor | {self.humour} |\n"
            f"| Descrição Humor | {humour_description} |"
        )


class TrainerProfile(TrainerProfileInput):
    """
    TrainerProfile model representing the complete profile (includes user_email).
    """

    user_email: str = Field(..., description="User's email")
