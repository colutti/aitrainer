"""
LangChain tools for workout tracking.
"""

from langchain_core.tools import tool
from src.core.logs import logger


def create_save_workout_tool(database, user_email: str):
    """
    Factory function to create a save_workout tool with injected dependencies.

    Args:
        database: MongoDatabase instance for saving workouts.
        user_email: Email of the user whose workout is being saved.

    Returns:
        A LangChain tool function for saving workouts.
    """
    # Import here to avoid circular imports
    from src.api.models.workout_log import WorkoutLog, ExerciseLog

    @tool
    def save_workout(
        workout_type: str,
        exercises: list[dict],
        duration_minutes: int | None = None,
    ) -> str:
        """
        Salva um treino executado pelo aluno no banco de dados.
        Use esta ferramenta quando o aluno reportar exercícios que ele fez.
        EXTRAIA os dados do texto do aluno para preencher os argumentos.

        Args:
            workout_type: Tipo de treino. Exemplos: "Pernas", "Peito", "Costas", "Braços", "Full Body"
            exercises: Lista de dicionários com exercícios. Cada dict deve ter:
                - name (str): Nome do exercício. Ex: "agachamento", "leg press", "supino"
                - sets (int): Número de séries. Ex: 4
                - reps (int): Número de repetições. Ex: 10
                - weight_kg (float, opcional): Peso em kg. Ex: 80.0
            duration_minutes: Duração total em minutos (opcional)

        Exemplo de chamada:
            workout_type="Pernas"
            exercises=[
                {"name": "agachamento", "sets": 4, "reps": 10, "weight_kg": 80},
                {"name": "leg press", "sets": 3, "reps": 12, "weight_kg": 150}
            ]

        Returns:
            Confirmação de que o treino foi salvo.
        """
        try:
            exercise_logs = []
            for ex in exercises:
                exercise_logs.append(
                    ExerciseLog(
                        name=ex.get("name", "Exercício"),
                        sets=ex.get("sets", 1),
                        reps=ex.get("reps", 1),
                        weight_kg=ex.get("weight_kg"),
                    )
                )

            workout = WorkoutLog(
                user_email=user_email,
                workout_type=workout_type,
                exercises=exercise_logs,
                duration_minutes=duration_minutes,
            )

            workout_id = database.save_workout_log(workout)
            logger.info(
                "Saved workout for user %s: %s exercises, type=%s",
                user_email,
                len(exercise_logs),
                workout_type,
            )
            return f"Treino registrado com sucesso! (ID: {workout_id})"

        except Exception as e:
            logger.error("Failed to save workout for user %s: %s", user_email, e)
            return "Erro ao registrar treino. Tente novamente."

    return save_workout


def create_get_workouts_tool(database, user_email: str):
    """
    Factory function to create a get_workouts tool with injected dependencies.

    Args:
        database: MongoDatabase instance for retrieving workouts.
        user_email: Email of the user whose workouts are being retrieved.

    Returns:
        A LangChain tool function for retrieving workouts.
    """

    @tool
    def get_workouts(limit: int = 5) -> str:
        """
        Busca os últimos treinos do aluno no banco de dados.
        Use quando o aluno perguntar sobre seu histórico de treinos.

        Args:
            limit: Número máximo de treinos a retornar (default: 5)

        Returns:
            Resumo formatado dos treinos encontrados.
        """
        try:
            workouts = database.get_workout_logs(user_email, limit=limit)

            if not workouts:
                return "Nenhum treino registrado ainda."

            # Format for presentation
            result = f"Encontrei {len(workouts)} treino(s):\n\n"
            for i, w in enumerate(workouts, 1):
                date_str = w.date.strftime("%d/%m/%Y %H:%M")
                exercises = ", ".join(
                    [f"{e.sets}x{e.reps} {e.name}" for e in w.exercises]
                )
                duration = f" ({w.duration_minutes}min)" if w.duration_minutes else ""
                result += f"{i}. [{w.workout_type or 'Treino'}] {date_str}{duration}\n"
                result += f"   Exercícios: {exercises}\n\n"

            logger.info(
                "Retrieved %d workouts for user %s", len(workouts), user_email
            )
            return result

        except Exception as e:
            logger.error("Failed to get workouts for user %s: %s", user_email, e)
            return "Erro ao buscar treinos. Tente novamente."

    return get_workouts
