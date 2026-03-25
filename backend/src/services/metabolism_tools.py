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
            tdee_data = AdaptiveTDEEService(database).calculate_tdee(
                user_email, lookback_weeks=4
            )
            profile = database.get_user_profile(user_email)

            # Extract raw trends
            trends = {
                "weight": tdee_data.get("weight_trend", []),
                "calorie": tdee_data.get("calorie_trend", []),
            }

            # Calculate Weekly Lows (3 lowest weights)
            today = date.today()

            def get_avg_lows(days_offset_start, days_offset_end):
                d_start = today - timedelta(days=days_offset_start)
                d_end = today - timedelta(days=days_offset_end)
                period_weights = [
                    w["weight"]
                    for w in trends["weight"]
                    if w["weight"] and d_end <= date.fromisoformat(w["date"]) <= d_start
                ]
                if not period_weights:
                    return None
                lowest_3 = sorted(period_weights)[:3]
                return sum(lowest_3) / len(lowest_3)

            current_lows = get_avg_lows(0, 6)
            previous_lows = get_avg_lows(7, 13)

            lows_delta = (
                (current_lows - previous_lows)
                if (current_lows and previous_lows)
                else None
            )

            # Build detailed raw response
            response = f"""=== METABOLISMO: DADOS BRUTOS (Últimos 30 dias) ===

TDEE Estimado: {tdee_data.get("tdee")} kcal
Meta Diária Atual: {tdee_data.get("daily_target")} kcal
Objetivo: {tdee_data.get("goal_type")} ({tdee_data.get("goal_weekly_rate")} kg/semana)

-- AUDITORIA DE LOWS (Média dos 3 menores pesos) --
Semana Atual: {f"{current_lows:.2f} kg" if current_lows else "N/A"}
Semana Anterior: {f"{previous_lows:.2f} kg" if previous_lows else "N/A"}
Delta Lows: {f"{lows_delta:+.2f} kg" if lows_delta is not None else "N/A"}

-- SÉRIE TEMPORAL (Peso e Calorias) --
"""
            # Add last 14 days of raw data for concise AI context
            r_weight = {w["date"]: w["weight"] for w in trends["weight"]}
            r_cal = {c["date"]: c["calories"] for c in trends["calorie"]}

            all_dates = sorted(
                set(list(r_weight.keys()) + list(r_cal.keys())), reverse=True
            )[:14]
            for d in all_dates:
                response += (
                    f"{d}: Peso {r_weight.get(d, '---'):>5} kg | "
                    f"Cal {r_cal.get(d, '---'):>5} kcal\n"
                )

            last_check_in_str = profile.tdee_last_check_in if profile else "Nunca"
            response += f"""
Fator Atividade (Âncora): {profile.tdee_activity_factor or 1.45 if profile else 1.45}
Último Ajuste de Meta: {last_check_in_str}
... Applied fuzzy match.
=== COMO O SISTEMA V4 DE TDEE FUNCIONA (Contexto para você) ===
O algoritmo não é uma média simples. Ele usa:
1. Span Dinâmico: A inércia do cálculo varia de 7 a 30 dias. Se o aluno perde peso de forma linear, a janela cai para 7 dias (reação rápida). Se há muito sobe/desce, vai para 30 dias (proteção contra ruído).
2. Dampening de Água: Quedas abruptas na primeira semana (>1.5kg) têm seu impacto energético reduzido (água/glicogênio) para não causar picos falsos no Gasto Diário.
3. Imputação de Gaps: Se o aluno não logar calorias, o sistema preenche as lacunas usando a Meta, evitando que o algoritmo congele.

=== INSTRUÇÃO PARA O TREINADOR ===
Use o conhecimento acima para explicar o comportamento do app ao aluno. Se os 'Lows' estiverem caindo consistentemente na taxa meta, mas o TDEE estimado ainda estiver baixo (mesmo com Span rápido de 7 dias), você deve ajustar o fator de atividade do aluno usando a tool 'update_tdee_params' passando reset_tracking=True para forçar o recalculo imediato.
"""
            return response

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to get metabolism data for %s: %s", user_email, e)
            return f"Erro ao buscar dados brutos de metabolismo: {str(e)}"

    return get_metabolism_data


def create_update_tdee_params_tool(database: MongoDatabase, user_email: str):
    """
    Factory function to create an update_tdee_params tool with injected dependencies.
    """

    @tool
    def update_tdee_params(activity_factor: float, reset_tracking: bool = False) -> str:
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

        IMPORTANTE: Caso o aluno tenha iniciado um novo plano de treinos INTENSO ou esteja
        reclamando que a meta hoje é MUITO BAIXA/ALTA em relação ao que ele está gastando
        de fato agora (lag do algoritmo), você DEVE usar o parâmetro `reset_tracking=True`
        para zerar o histórico passado e forçar o recalculo imediato da meta com a nova base.

        Exemplos válidos:
          - "Comecei a trabalhar em escritório" → 1.2
          - "Mudei de escritório para trabalho de pé" → 1.55

        Exemplos inválidos:
          - "Comecei a treinar 3x/semana" → NÃO ajustar (mude apenas mudanças muito bruscas)

        Args:
            activity_factor (float): O novo fator de atividade.
            reset_tracking (bool): Se verdadeiro, descarta o histórico anterior
                e recomeça a média móvel a partir de hoje.
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

            reset_msg = ""
            if reset_tracking:
                profile.tdee_start_date = date.today().isoformat()
                reset_msg = (
                    " e o histórico adaptativo foi resetado "
                    "para forçar recalculo imediato"
                )

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
                "User %s updated activity_factor from %s to %s (reset_tracking=%s)",
                user_email,
                old_factor,
                activity_factor,
                reset_tracking,
            )

            return (
                f"Fator de atividade atualizado com sucesso para "
                f"{activity_factor} ({label}){reset_msg}. "
                f"O TDEE será recalculado com este novo valor."
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
                "User %s reset TDEE tracking from date %s", user_email, start_date_iso
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
