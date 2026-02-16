"""
LangChain tools for workout tracking.
"""

from datetime import datetime
from langchain_core.tools import tool
from src.core.logs import logger
from src.api.models.workout_log import WorkoutLog, ExerciseLog


def create_save_workout_tool(database, user_email: str):
    """
    Factory function to create a save_workout tool with injected dependencies.
    """

    @tool
    def save_workout(
        workout_type: str,
        exercises: list[dict],
        duration_minutes: int | None = None,
        date: str | None = None,
    ) -> str:
        """
        Salva um treino executado pelo aluno no banco de dados.

        Use APENAS para treinos (musculação, cardio, spinning, etc).
        NÃO salve: descanso, água, humor, sono, atividades do dia-a-dia.

        Argumentos:
        - workout_type: Tipo de treino. Ex: "Pernas", "Peito"
        - exercises: Lista de dicts com 'name', 'sets', 'reps_per_set', 'weights_per_set', 'distance_meters_per_set', 'duration_seconds_per_set'
        - duration_minutes: Duração total em minutos (opcional)
        - date: Data do treino no formato ISO (YYYY-MM-DD). Default: hoje.

        Exemplos de exercises:
        - Força: {name: "Supino", sets: 3, reps_per_set: [10, 8, 6], weights_per_set: [80, 85, 90]}
        - Cardio: {name: "Esteira", sets: 1, distance_meters_per_set: [1000], duration_seconds_per_set: [900]}
        - Misto: {name: "Remo", sets: 2, reps_per_set: [15, 12], distance_meters_per_set: [500, 600], duration_seconds_per_set: [120, 140]}
        """
        try:
            log_date = _parse_date(date)
            exercise_logs = _parse_exercises(exercises)

            workout = WorkoutLog(
                user_email=user_email,
                date=log_date,
                workout_type=workout_type,
                exercises=exercise_logs,
                duration_minutes=duration_minutes,
            )

            workout_id = database.save_workout_log(workout)
            logger.info("Saved workout for %s: %s", user_email, workout_id)
            date_fmt = log_date.strftime('%d/%m/%Y')
            return f"Treino de {date_fmt} registrado com sucesso! (ID: {workout_id})"

        except (ValueError, TypeError) as e:
            logger.error("Input error saving workout for %s: %s", user_email, e)
            return f"Erro nos dados: {str(e)}"
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to save workout for user %s: %s", user_email, e)
            return "Erro ao registrar treino. Tente novamente."

    return save_workout


def _parse_date(date_str: str | None) -> datetime:
    """Helper to parse date string into datetime object."""
    if not date_str:
        return datetime.now()
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            logger.warning("Invalid date format '%s', using today", date_str)
            return datetime.now()


def _parse_exercises(exercises: list[dict]) -> list[ExerciseLog]:
    """Helper to parse exercise dictionaries into ExerciseLog objects."""
    exercise_logs = []
    for ex in exercises:
        name = ex.get("name", "Exercício")
        sets = ex.get("sets", 1)

        # Suporta novo formato (reps_per_set) e formato antigo (reps)
        reps_per_set = ex.get("reps_per_set")
        if reps_per_set is None:
            reps = ex.get("reps", 1)
            reps_per_set = [reps] * sets

        # Suporta novo formato (weights_per_set) e formato antigo (weight_kg)
        weights_per_set = ex.get("weights_per_set")
        if weights_per_set is None:
            weight_kg = ex.get("weight_kg")
            weights_per_set = [weight_kg] * sets if weight_kg is not None else []

        # Novos campos de cardio
        distance_meters_per_set = ex.get("distance_meters_per_set", [])
        duration_seconds_per_set = ex.get("duration_seconds_per_set", [])

        exercise_logs.append(
            ExerciseLog(
                name=name,
                sets=sets,
                reps_per_set=reps_per_set,
                weights_per_set=weights_per_set,
                distance_meters_per_set=distance_meters_per_set,
                duration_seconds_per_set=duration_seconds_per_set,
            )
        )
    return exercise_logs


def create_get_workouts_tool(database, user_email: str):
    """
    Factory function to create a get_workouts tool with injected dependencies.
    """

    @tool
    def get_workouts(limit: int = 5) -> str:
        """
        Busca os últimos treinos do aluno no banco de dados.
        """
        try:
            workouts = database.get_workout_logs(user_email, limit=limit)
            if not workouts:
                return "Nenhum treino registrado ainda."

            result = f"Encontrei {len(workouts)} treino(s):\n\n"
            for i, w in enumerate(workouts, 1):
                date_str = w.date.strftime("%d/%m/%Y %H:%M")
                ex_summary = _format_exercises_summary(w.exercises)
                duration = f" ({w.duration_minutes}min)" if w.duration_minutes else ""
                w_type = w.workout_type or 'Treino'
                result += f"{i}. [{w_type}] {date_str}{duration}\n"
                result += f"   Exercícios: {ex_summary}\n\n"

            logger.info("Retrieved %d workouts for user %s", len(workouts), user_email)
            return result
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to get workouts for user %s: %s", user_email, e)
            return "Erro ao buscar treinos. Tente novamente."

    return get_workouts


def _format_exercises_summary(exercises: list[ExerciseLog]) -> str:
    """Helper to format exercise list into a readable summary string."""
    ex_details = []
    for e in exercises:
        # Se todos os reps e pesos são iguais, formato simplificado
        uniform_reps = all(r == e.reps_per_set[0] for r in e.reps_per_set)
        uniform_weights = not e.weights_per_set or all(
            w == e.weights_per_set[0] for w in e.weights_per_set
        )

        if uniform_reps and uniform_weights:
            weight_str = f" @ {e.weights_per_set[0]}kg" if e.weights_per_set else ""
            ex_details.append(f"{e.sets}x{e.reps_per_set[0]} {e.name}{weight_str}")
        else:
            series = []
            for idx, reps in enumerate(e.reps_per_set):
                if e.weights_per_set and idx < len(e.weights_per_set):
                    series.append(f"{reps}@{e.weights_per_set[idx]}kg")
                else:
                    series.append(f"{reps} reps")
            ex_details.append(f"{e.name}: {', '.join(series)}")

    return "; ".join(ex_details)
