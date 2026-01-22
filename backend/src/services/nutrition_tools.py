"""
LangChain tools for nutrition tracking.
"""

from datetime import datetime
from langchain_core.tools import tool
from src.core.logs import logger


def create_save_nutrition_tool(database, user_email: str):
    """
    Factory function to create a save_nutrition tool with injected dependencies.

    Args:
        database: MongoDatabase instance.
        user_email: Email of the user.

    Returns:
        A LangChain tool function.
    """
    from src.api.models.nutrition_log import NutritionLog

    @tool
    def save_daily_nutrition(
        calories: int,
        protein_grams: float,
        carbs_grams: float,
        fat_grams: float,
        fiber_grams: float | None = None,
        sugar_grams: float | None = None,
        sodium_mg: float | None = None,
        cholesterol_mg: float | None = None,
        date: str | None = None,
    ) -> str:
        """
        Salva o resumo nutricional DIÁRIO do aluno.
        Geralmente usado quando o aluno reporta o que comeu no dia (ex: dados do MyFitnessPal).
        Se já existe log para a data, ATUALIZA os dados (upsert).

        EXTRAIA os TOTAIS do texto do aluno (linha "TOTAIS" se for tabela).

        Args:
            calories (int): Calorias totais (kcal).
            protein_grams (float): Proteínas totais (g).
            carbs_grams (float): Carboidratos totais (g).
            fat_grams (float): Gorduras totais (g).
            fiber_grams (float, opcional): Fibras totais (g).
            sugar_grams (float, opcional): Açúcar total (g).
            sodium_mg (float, opcional): Sódio total (mg).
            cholesterol_mg (float, opcional): Colesterol total (mg).
            date (str, opcional): Data no formato ISO (YYYY-MM-DD). Se omitido, usa hoje.

        Returns:
            Confirmação de que o log foi salvo/atualizado.
        """
        try:
            if date:
                try:
                    log_date = datetime.fromisoformat(date)
                except ValueError:
                    # Tentar formato simples YYYY-MM-DD
                    log_date = datetime.strptime(date, "%Y-%m-%d")
            else:
                log_date = datetime.now()

            log = NutritionLog(
                user_email=user_email,
                date=log_date,
                calories=calories,
                protein_grams=protein_grams,
                carbs_grams=carbs_grams,
                fat_grams=fat_grams,
                fiber_grams=fiber_grams,
                sugar_grams=sugar_grams,
                sodium_mg=sodium_mg,
                cholesterol_mg=cholesterol_mg,
                source="chat",
                notes=None,
            )

            doc_id, is_new = database.save_nutrition_log(log)

            action = "criado" if is_new else "atualizado"
            date_str = log_date.strftime("%d/%m/%Y")

            logger.info(
                "Nutrition log %s for user %s on %s", action, user_email, date_str
            )
            return f"Log nutricional de {date_str} {action} com sucesso! (ID: {doc_id})"

        except Exception as e:
            logger.error("Failed to save nutrition log for user %s: %s", user_email, e)
            return (
                "Erro ao salvar log nutricional. Verifique os dados e tente novamente."
            )

    return save_daily_nutrition


def create_get_nutrition_tool(database, user_email: str):
    """
    Factory function to create get_nutrition tool.
    """

    @tool
    def get_nutrition(limit: int = 7) -> str:
        """
        Busca o histórico nutricional recente do aluno.
        Use quando o aluno perguntar "o que comi", "minhas macros" ou sobre histórico.

        Args:
            limit (int): Número de dias a buscar (default: 7).

        Returns:
            Resumo formatado dos logs nutricionais.
        """
        try:
            logs = database.get_nutrition_logs(user_email, limit=limit)

            if not logs:
                return "Nenhum registro nutricional encontrado recentemente."

            result = f"Encontrei {len(logs)} registro(s) nutricional(is):\n\n"
            for log in logs:
                date_str = log.date.strftime("%d/%m/%Y")
                micros = []
                if log.fiber_grams:
                    micros.append(f"Fibras: {log.fiber_grams}g")
                if log.sodium_mg:
                    micros.append(f"Sódio: {log.sodium_mg}mg")

                micros_str = f" | {', '.join(micros)}" if micros else ""

                result += (
                    f"📅 {date_str}: {log.calories} kcal\n"
                    f"   P: {log.protein_grams}g | C: {log.carbs_grams}g | G: {log.fat_grams}g{micros_str}\n\n"
                )

            return result

        except Exception as e:
            logger.error(
                "Failed to get nutrition history for user %s: %s", user_email, e
            )
            return "Erro ao buscar histórico nutricional."

    return get_nutrition
