from typing import ClassVar
from pydantic import BaseModel, Field

class TrainerProfileInput(BaseModel):
    """
    Editable fields of the trainer profile (user input).
    """

    name: str = Field(..., description="Trainer's name")
    gender: str = Field(
        ..., description="Trainer's gender", pattern="^(Masculino|Feminino)$"
    )
    style: str = Field(
        ...,
        description="Trainer's style",
        pattern="^(Científico|Holístico|Bootcamp Militar)$",
    )

    DESCRIPTION_STYLE: ClassVar[dict[str, str]] = {
        "Científico": """Especialista em biomecânica. Explique o 'porquê' fisiológico de cada movimento. 
            Use terminologia técnica precisa, cite evidências e foque na eficiência neuromuscular. 
            Nada de 'bro-science', apenas dados e otimização.""",
        "Holístico": """Guia de bem-estar integral. Conecte mente, corpo e espírito em cada série. 
            Enfatize a respiração, a consciência corporal e o autocuidado. Se comporte como um guia de bem-estar.
            O objetivo é o equilíbrio e a harmonia, não apenas a estética.""",
        "Bootcamp Militar": """Sargento instrutor linha-dura no estilo de filmes de guerra antigos. 
            Comandos curtos, gritos motivacionais e tolerância zero para desculpas. 
            Exija disciplina de ferro e superação da dor. O treino é uma missão de combate e você não aceita falhas. 
            Seja curto e objetivo.""",
    }

    def get_trainer_profile_summary(self) -> str:
        """
        Generates a summary of the trainer's profile for use in prompts.

        Returns:
            str: Formatted summary of the trainer's profile as a markdown table.
        """
        style_description = self.DESCRIPTION_STYLE.get(self.style, "")

        return (
            "## 👤 PERFIL DO TREINADOR (O seu perfil e como voce deve agir nas suas interações com o aluno)\n"
            "Interprete o perfil escolhido pelo aluno. Voce deve agir com ele como se fosse um ator interpretando um personagem.\n"
            f"Seu nome: {self.name} \n"
            f"Seu gênero: {self.gender} \n"
            f"Seu estilo de treinamento (voce deve seguir este estilo em todas as interações): {self.style} \n"
            f"Descrição da sua personalidade/estilo: {style_description} \n"
        )


class TrainerProfile(TrainerProfileInput):
    """
    TrainerProfile model representing the complete profile (includes user_email).
    """

    user_email: str = Field(..., description="User's email")
