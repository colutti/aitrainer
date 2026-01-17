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

def create_search_hevy_exercises_tool(hevy_service, database, user_email: str):
    @tool
    def search_hevy_exercises(query: str) -> str:
        """
        Pesquisa o catálogo de exercícios do Hevy para encontrar o `exercise_template_id` correto.
        VOCÊ DEVE USAR ESTA FERRAMENTA ANTES DE CRIAR OU EDITAR UMA ROTINA para garantir que os IDs estão corretos.
        Exemplo de query: "supino", "agachamento", "leg press".
        """
        profile = database.get_user_profile(user_email)
        if not profile or not profile.hevy_enabled or not profile.hevy_api_key:
            return "Integração desativada."

        import asyncio
        # Fetch ALL exercise templates to avoid missing data from first page only
        all_templates = asyncio.run(hevy_service.get_all_exercise_templates(profile.hevy_api_key))
        
        if not all_templates:
            return "Nenhum exercício encontrado no catálogo do Hevy."

        # logic: exact match first, then all words match
        query = query.lower().replace("-", " ") # Basic normalization
        parts = query.split()
        
        exact_matches = [ex for ex in all_templates if query == ex.title.lower().replace("-", " ")]
        all_words_matches = [
            ex for ex in all_templates 
            if all(p in ex.title.lower().replace("-", " ") for p in parts)
        ]
        
        # Merge and remove duplicates (preserving order)
        matches = exact_matches + [m for m in all_words_matches if m not in exact_matches]

        if not matches:
            # Last resort: partial muscle match
            matches = [ex for ex in all_templates if query in (ex.primary_muscle_group or "").lower()]

        if not matches:
            return f"Nenhum exercício encontrado para '{query}'. Tente usar o nome em inglês ou termos parciais (Ex: 'Leg Press' em vez de 'Prensa')."

        # Limit to top 5 most relevant
        top_matches = matches[:5]
        result = f"Encontrei {len(matches)} exercício(s) para '{query}':\n\n"
        for ex in top_matches:
            result += f"• {ex.title} → ID: `{ex.id}`\n"
        
        if len(matches) > 5:
            result += f"\n... e mais {len(matches) - 5} opções. Refine a busca se necessário."
        
        return result

    return search_hevy_exercises

def create_create_hevy_routine_tool(hevy_service, database, user_email: str):
    @tool
    def create_hevy_routine(
        title: str,
        exercises: list[dict],
        notes: str | None = None,
        folder_id: int | None = None
    ) -> str:
        """
        Cria uma nova rotina no Hevy.
        
        Argumento `exercises` deve ser uma lista de dicionários:
        [
          {
            "exercise_template_id": "0EB695C9", 
            "notes": "Foco em cadência",
            "sets": [{"type": "normal", "weight_kg": 100, "reps": 10}]
          }
        ]

        IMPORTANTE: 
        1. Use `search_hevy_exercises` primeiro para obter os IDs reais.
        2. `exercises` NÃO PODE estar vazio. 
        """
        if not title:
            return "O título da rotina é obrigatório."
        if not exercises:
            return "A rotina deve conter pelo menos um exercício. Use `search_hevy_exercises` primeiro."

        profile = database.get_user_profile(user_email)
        if not profile or not profile.hevy_enabled or not profile.hevy_api_key:
            return "Integração desativada."

        try:
            # Validate and clean folder_id
            clean_folder_id = None
            if folder_id is not None:
                try:
                    clean_folder_id = int(folder_id)
                except (ValueError, TypeError):
                    clean_folder_id = None

            routine_exercises = []
            for ex in exercises:
                if not ex.get("exercise_template_id"):
                    return f"Exercício inválido: faltando `exercise_template_id`. Use `search_hevy_exercises`."
                
                # Default empty sets if missing
                if not ex.get("sets"):
                    ex["sets"] = [{"type": "normal", "weight_kg": 0, "reps": 10}]
                
                routine_exercises.append(HevyRoutineExercise(**ex))

            routine = HevyRoutine(
                title=title,
                notes=notes,
                folder_id=clean_folder_id,
                exercises=routine_exercises
            )
            
            import asyncio
            result = asyncio.run(hevy_service.create_routine(profile.hevy_api_key, routine))
            
            if result:
                return f"Rotina '{result.title}' criada com sucesso! ID: {result.id}"
            return "Falha na criação. Verifique se os exercícios e o folder_id estão corretos."
        except Exception as e:
            logger.error(f"Error in create_hevy_routine tool: {e}")
            return f"Erro ao criar rotina: {str(e)}"

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
        
        IMPORTANTE: 
        1. Você DEVE fornecer o `routine_id` (use `list_hevy_routines` para encontrar).
        2. Se alterar exercícios, use `search_hevy_exercises` para validar os IDs.
        """
        if not routine_id:
            return "ID da rotina é obrigatório para atualização."

        profile = database.get_user_profile(user_email)
        if not profile or not profile.hevy_enabled or not profile.hevy_api_key:
            return "Integração desativada."

        import asyncio
        try:
            # Fetch current to preserve fields not being updated
            current = asyncio.run(hevy_service.get_routine_by_id(profile.hevy_api_key, routine_id))
            if not current:
                return f"Rotina com ID {routine_id} não encontrada no Hevy."

            if title: current.title = title
            if notes: current.notes = notes
            if exercises:
                new_exercises = []
                for ex in exercises:
                    if not ex.get("exercise_template_id"):
                        return "Cada exercício atualizado deve ter um `exercise_template_id`."
                    if not ex.get("sets"):
                        ex["sets"] = [{"type": "normal", "weight_kg": 0, "reps": 10}]
                    new_exercises.append(HevyRoutineExercise(**ex))
                current.exercises = new_exercises

            result = asyncio.run(hevy_service.update_routine(profile.hevy_api_key, routine_id, current))
            if result:
                return f"Rotina '{result.title}' atualizada com sucesso!"
            return "Falha ao atualizar rotina no Hevy. Verifique o ID e os dados."
        except Exception as e:
            logger.error(f"Error in update_hevy_routine: {e}")
            return f"Erro técnico na atualização: {str(e)}"

    return update_hevy_routine
