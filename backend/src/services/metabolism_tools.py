"""
LangChain tools for TDEE and metabolism data access.
Provides AI trainer access to adaptive TDEE calculations with full algorithm documentation.
"""

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
        Consulta o TDEE adaptativo real do aluno e a meta calórica diária.

        USE ESTA TOOL SEMPRE que for falar sobre:
        - Calorias para comer (meta, déficit, superávit)
        - Metabolismo, TDEE, gasto energético
        - Progresso de peso em relação ao objetivo
        - Recomendações de nutrição personalizadas

        NUNCA use fórmulas padrão (Harris-Benedict, Mifflin-St Jeor, etc.)
        para estimar calorias. Os dados desta tool são sempre mais precisos
        porque usam dados reais do aluno.
        """
        try:
            tdee_service = AdaptiveTDEEService(database)
            tdee_data = tdee_service.calculate_tdee(user_email)
            profile = database.get_user_profile(user_email)

            response = f"""=== METABOLISMO ADAPTATIVO DO ALUNO ===

TDEE atual: {tdee_data.get('tdee', 'N/A')} kcal
  → Calculado a partir de {tdee_data.get('weight_logs_count', '?')} pesagens de dados reais
  → Confiança: {tdee_data.get('confidence', 'desconhecida').upper()}
    ({tdee_data.get('confidence_reason', 'dados insuficientes')})

Meta diária: {tdee_data.get('daily_target', 'N/A')} kcal
  → Balanço energético: {tdee_data.get('energy_balance', 0):.0f} kcal
  → Status: {tdee_data.get('status', 'desconhecido').upper()}
  → Objetivo: {tdee_data.get('goal_type', 'manter')} peso
    ({tdee_data.get('goal_weekly_rate', 0)} kg/semana)

Fator de atividade atual: {profile.tdee_activity_factor or 1.45 if profile else 1.45}
  → Usado como âncora inicial do cálculo
  → Pode ser ajustado via update_tdee_params() se o nível de atividade mudou

=== COMO ESTE TDEE É CALCULADO ===

Algoritmo: Adaptativo v3 (baseado no método MacroFactor / Stronger by Science)

Fórmula central (janela de 7 dias):
  TDEE_obs = média_calorias_7d − (Δpeso_tendência_7d ÷ 7) × energia_por_kg

Suavização final:
  EMA de 21 dias sobre as observações diárias
  Ancorada no prior: BMR × fator_atividade

Energia por kg de peso (modelo Forbes/Hall, 1987):
  fat_fraction = 0.75 + (gordura_corporal% − 25) × 0.005
  energia_por_kg = fat_fraction × 9400 + (1 − fat_fraction) × 1800
  Fallback sem dados de composição: 7700 kcal/kg

Peso suavizado: EMA 21 dias + interpolação linear (gaps ≤ 14 dias)

Por que é mais preciso que Harris-Benedict / Mifflin-St Jeor:
  Fórmulas estáticas erram ±20-30% pois ignoram adaptação metabólica.
  Este algoritmo usa dados reais do aluno e converge para o valor verdadeiro.

Referências:
  - Hall et al. (2012) "Quantification of the effect of energy imbalance on bodyweight"
  - Forbes (1987) "Human Body Composition"
  - MacroFactor methodology (https://macrofactorapp.com)

=== INSTRUÇÃO PARA O TREINADOR ===
Baseie TODAS as recomendações calóricas nos valores acima.
Se o aluno questionar os números, explique que são calculados
a partir do comportamento real do peso e calorias consumidas —
não de estimativas genéricas.
"""
            return response

        except Exception as e:
            logger.error("Failed to get metabolism data for %s: %s", user_email, e)
            return (
                "Erro ao buscar dados de metabolismo. "
                "Certifique-se de que há histórico de peso e nutrição registrado."
            )

    return get_metabolism_data


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

        IMPORTANTE: Não ajuste por causa de treinos (já capturados pelo adaptativo).
        Ajuste apenas quando o ESTILO DE VIDA base mudar.

        Exemplos válidos:
          - "Comecei a trabalhar em escritório" → 1.2
          - "Mudei de escritório para trabalho de pé" → 1.55

        Exemplos inválidos:
          - "Comecei a treinar 3x/semana" → NÃO ajustar (adaptativo já captura)
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

        except Exception as e:
            logger.error("Failed to update TDEE params for %s: %s", user_email, e)
            return f"Erro ao atualizar parâmetros de metabolismo: {str(e)}"

    return update_tdee_params
