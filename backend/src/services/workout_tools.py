"""
LangChain tools for workout tracking.
"""

from datetime import datetime
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
        date: str | None = None,
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
                - reps_per_set (list[int]): Repetições por série. Ex: [10, 10, 8, 8]
                - weights_per_set (list[float], opcional): Pesos por série em kg. Ex: [80, 80, 85, 85]
            duration_minutes: Duração total em minutos (opcional)
            date: Data do treino no formato ISO (YYYY-MM-DD). Se omitido, usa hoje.
                  Exemplos: "2024-01-15" para 15 de janeiro. "ontem" deve ser convertido para data real.

        Exemplo de chamada:
            workout_type="Pernas"
            exercises=[
                {"name": "agachamento", "sets": 4, "reps_per_set": [10, 10, 8, 8], "weights_per_set": [80, 80, 85, 85]},
                {"name": "leg press", "sets": 3, "reps_per_set": [12, 12, 12], "weights_per_set": [150, 150, 150]}
            ]
            date="2024-01-14"

        Returns:
            Confirmação de que o treino foi salvo.
        """
        try:
            # Parse date parameter
            if date:
                try:
                    log_date = datetime.fromisoformat(date)
                except ValueError:
                    try:
                        log_date = datetime.strptime(date, "%Y-%m-%d")
                    except ValueError:
                        logger.warning("Invalid date format '%s', using today", date)
                        log_date = datetime.now()
            else:
                log_date = datetime.now()

            exercise_logs = []
            for ex in exercises:
                name = ex.get("name", "Exercício")
                sets = ex.get("sets", 1)
                
                # Suporta novo formato (reps_per_set) e formato antigo (reps)
                reps_per_set = ex.get("reps_per_set")
                if reps_per_set is None:
                    # Formato antigo: converter reps único para lista
                    reps = ex.get("reps", 1)
                    reps_per_set = [reps] * sets
                
                # Suporta novo formato (weights_per_set) e formato antigo (weight_kg)
                weights_per_set = ex.get("weights_per_set")
                if weights_per_set is None:
                    weight_kg = ex.get("weight_kg")
                    if weight_kg is not None:
                        weights_per_set = [weight_kg] * sets
                    else:
                        weights_per_set = []
                
                exercise_logs.append(
                    ExerciseLog(
                        name=name,
                        sets=sets,
                        reps_per_set=reps_per_set,
                        weights_per_set=weights_per_set,
                    )
                )

            workout = WorkoutLog(
                user_email=user_email,
                date=log_date,
                workout_type=workout_type,
                exercises=exercise_logs,
                duration_minutes=duration_minutes,
            )

            workout_id = database.save_workout_log(workout)
            logger.info(
                "Saved workout for user %s: %s exercises, type=%s, date=%s",
                user_email,
                len(exercise_logs),
                workout_type,
                log_date.strftime("%Y-%m-%d")
            )
            return f"Treino de {log_date.strftime('%d/%m/%Y')} registrado com sucesso! (ID: {workout_id})"

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
                
                # Formatar exercícios com detalhes por série
                ex_details = []
                for e in w.exercises:
                    # Se todos os reps e pesos são iguais, formato simplificado
                    uniform_reps = all(r == e.reps_per_set[0] for r in e.reps_per_set)
                    uniform_weights = (not e.weights_per_set or 
                                     all(w == e.weights_per_set[0] for w in e.weights_per_set))
                    
                    if uniform_reps and uniform_weights:
                        # Formato simples: "3x10 Supino @ 80kg"
                        weight_str = f" @ {e.weights_per_set[0]}kg" if e.weights_per_set else ""
                        ex_details.append(f"{e.sets}x{e.reps_per_set[0]} {e.name}{weight_str}")
                    else:
                        # Formato detalhado: "Supino: 10@80kg, 10@85kg, 8@85kg"
                        series = []
                        for idx, reps in enumerate(e.reps_per_set):
                            if e.weights_per_set and idx < len(e.weights_per_set):
                                series.append(f"{reps}@{e.weights_per_set[idx]}kg")
                            else:
                                series.append(f"{reps} reps")
                        ex_details.append(f"{e.name}: {', '.join(series)}")
                
                exercises = "; ".join(ex_details)
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
