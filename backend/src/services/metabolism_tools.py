"""
LangChain tools for TDEE and metabolism data access.
Provides AI trainer access to adaptive TDEE calculations with full algorithm documentation.
"""

from datetime import date, timedelta
from langchain_core.tools import tool
from src.core.logs import logger
from src.services.database import MongoDatabase
from src.services.adaptive_tdee import AdaptiveTDEEService


def create_get_metabolism_tool(database: MongoDatabase, user_email: str):
    """
    Factory function to create a get_metabolism_data tool with injected dependencies.
    """

    @tool
    def get_metabolism_data() -> str:
        """
        Consulta os dados brutos de metabolismo e TDEE do aluno.

        Retorna:
        - TDEE atual e meta calórica
        - Histórico de peso e calorias dos últimos 30 dias (dados crus)
        - Médias de 'Lows' (3 menores pesos) da semana atual vs anterior

        USE ESTA TOOL SEMPRE que precisar analisar o progresso real ou quando o aluno
        questionar se a meta está correta. Use os dados brutos para tirar suas próprias
        conclusões matemáticas e comparar com a estimativa do algoritmo.
        """
        try:
            tdee_service = AdaptiveTDEEService(database)
            tdee_data = tdee_service.calculate_tdee(user_email, lookback_weeks=4)
            profile = database.get_user_profile(user_email)

            # Extract raw trends
            w_trend = tdee_data.get("weight_trend", [])
            c_trend = tdee_data.get("calorie_trend", [])

            # Calculate Weekly Lows (3 lowest weights)
            today = date.today()
            
            def get_avg_lows(days_offset_start, days_offset_end):
                d_start = today - timedelta(days=days_offset_start)
                d_end = today - timedelta(days=days_offset_end)
                period_weights = [
                    w["weight"] for w in w_trend
                    if w["weight"] and d_end <= date.fromisoformat(w["date"]) <= d_start
                ]
                if not period_weights:
                    return None
                lowest_3 = sorted(period_weights)[:3]
                return sum(lowest_3) / len(lowest_3)

            current_lows = get_avg_lows(0, 6)
            previous_lows = get_avg_lows(7, 13)

            lows_delta = (current_lows - previous_lows) if (current_lows and previous_lows) else None
            
            # Pack status info
            lows_status = f"{lows_delta:+.2f} kg" if lows_delta is not None else "N/A"

            # Build detailed raw response
            response = f"""=== METABOLISMO: DADOS BRUTOS (Últimos 30 dias) ===

TDEE Estimado: {tdee_data.get('tdee')} kcal
Meta Diária Atual: {tdee_data.get('daily_target')} kcal
Objetivo: {tdee_data.get('goal_type')} ({tdee_data.get('goal_weekly_rate')} kg/semana)

-- AUDITORIA DE LOWS (Média dos 3 menores pesos) --
Semana Atual: {f'{current_lows:.2f} kg' if current_lows else 'N/A'}
Semana Anterior: {f'{previous_lows:.2f} kg' if previous_lows else 'N/A'}
Delta Lows: {lows_status}

-- SÉRIE TEMPORAL (Peso e Calorias) --
"""
            # Add last 14 days of raw data for concise AI context
            r_weight = {w["date"]: w["weight"] for w in w_trend}
            r_cal = {c["date"]: c["calories"] for c in c_trend}

            all_dates = sorted(set(list(r_weight.keys()) + list(r_cal.keys())), reverse=True)[:14]
            for d in all_dates:
                w = f"{r_weight.get(d, '---'):>5}"
                c = f"{r_cal.get(d, '---'):>5}"
                response += f"{d}: Peso {w} kg | Cal {c} kcal\n"

            last_check_in_str = profile.tdee_last_check_in if profile else "Nunca"
            response += f"""
Fator Atividade (Âncora): {profile.tdee_activity_factor or 1.45 if profile else 1.45}
Último Ajuste de Meta: {last_check_in_str}
... Applied fuzzy match.
=== INSTRUÇÃO PARA O TREINADOR ===
Analise os dados acima. Se os 'Lows' estiverem caindo consistentemente na taxa meta, mas o TDEE estimado ainda estiver baixo (lag do algoritmo), você pode concordar com o aluno e usar a tool 'force_target_update' para ajustar a meta agora.
"""
            return response

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to get metabolism data for %s: %s", user_email, e)
            return f"Erro ao buscar dados brutos de metabolismo: {str(e)}"

    return get_metabolism_data


def create_force_target_update_tool(database: MongoDatabase, user_email: str):
    """
    Factory function for the force_target_update tool.
    Allows the AI to manually override the target and reset the coaching clock.
    """

    @tool
    def force_target_update(target_calories: int) -> str:
        """
        Força a atualização da meta calórica diária do aluno.
        Use esta tool APENAS quando seu raciocínio matemático (baseado nos dados brutos)
        indicar que a meta atual está defasada e precisa de um ajuste imediato,
        ignorando a trava de 7 dias do sistema.

        Args:
            target_calories (int): A nova meta calórica sugerida.
        """
        try:
            profile = database.get_user_profile(user_email)
            if not profile:
                return "Perfil do aluno não encontrado."

            # Update target and clear last check-in to force immediate UI update
            fields = {
                "tdee_last_target": target_calories,
                "tdee_last_check_in": None
            }
            database.update_user_profile_fields(user_email, fields)

            logger.info(
                "AI forced target update for %s to %d kcal",
                user_email,
                target_calories
            )
            return (
                f"Meta calórica atualizada com sucesso para {target_calories} kcal. "
                "A alteração será visível imediatamente para o aluno."
            )

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to force target update for %s: %s", user_email, e)
            return f"Erro ao forçar atualização da meta: {str(e)}"

    return force_target_update


def create_update_tdee_params_tool(database: MongoDatabase, user_email: str):
    """
    Factory function to create an update_tdee_params tool with injected dependencies.
    """

    @tool
    def update_tdee_params(activity_factor: float) -> str:
        """
        Ajusta o fator de atividade usado no cálculo do TDEE adaptativo do aluno.

        Use quando o aluno reportar mudança SIGNIFICATIVA e PERMANENTE no nível
        de atividade do dia a dia (não treinos — esses já estão no TDEE adaptativo).

        Valores de referência:
        - 1.2   → Sedentário (trabalho de mesa, pouco movimento)
        - 1.375 → Levemente ativo (caminhadas, trabalho em pé)
        - 1.55  → Moderadamente ativo (trabalho físico leve)
        - 1.725 → Muito ativo (trabalho físico pesado, muito movimento)
        - 1.9   → Extremamente ativo (atleta, trabalho extenuante)

        IMPORTANTE: Caso o aluno tenha iniciado um novo plano de treinos INTENSO
        (ex: HIIT 5x/semana) ou esteja reclamando que a meta hoje é MUITO BAIXA em relação
        ao que ele está gastando de fato agora, você PODE usar esta tool para subir
        levemente o fator e, OBRIGATORIAMENTE, usar a tool 'reset_tdee_tracking'
        junto para resetar o passado.

        Exemplos válidos:
          - "Comecei a trabalhar em escritório" → 1.2
          - "Mudei de escritório para trabalho de pé" → 1.55

        Exemplos inválidos:
          - "Comecei a treinar 3x/semana" → NÃO ajustar (mude apenas mudanças muito bruscas)
        """
        try:
            if not isinstance(activity_factor, (int, float)):
                return (
                    "Erro: activity_factor deve ser um número entre 1.2 e 1.9. "
                    f"Recebido: {activity_factor}"
                )

            if activity_factor < 1.2 or activity_factor > 1.9:
                return (
                    f"Erro: activity_factor deve estar entre 1.2 e 1.9. "
                    f"Recebido: {activity_factor}. "
                    "Valores de referência: 1.2 (sedentário) até 1.9 (extremamente ativo)."
                )

            profile = database.get_user_profile(user_email)
            if not profile:
                return "Perfil do aluno não encontrado."

            old_factor = profile.tdee_activity_factor or 1.45
            profile.tdee_activity_factor = activity_factor
            database.save_user_profile(profile)

            activity_labels = {
                1.2: "sedentário",
                1.375: "levemente ativo",
                1.55: "moderadamente ativo",
                1.725: "muito ativo",
                1.9: "extremamente ativo",
            }
            label = activity_labels.get(activity_factor, f"{activity_factor}")

            logger.info(
                "User %s updated activity_factor from %s to %s",
                user_email,
                old_factor,
                activity_factor,
            )

            return (
                f"Fator de atividade atualizado com sucesso! "
                f"Novo fator: {activity_factor} ({label}). "
                f"O TDEE será recalculado no próximo check-in com este novo valor."
            )

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to update TDEE params for %s: %s", user_email, e)
            return f"Erro ao atualizar parâmetros de metabolismo: {str(e)}"

    return update_tdee_params

def create_reset_tdee_tracking_tool(database: MongoDatabase, user_email: str):
    """Factory function for the TDEE reset tool."""

    @tool
    def reset_tdee_tracking(start_date_iso: str) -> str:
        """
        Zera o histórico do algoritmo adaptativo de TDEE, descartando os dados anteriores
        à data informada no cálculo da Média Móvel. 
        
        USE ESTA TOOL quando o aluno reportar que mudou radicalmente sua rotina de 
        treinos/atividade física recentemente, e a meta calórica atual sugerida
        parece muito baixa ou incorreta por causa de um "atraso/lag" do algoritmo 
        (que ainda está puxando a média para baixo com dados de quando o aluno gastava menos).
        
        Args:
            start_date_iso (str): A data a partir da qual o algoritmo deve começar
                                  a considerar os dados para a média. Formato YYYY-MM-DD.
                                  Se a mudança foi hoje, passe a data de hoje.
        """
        try:
            profile = database.get_user_profile(user_email)
            if not profile:
                return "Perfil do aluno não encontrado."

            profile.tdee_start_date = start_date_iso
            database.save_user_profile(profile)

            logger.info(
                "User %s reset TDEE tracking from date %s",
                user_email,
                start_date_iso
            )

            return (
                f"Histórico adaptativo resetado com sucesso! O algoritmo agora usará "
                f"somente dados de dieta e peso a partir de {start_date_iso}. "
                f"A nova meta será recalculada imediatamente."
            )
        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to reset TDEE tracking for %s: %s", user_email, e)
            return f"Erro ao resetar histórico: {str(e)}"

    return reset_tdee_tracking
