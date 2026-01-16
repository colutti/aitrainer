from langchain_core.tools import tool
from src.core.logs import logger
from src.api.models.routine import HevyRoutine, HevyRoutineExercise, HevySet, HevyRepRange

def create_list_hevy_routines_tool(hevy_service, database, user_email: str):
    @tool
    def list_hevy_routines(page: int = 1, page_size: int = 10) -> str:
        """
        Lista as rotinas de treino do aluno no Hevy.
        Use quando o aluno perguntar "quais são minhas rotinas" ou "mostre meus treinos salvos".
        """
        profile = database.get_user_profile(user_email)
        if not profile or not profile.hevy_enabled or not profile.hevy_api_key:
            return "A integração com Hevy está desativada ou a chave API não está configurada. Por favor, ative-a nas configurações."

        import asyncio
        response = asyncio.run(hevy_service.get_routines(profile.hevy_api_key, page, page_size))
        
        if not response or not response.routines:
            return "Nenhuma rotina encontrada no Hevy."

        result = f"Encontrei {len(response.routines)} rotinas (Página {response.page}/{response.page_count}):\n\n"
        for i, r in enumerate(response.routines, 1):
            result += f"{i}. **{r.title}** (ID: {r.id})\n"
            if r.notes:
                result += f"   Notas: {r.notes}\n"
            exercises = [ex.exercise_template_id for ex in r.exercises]
            result += f"   Exercícios: {', '.join(exercises[:5])}"
            if len(exercises) > 5:
                result += "..."
            result += "\n\n"
        
        return result

    return list_hevy_routines

def create_create_hevy_routine_tool(hevy_service, database, user_email: str):
    @tool
    def create_hevy_routine(
        title: str,
        exercises: list[dict],
        notes: str | None = None,
        folder_id: int | None = None
    ) -> str:
        """
        Cria uma nova rotina no Hevy para o aluno.
        Use quando o aluno pedir para "criar uma rotina", "salvar esse treino como rotina" ou "planejar um treino".
        
        Args:
            title: Título da rotina.
            exercises: Lista de exercícios. Cada exercício deve ser um dict com:
                - exercise_template_id (str): ID do template do exercício (ex: "squat", "bench_press")
                - rest_seconds (int, opcional): Tempo de descanso.
                - notes (str, opcional): Notas do exercício.
                - sets (list[dict]): Lista de séries. Cada série deve ter:
                    - type (str): "normal", "warm_up", "drop_set", "failure"
                    - weight_kg (float, opcional)
                    - reps (int, opcional)
            notes: Notas gerais da rotina.
            folder_id: ID da pasta (opcional).
        """
        profile = database.get_user_profile(user_email)
        if not profile or not profile.hevy_enabled or not profile.hevy_api_key:
            return "A integração com Hevy está desativada. Não é possível criar rotinas."

        try:
            routine = HevyRoutine(
                title=title,
                notes=notes,
                folder_id=folder_id,
                exercises=[HevyRoutineExercise(**ex) for ex in exercises]
            )
            
            import asyncio
            result = asyncio.run(hevy_service.create_routine(profile.hevy_api_key, routine))
            
            if result:
                return f"Rotina '{result.title}' criada com sucesso no Hevy! (ID: {result.id})"
            return "Falha ao criar rotina no Hevy. Verifique os dados e tente novamente."
        except Exception as e:
            logger.error(f"Error in create_hevy_routine tool: {e}")
            return f"Erro técnico ao criar rotina: {str(e)}"

    return create_hevy_routine

def create_update_hevy_routine_tool(hevy_service, database, user_email: str):
    @tool
    def update_hevy_routine(
        routine_id: str,
        title: str | None = None,
        exercises: list[dict] | None = None,
        notes: str | None = None
    ) -> str:
        """
        Atualiza uma rotina existente no Hevy.
        Use quando o aluno pedir para "alterar", "editar" ou "mudar" uma rotina.
        
        VOCÊ DEVE PRIMEIRO LISTAR AS ROTINAS PARA OBTER O ID CORRETO.
        """
        profile = database.get_user_profile(user_email)
        if not profile or not profile.hevy_enabled or not profile.hevy_api_key:
            return "A integração com Hevy está desativada."

        import asyncio
        # First fetch current to preserve fields not being updated
        current = asyncio.run(hevy_service.get_routine_by_id(profile.hevy_api_key, routine_id))
        if not current:
            return f"Rotina com ID {routine_id} não encontrada."

        if title: current.title = title
        if notes: current.notes = notes
        if exercises:
            current.exercises = [HevyRoutineExercise(**ex) for ex in exercises]

        result = asyncio.run(hevy_service.update_routine(profile.hevy_api_key, routine_id, current))
        if result:
            return f"Rotina '{result.title}' atualizada com sucesso no Hevy!"
        return "Falha ao atualizar rotina no Hevy."

    return update_hevy_routine
