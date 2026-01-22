"""
LangChain tools for body composition tracking.
"""

from datetime import datetime
from langchain_core.tools import tool
from src.core.logs import logger


def create_save_composition_tool(database, user_email: str):
    """
    Factory function to create a save_body_composition tool with injected dependencies.

    Args:
        database: MongoDatabase instance.
        user_email: Email of the user.

    Returns:
        A LangChain tool function for saving body composition logs.
    """
    from src.api.models.weight_log import WeightLog

    @tool
    def save_body_composition(
        weight_kg: float,
        date: str | None = None,
        body_fat_pct: float | None = None,
        muscle_mass_pct: float | None = None,
        bone_mass_kg: float | None = None,
        body_water_pct: float | None = None,
        visceral_fat: float | None = None,
        bmr: int | None = None,
        bmi: float | None = None,
        notes: str | None = None,
    ) -> str:
        """
        Salva ou atualiza os dados de composição corporal (peso, gordura, músculo, etc.) do aluno.
        Use esta ferramenta sempre que o aluno reportar seu peso ou dados vindos de uma balança de bioimpedância.

        Args:
            weight_kg (float): Peso corporal total em quilogramas.
            date (str, opcional): Data no formato ISO (YYYY-MM-DD). Se não informado, usa hoje.
            body_fat_pct (float, opcional): Percentual de gordura corporal (0-100).
            muscle_mass_pct (float, opcional): Percentual de massa muscular (0-100).
            bone_mass_kg (float, opcional): Massa óssea em kg.
            body_water_pct (float, opcional): Percentual de água corporal.
            visceral_fat (float, opcional): Nível de gordura visceral.
            bmr (int, opcional): Taxa metabólica basal (kcal).
            bmi (float, opcional): Índice de massa corporal.
            notes (str, opcional): Notas ou observações adicionais.

        Returns:
            Confirmação de que os dados foram salvos.
        """
        try:
            if date:
                try:
                    log_date = datetime.fromisoformat(date).date()
                except ValueError:
                    log_date = datetime.strptime(date, "%Y-%m-%d").date()
            else:
                log_date = datetime.now().date()

            log = WeightLog(
                user_email=user_email,
                date=log_date,
                weight_kg=weight_kg,
                body_fat_pct=body_fat_pct,
                muscle_mass_pct=muscle_mass_pct,
                bone_mass_kg=bone_mass_kg,
                body_water_pct=body_water_pct,
                visceral_fat=visceral_fat,
                bmr=bmr,
                bmi=bmi,
                notes=notes,
                source="chat",
            )

            doc_id, is_new = database.save_weight_log(log)
            action = "registrada" if is_new else "atualizada"
            date_str = log_date.strftime("%d/%m/%Y")

            logger.info(
                "Body composition %s for user %s on %s", action, user_email, date_str
            )
            return f"Composição corporal de {date_str} {action} com sucesso! (ID: {doc_id})"

        except Exception as e:
            logger.error(
                "Failed to save body composition for user %s: %s", user_email, e
            )
            return "Erro ao salvar composição corporal. Tente novamente."

    return save_body_composition


def create_get_composition_tool(database, user_email: str):
    """
    Factory function to create a get_body_composition tool with injected dependencies.

    Args:
        database: MongoDatabase instance.
        user_email: Email of the user.

    Returns:
        A LangChain tool function for retrieving body composition logs.
    """

    @tool
    def get_body_composition(limit: int = 10) -> str:
        """
        Busca o histórico recente de composição corporal do aluno.
        Use quando o aluno perguntar sobre sua evolução de peso, percentual de gordura ou massa muscular.

        Args:
            limit (int): Número máximo de registros a buscar (default: 10).

        Returns:
            Resumo formatado do histórico de composição corporal.
        """
        try:
            logs = database.get_weight_logs(user_email, limit=limit)

            if not logs:
                return "Nenhum registro de composição corporal encontrado ainda."

            result = f"Encontrei {len(logs)} registro(s) de composição corporal:\n\n"
            for log in logs:
                date_str = log.date.strftime("%d/%m/%Y")

                metrics = [f"Peso: {log.weight_kg}kg"]
                if log.body_fat_pct:
                    metrics.append(f"Gordura: {log.body_fat_pct}%")
                if log.muscle_mass_pct:
                    metrics.append(f"Músculo: {log.muscle_mass_pct}%")
                if log.visceral_fat:
                    metrics.append(f"Gord. Visceral: {log.visceral_fat}")
                if log.bmr:
                    metrics.append(f"BMR: {log.bmr} kcal")

                result += f"📅 {date_str}: {', '.join(metrics)}\n"
                if log.notes:
                    result += f"   Nota: {log.notes}\n"
                result += "\n"

            return result

        except Exception as e:
            logger.error(
                "Failed to get body composition for user %s: %s", user_email, e
            )
            return "Erro ao buscar histórico de composição corporal."

    return get_body_composition
