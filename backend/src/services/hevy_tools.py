from langchain_core.tools import tool
from src.core.logs import logger
from src.api.models.routine import HevyRoutine, HevyRoutineExercise


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

        try:
            response = asyncio.run(
                hevy_service.get_routines(profile.hevy_api_key, page, page_size)
            )

            if not response or not response.routines:
                logger.info("[list_hevy_routines] No routines found")
                return "Nenhuma rotina encontrada no Hevy."

            logger.info(f"[list_hevy_routines] Found {len(response.routines)} routines")
            result = f"Encontrei {len(response.routines)} rotinas (Página {response.page}/{response.page_count}):\n\n"
            for i, r in enumerate(response.routines, 1):
                result += f"{i}. **{r.title}**\n"
                if r.notes:
                    result += f"   Notas: {r.notes}\n"
                # Show exercise titles if available, otherwise IDs
                exercise_names = []
                for ex in r.exercises:
                    if ex.title:
                        exercise_names.append(ex.title)
                    else:
                        exercise_names.append(f"ID:{ex.exercise_template_id}")
                result += f"   Exercícios: {', '.join(exercise_names[:5])}"
                if len(exercise_names) > 5:
                    result += f"... (+{len(exercise_names) - 5} mais)"
                result += "\n\n"

            return result
        except Exception as e:
            logger.error(f"[list_hevy_routines] Error: {e}")
            return f"Erro ao buscar rotinas: {str(e)}"

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
        all_templates = asyncio.run(
            hevy_service.get_all_exercise_templates(profile.hevy_api_key)
        )

        if not all_templates:
            return "Nenhum exercício encontrado no catálogo do Hevy."

        # logic: exact match first, then all words match
        query = query.lower().replace("-", " ")  # Basic normalization
        parts = query.split()

        exact_matches = [
            ex for ex in all_templates if query == ex.title.lower().replace("-", " ")
        ]
        all_words_matches = [
            ex
            for ex in all_templates
            if all(p in ex.title.lower().replace("-", " ") for p in parts)
        ]

        # Merge and remove duplicates (preserving order)
        matches = exact_matches + [
            m for m in all_words_matches if m not in exact_matches
        ]

        if not matches:
            # Last resort: partial muscle match
            matches = [
                ex
                for ex in all_templates
                if query in (ex.primary_muscle_group or "").lower()
            ]

        if not matches:
            return f"Nenhum exercício encontrado para '{query}'. Tente usar o nome em inglês ou termos parciais (Ex: 'Leg Press' em vez de 'Prensa')."

        # Limit to top 5 most relevant
        top_matches = matches[:5]
        result = f"Encontrei {len(matches)} exercício(s) para '{query}':\n\n"
        for ex in top_matches:
            result += f"• {ex.title} → ID: `{ex.id}`\n"

        if len(matches) > 5:
            result += (
                f"\n... e mais {len(matches) - 5} opções. Refine a busca se necessário."
            )

        return result

    return search_hevy_exercises


def create_create_hevy_routine_tool(hevy_service, database, user_email: str):
    @tool
    def create_hevy_routine(
        title: str,
        exercises: list[dict],
        notes: str | None = None,
        folder_id: int | None = None,
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
        # Debug logging
        logger.info(
            f"[create_hevy_routine] Called with: title='{title}', exercises count={len(exercises) if exercises else 0}"
        )
        if exercises:
            for i, ex in enumerate(exercises[:3]):  # Log first 3
                logger.info(f"[create_hevy_routine] Exercise {i}: {ex}")

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
                    return "Exercício inválido: faltando `exercise_template_id`. Use `search_hevy_exercises`."

                # Default empty sets if missing
                if not ex.get("sets"):
                    ex["sets"] = [{"type": "normal", "weight_kg": 0, "reps": 10}]

                routine_exercises.append(HevyRoutineExercise(**ex))

            routine = HevyRoutine(
                title=title,
                notes=notes,
                folder_id=clean_folder_id,
                exercises=routine_exercises,
            )

            import asyncio

            result, error = asyncio.run(
                hevy_service.create_routine(profile.hevy_api_key, routine)
            )

            if result:
                return f"✅ Rotina '{result.title}' criada com sucesso! ID: {result.id}"

            # Handle specific errors
            if error == "LIMIT_EXCEEDED":
                return "❌ Limite atingido: Sua conta gratuita do Hevy permite apenas 4 rotinas. Delete uma rotina existente ou faça upgrade para Hevy Pro."

            return f"❌ Falha ao criar rotina: {error}"
        except Exception as e:
            logger.error(f"Error in create_hevy_routine tool: {e}")
            return f"Erro ao criar rotina: {str(e)}"

    return create_hevy_routine


def create_update_hevy_routine_tool(hevy_service, database, user_email: str):
    @tool
    def update_hevy_routine(
        routine_title: str,
        new_title: str | None = None,
        exercises: list[dict] | None = None,
        notes: str | None = None,
    ) -> str:
        """
        Atualiza uma rotina existente no Hevy.

        Args:
            routine_title: Título da rotina a ser atualizada (ex: "Pull Workout", "Treino A")
            new_title: Novo título para a rotina (opcional, se quiser renomear)
            exercises: Lista de exercícios atualizada (opcional)
            notes: Notas atualizadas (opcional)

        IMPORTANTE:
        1. Use o título que aparece em `list_hevy_routines`.
        2. Se alterar exercícios, use `search_hevy_exercises` para validar os IDs.
        """
        if not routine_title:
            return "Título da rotina é obrigatório para atualização."

        profile = database.get_user_profile(user_email)
        if not profile or not profile.hevy_enabled or not profile.hevy_api_key:
            return "Integração desativada."

        import asyncio

        try:
            # Buscar todas rotinas para encontrar a correta por título
            all_routines_response = asyncio.run(
                hevy_service.get_routines(profile.hevy_api_key, page=1, page_size=100)
            )

            if not all_routines_response or not all_routines_response.routines:
                return "Nenhuma rotina encontrada no Hevy. Crie uma rotina primeiro."

            # Procurar rotina por título (case-insensitive match)
            target_routine = None
            routine_title_lower = routine_title.lower().strip()

            for r in all_routines_response.routines:
                if r.title.lower().strip() == routine_title_lower:
                    target_routine = r
                    break

            if not target_routine:
                # Tentar match parcial fuzzy
                for r in all_routines_response.routines:
                    if routine_title_lower in r.title.lower():
                        target_routine = r
                        break

            if not target_routine:
                available_titles = [r.title for r in all_routines_response.routines[:5]]
                return f"Rotina '{routine_title}' não encontrada. Rotinas disponíveis: {', '.join(available_titles)}"

            routine_id = target_routine.id

            # Fetch current to preserve fields not being updated
            current = asyncio.run(
                hevy_service.get_routine_by_id(profile.hevy_api_key, routine_id)
            )
            if not current:
                return f"Detalhes da rotina '{routine_title}' não encontrados no Hevy."

            if new_title:
                current.title = new_title
            if notes:
                current.notes = notes
            if exercises:
                new_exercises = []
                for ex in exercises:
                    if not ex.get("exercise_template_id"):
                        return "Cada exercício atualizado deve ter um `exercise_template_id`."
                    if not ex.get("sets"):
                        ex["sets"] = [{"type": "normal", "weight_kg": 0, "reps": 10}]
                    new_exercises.append(HevyRoutineExercise(**ex))
                current.exercises = new_exercises

            result = asyncio.run(
                hevy_service.update_routine(profile.hevy_api_key, routine_id, current)
            )
            if result:
                return f"✅ Rotina '{result.title}' atualizada com sucesso!"
            return "Falha ao atualizar rotina no Hevy. Verifique os dados."
        except Exception as e:
            logger.error(f"Error in update_hevy_routine: {e}")
            return f"Erro técnico na atualização: {str(e)}"

    return update_hevy_routine
