"""Read-only tool for fetching the training section from the active plan."""

import json

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class PlanTrainingInput(BaseModel):
    """Input schema for get_plan_training_program."""

    output_format: str = Field(
        default="text",
        alias="format",
        serialization_alias="format",
        description="Formato de saída: 'text' para legível ou 'json' para estruturado",
    )


def create_get_plan_training_program_tool(database, user_email: str):
    """Returns only the training section from the user's plan."""

    @tool(args_schema=PlanTrainingInput)
    def get_plan_training_program(output_format: str = "text") -> str:
        """Retorna a secao de treino salva no plano ativo do usuario.
        Use esta ferramenta quando o usuario perguntar sobre:
        - "qual e o meu treino/rotina"
        - "quais sao os exercicios do meu treino"
        - "me mostre as series e repeticoes do meu plano"
        - "qual treino devo fazer hoje"
        - qualquer pergunta sobre exercicios, series, repeticoes, splits ou
          agenda semanal de treino salvos no plano.
        Retorna split, frequencia, rotinas, exercicios, series e repeticoes.
        NAO retorna dados de nutricao, objetivo ou outras secoes do plano."""
        plan = database.get_plan(user_email)
        if plan is None:
            return "Nenhum programa de treino salvo no plano."
        tp = plan.training
        if output_format == "json":
            return json.dumps(tp.model_dump(), ensure_ascii=False, indent=2)
        lines = []
        lines.append(f"Split: {tp.split_name}")
        lines.append(f"Frequencia semanal: {tp.frequency_per_week} dias")
        if tp.session_duration_min:
            lines.append(f"Duracao por sessao: {tp.session_duration_min} min")
        lines.append("")
        for r in tp.routines:
            lines.append(f"--- {r.name} ---")
            for ex in r.exercises:
                reps = f"{ex.rep_range.min_reps}-{ex.rep_range.max_reps}"
                load = ex.intensity.target or ""
                notes = ex.notes or ""
                extra = f" - {load}" if load else ""
                extra += f" ({notes})" if notes else ""
                lines.append(f"  {ex.name}: {ex.sets}x{reps}{extra}")
            lines.append("")
        if tp.weekly_schedule:
            lines.append("Agenda semanal:")
            days_pt = {
                "monday": "Segunda", "tuesday": "Terca", "wednesday": "Quarta",
                "thursday": "Quinta", "friday": "Sexta", "saturday": "Sabado",
                "sunday": "Domingo",
            }
            for item in tp.weekly_schedule:
                day_pt = days_pt.get(item.day, item.day)
                routine_name = next(
                    (r.name for r in tp.routines if r.id == item.routine_id),
                    item.routine_id,
                )
                lines.append(f"  {day_pt}: {routine_name}")
        return "\n".join(lines)

    return get_plan_training_program
