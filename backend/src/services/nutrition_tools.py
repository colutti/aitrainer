"""
LangChain tools for nutrition tracking.
"""

from datetime import datetime
from langchain_core.tools import tool
from src.core.logs import logger
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any


class SaveDailyNutritionInput(BaseModel):
    """Input schema for save_daily_nutrition tool."""
    
    calories: int = Field(description="Calorias totais (kcal)")
    protein_grams: float = Field(description="Proteínas totais (g)")
    carbs_grams: float = Field(description="Carboidratos totais (g)")
    fat_grams: float = Field(description="Gorduras totais (g)")
    fiber_grams: Optional[float] = Field(default=None, description="Fibras totais (g)")
    sugar_grams: Optional[float] = Field(default=None, description="Açúcar total (g)")
    sodium_mg: Optional[float] = Field(default=None, description="Sódio total (mg)")
    cholesterol_mg: Optional[float] = Field(default=None, description="Colesterol total (mg)")
    date: Optional[str] = Field(default=None, description="Data no formato ISO (YYYY-MM-DD). Se omitido, usa hoje")

    @field_validator('calories', mode='before')
    @classmethod
    def clean_calories(cls, v: Any) -> int:
        """Clean calories input (remove units, convert to int)."""
        if isinstance(v, str):
            clean = v.lower().replace('kcal', '').replace('cal', '').strip()
            clean = clean.replace(',', '.')
            return int(float(clean))
        return int(v)

    @field_validator('protein_grams', 'carbs_grams', 'fat_grams', 'fiber_grams', 
                     'sugar_grams', 'sodium_mg', 'cholesterol_mg', mode='before')
    @classmethod
    def clean_numeric(cls, v: Any) -> Optional[float]:
        """Clean numeric input (remove units, convert commas to dots)."""
        if v is None:
            return None
        if isinstance(v, str):
            clean = v.lower().replace('g', '').replace('mg', '').strip()
            clean = clean.replace(',', '.')
            return float(clean)
        return float(v)



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

    def parse_numeric(value: int | float | str | None) -> float | None:
        """Helper to strict parse numeric values, cleaning 'g', 'mg', etc."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remove common units and whitespace
            clean = value.lower().replace('g', '').replace('mg', '').replace('kcal', '').strip()
            # Handle comma as decimal separator if present
            clean = clean.replace(',', '.')
            try:
                return float(clean)
            except ValueError:
                return None
        return None

    @tool(args_schema=SaveDailyNutritionInput)
    def save_daily_nutrition(
        calories: int,
        protein_grams: float,
        carbs_grams: float,
        fat_grams: float,
        fiber_grams: Optional[float] = None,
        sugar_grams: Optional[float] = None,
        sodium_mg: Optional[float] = None,
        cholesterol_mg: Optional[float] = None,
        date: Optional[str] = None,
    ) -> str:
        """
        Salva o resumo nutricional DIÁRIO do aluno.
        Geralmente usado quando o aluno reporta o que comeu no dia (ex: dados do MyFitnessPal).
        Se já existe log para a data, ATUALIZA os dados (upsert).

        EXTRAIA os TOTAIS do texto do aluno (linha "TOTAIS" se for tabela).

        Args:
            calories (int | str): Calorias totais (kcal).
            protein_grams (float | str): Proteínas totais (g).
            carbs_grams (float | str): Carboidratos totais (g).
            fat_grams (float | str): Gorduras totais (g).
            fiber_grams (float | str, opcional): Fibras totais (g).
            sugar_grams (float | str, opcional): Açúcar total (g).
            sodium_mg (float | str, opcional): Sódio total (mg).
            cholesterol_mg (float | str, opcional): Colesterol total (mg).
            date (str, opcional): Data no formato ISO (YYYY-MM-DD). Se omitido, usa hoje.

        Returns:
            Confirmação de que o log foi salvo/atualizado.
        """
        try:
            # DEBUG LOGGING requested by user
            logger.info(f"TOOL CALL: save_daily_nutrition")
            logger.info(f"RAW INPUTS - Cals: {calories}, P: {protein_grams}, C: {carbs_grams}, F: {fat_grams}, Date: {date}")

            # Parse and clean inputs
            cal_val = parse_numeric(calories)
            prot_val = parse_numeric(protein_grams)
            carb_val = parse_numeric(carbs_grams)
            fat_val = parse_numeric(fat_grams)
            
            logger.info(f"PARSED VALUES - Cals: {cal_val}, P: {prot_val}, C: {carb_val}, F: {fat_val}")

            fib_val = parse_numeric(fiber_grams)
            sug_val = parse_numeric(sugar_grams)
            sod_val = parse_numeric(sodium_mg)
            chol_val = parse_numeric(cholesterol_mg)

            # Validate required fields after parsing
            if cal_val is None or prot_val is None or carb_val is None or fat_val is None:
                return "Erro: Valores numéricos inválidos para calorias ou macros."

            if date:
                try:
                    log_date = datetime.fromisoformat(date)
                except ValueError:
                    try:
                        log_date = datetime.strptime(date, "%Y-%m-%d")
                    except ValueError:
                         # Try with slash
                        try:
                            log_date = datetime.strptime(date, "%d/%m/%Y")
                        except ValueError:
                            return f"Erro: Formato de data inválido '{date}'. Use YYYY-MM-DD."
            else:
                log_date = datetime.now()

            log = NutritionLog(
                user_email=user_email,
                date=log_date,
                calories=int(cal_val),
                protein_grams=prot_val,
                carbs_grams=carb_val,
                fat_grams=fat_val,
                fiber_grams=fib_val,
                sugar_grams=sug_val,
                sodium_mg=sod_val,
                cholesterol_mg=chol_val,
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
