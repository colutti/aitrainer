"""
LangChain tools for user profile management.
"""

from langchain_core.tools import tool
from src.core.logs import logger
from src.services.database import MongoDatabase


def create_get_user_goal_tool(database: MongoDatabase, user_email: str):
    """
    Factory function to create a get_user_goal tool with injected dependencies.
    """

    @tool
    def get_user_goal() -> str:
        """
        Consulta o perfil e objetivo atual do aluno (perder peso, ganhar massa, manter peso).

        O perfil básico já está em seu contexto no sistema, mas use esta tool quando:
        - O aluno mencionar mudança de objetivo e você quiser confirmar os dados atualizados
        - Precisar re-consultar após possível atualização de perfil
        - Quiser validar dados antes de fazer recomendações personalizadas

        Exemplo: "Antes eu perdia peso, mas agora quero ganhar massa" → use esta tool
                 para confirmar que o objetivo foi atualizado.
        """
        try:
            profile = database.get_user_profile(user_email)
            if not profile:
                return "Perfil do aluno não encontrado."

            summary = profile.get_profile_summary()
            return f"Este é o objetivo atual do aluno:\n\n{summary}"

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to get user goal for %s: %s", user_email, e)
            return "Erro ao buscar objetivo do aluno."

    return get_user_goal


def create_update_user_goal_tool(database: MongoDatabase, user_email: str):
    """
    Factory function to create an update_user_goal tool with injected dependencies.
    """

    @tool
    def update_user_goal(goal_type: str, weekly_rate: float | None = None) -> str:
        """
        Atualiza o tipo de objetivo e a taxa semanal de mudança de peso do perfil do aluno.

        Parâmetros:
        - goal_type: um de 'lose' (perda), 'gain' (ganho), 'maintain' (manutenção)
        - weekly_rate: taxa semanal em kg (OBRIGATÓRIO para 'lose' ou 'gain', ignorado para 'maintain')

        Exemplos de uso:
        - Aluno quer parar de perder peso: goal_type='maintain'
        - Aluno quer ganhar 0.5kg/semana: goal_type='gain', weekly_rate=0.5
        - Aluno quer perder 1kg/semana: goal_type='lose', weekly_rate=1.0

        Use quando o aluno expressar mudança clara de objetivo ou quando calcular
        que o objetivo atual não mais faz sentido (ex: já atingiu peso-alvo).
        """
        try:
            if goal_type not in ["lose", "gain", "maintain"]:
                return "Erro: goal_type deve ser 'lose', 'gain' ou 'maintain'."

            if goal_type in ["lose", "gain"] and (
                weekly_rate is None or weekly_rate <= 0
            ):
                return (
                    "Erro: weekly_rate (taxa semanal) é obrigatório e deve ser "
                    "positivo para objetivos de perda ou ganho."
                )

            profile = database.get_user_profile(user_email)
            if not profile:
                return "Perfil do aluno não encontrado."

            profile.goal_type = goal_type
            if weekly_rate is not None:
                profile.weekly_rate = weekly_rate
            elif goal_type == "maintain":
                profile.weekly_rate = 0.0

            database.save_user_profile(profile)

            action = {
                "lose": "focado em perda de peso",
                "gain": "focado em ganho de massa",
                "maintain": "focado em manutenção",
            }[goal_type]

            rate_info = (
                f" com uma taxa de {weekly_rate}kg/semana"
                if weekly_rate and goal_type != "maintain"
                else ""
            )

            logger.info(
                "User %s updated goal to %s%s", user_email, goal_type, rate_info
            )
            return (
                f"Perfil atualizado com sucesso! Agora você está {action}{rate_info}."
            )

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to update user goal for %s: %s", user_email, e)
            return f"Erro ao atualizar perfil: {str(e)}"

    return update_user_goal
