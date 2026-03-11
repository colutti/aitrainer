"""
LangChain tools for body composition tracking.
"""

from datetime import datetime
from langchain_core.tools import tool
from src.core.logs import logger
from src.api.models.weight_log import WeightLog
from src.services.adaptive_tdee import AdaptiveTDEEService


def create_save_composition_tool(database, user_email: str):
    """
    Factory function to create a save_body_composition tool with injected dependencies.
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    @tool
    def save_body_composition(
        weight_kg: float,
        date: str | None = None,
        body_fat_pct: float | None = None,
        muscle_mass_pct: float | None = None,
        muscle_mass_kg: float | None = None,
        bone_mass_kg: float | None = None,
        body_water_pct: float | None = None,
        visceral_fat: float | None = None,
        bmr: int | None = None,
        bmi: float | None = None,
        notes: str | None = None,
        neck_cm: float | None = None,
        chest_cm: float | None = None,
        waist_cm: float | None = None,
        hips_cm: float | None = None,
        bicep_r_cm: float | None = None,
        bicep_l_cm: float | None = None,
        thigh_r_cm: float | None = None,
        thigh_l_cm: float | None = None,
        calf_r_cm: float | None = None,
        calf_l_cm: float | None = None,
    ) -> str:
        """
        Salva ou atualiza os dados de composição corporal do aluno.

        Use APENAS para dados corporais (peso, gordura, medidas).
        NÃO salve: humor, sono, nível de energia.

        Use quando o aluno reportar:
        - Peso de uma balança inteligente (com bioimpedância):
          peso_kg, body_fat_pct, muscle_mass_kg, etc.
        - Medidas manuais com fita métrica: waist_cm, hip_cm, chest_cm, etc.
        - Dados de wearable/aplicativo: qualquer combinação dos campos acima

        Todos os campos são opcionais exceto weight_kg. Retorna dados brutos para seu análise e
        comparação com seus algoritmos.

        Exemplo: aluno fez medição no Zepp Life → use body_fat_pct, visceral_fat.
                 aluno mediu com fita → use waist_cm, hips_cm, chest_cm, neck_cm.
        """
        try:
            if date:
                try:
                    log_date = datetime.fromisoformat(date).date()
                except ValueError:
                    log_date = datetime.strptime(date, "%Y-%m-%d").date()
            else:
                log_date = datetime.now().date()

            # Calculate trend weight using EMA (same as API does)
            prev_logs = database.get_weight_logs(user_email, limit=1)
            prev_trend = prev_logs[0].trend_weight if prev_logs else None
            tdee_service = AdaptiveTDEEService(database)
            new_trend = tdee_service.calculate_ema_trend(weight_kg, prev_trend)

            log = WeightLog(
                user_email=user_email,
                date=log_date,
                weight_kg=weight_kg,
                body_fat_pct=body_fat_pct,
                muscle_mass_pct=muscle_mass_pct,
                muscle_mass_kg=muscle_mass_kg,
                bone_mass_kg=bone_mass_kg,
                body_water_pct=body_water_pct,
                visceral_fat=visceral_fat,
                bmr=bmr,
                bmi=bmi,
                notes=notes,
                source="chat",
                neck_cm=neck_cm,
                chest_cm=chest_cm,
                waist_cm=waist_cm,
                hips_cm=hips_cm,
                bicep_r_cm=bicep_r_cm,
                bicep_l_cm=bicep_l_cm,
                thigh_r_cm=thigh_r_cm,
                thigh_l_cm=thigh_l_cm,
                calf_r_cm=calf_r_cm,
                calf_l_cm=calf_l_cm,
                trend_weight=new_trend,
            )

            doc_id, is_new = database.save_weight_log(log)
            action = "registrada" if is_new else "atualizada"
            date_str = log_date.strftime("%d/%m/%Y")

            logger.info("Body composition %s for %s on %s", action, user_email, date_str)
            return f"Composição corporal de {date_str} {action} com sucesso! (ID: {doc_id})"

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to save body composition for %s: %s", user_email, e)
            return "Erro ao salvar composição corporal. Tente novamente."

    return save_body_composition


def _format_metrics(log) -> str:
    """Helper to format basic metrics for a composition log."""
    metrics = [f"Peso: {log.weight_kg}kg"]
    if log.body_fat_pct:
        metrics.append(f"Gordura: {log.body_fat_pct}%")
    if log.muscle_mass_kg:
        metrics.append(f"Músculo: {log.muscle_mass_kg}kg")
    elif log.muscle_mass_pct:
        metrics.append(f"Músculo: {log.muscle_mass_pct}%")
    if log.visceral_fat:
        metrics.append(f"Gord. Visceral: {log.visceral_fat}")
    if log.bmr:
        metrics.append(f"BMR: {log.bmr} kcal")
    return ", ".join(metrics)


def _format_measurements(log) -> list[str]:
    """Helper to format body measurements for a composition log."""
    measurements = []
    if log.neck_cm:
        measurements.append(f"Pescoço: {log.neck_cm}cm")
    if log.chest_cm:
        measurements.append(f"Peito: {log.chest_cm}cm")
    if log.waist_cm:
        measurements.append(f"Cintura: {log.waist_cm}cm")
    if log.hips_cm:
        measurements.append(f"Quadril: {log.hips_cm}cm")
    if log.bicep_r_cm or log.bicep_l_cm:
        measurements.append(
            f"Bíceps: D={log.bicep_r_cm}cm E={log.bicep_l_cm}cm"
            if log.bicep_r_cm and log.bicep_l_cm
            else f"Bíceps: {log.bicep_r_cm or log.bicep_l_cm}cm"
        )
    if log.thigh_r_cm or log.thigh_l_cm:
        measurements.append(
            f"Coxa: D={log.thigh_r_cm}cm E={log.thigh_l_cm}cm"
            if log.thigh_r_cm and log.thigh_l_cm
            else f"Coxa: {log.thigh_r_cm or log.thigh_l_cm}cm"
        )
    if log.calf_r_cm or log.calf_l_cm:
        measurements.append(
            f"Panturrilha: D={log.calf_r_cm}cm E={log.calf_l_cm}cm"
            if log.calf_r_cm and log.calf_l_cm
            else f"Panturrilha: {log.calf_r_cm or log.calf_l_cm}cm"
        )
    return measurements


def create_get_composition_tool(database, user_email: str):
    """
    Factory function to create a get_body_composition tool with injected dependencies.
    """

    @tool
    def get_body_composition(limit: int = 10) -> str:
        """
        Busca o histórico recente de composição corporal do aluno (últimos N registros).

        Use quando o aluno perguntar sobre evolução de peso, gordura corporal, ou histórico
        de medições. Retorna dados brutos para você calcular tendências e tirar suas próprias
        conclusões sobre progressão corporal.

        Exemplo: "Mostre meu histórico de gordura corporal dos últimos meses"
                 → Use esta tool, e você fará sua própria análise vs seus algoritmos.
        """
        try:
            logs = database.get_weight_logs(user_email, limit=limit)

            if not logs:
                return "Nenhum registro de composição corporal encontrado ainda."

            result = f"Encontrei {len(logs)} registro(s) de composição corporal:\n\n"
            for log in logs:
                date_str = log.date.strftime("%d/%m/%Y")

                metrics_str = _format_metrics(log)
                result += f"📅 {date_str}: {metrics_str}\n"

                measurements = _format_measurements(log)
                if measurements:
                    result += f"   Medidas: {', '.join(measurements)}\n"

                if log.notes:
                    result += f"   Nota: {log.notes}\n"
                result += "\n"

            # Pre-compute weekly averages for AI
            if len(logs) >= 2:
                today = datetime.now().date()
                current_week = [log for log in logs if (today - log.date).days < 7]
                prev_week = [log for log in logs if 7 <= (today - log.date).days < 14]

                result += "\n=== MÉDIAS SEMANAIS (pré-calculadas) ===\n"

                if current_week:
                    avg_current = (
                        sum(log.weight_kg for log in current_week) / len(current_week)
                    )
                    result += (
                        f"Média últimos 7 dias: {avg_current:.2f} kg "
                        f"({len(current_week)} logs)\n"
                    )
                    bf_vals = [log.body_fat_pct for log in current_week if log.body_fat_pct]
                    if bf_vals:
                        result += (
                            f"BF médio últimos 7 dias: "
                            f"{sum(bf_vals)/len(bf_vals):.1f}%\n"
                        )

                if prev_week:
                    avg_prev = sum(log.weight_kg for log in prev_week) / len(prev_week)
                    result += (
                        f"Média 7-14 dias atrás: {avg_prev:.2f} kg ({len(prev_week)} logs)\n"
                    )
                    if current_week:
                        diff = avg_current - avg_prev
                        result += f"Variação média semanal: {diff:+.2f} kg\n"

                if logs[0].trend_weight:
                    result += f"\nPeso de tendência (EMA): {logs[0].trend_weight:.2f} kg\n"

                result += "\n⚠️ USE ESTAS MÉDIAS para comparações. NÃO compare pesos isolados.\n"

            return result

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to get body composition for %s: %s", user_email, e)
            return "Erro ao buscar histórico de composição corporal."

    return get_body_composition
