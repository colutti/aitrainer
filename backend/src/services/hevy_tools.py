from langchain_core.tools import tool
from src.core.logs import logger
from src.api.models.routine import HevyRoutine, HevyRoutineExercise


def create_list_hevy_routines_tool(hevy_service, database, user_email: str):
    @tool
    async def list_hevy_routines(page: int = 1, page_size: int = 10) -> str:
        """
        Lista as rotinas de treino do aluno no Hevy.
        Use quando o aluno perguntar "quais são minhas rotinas" ou "mostre meus treinos salvos".
        """
        profile = database.get_user_profile(user_email)
        if not profile or not profile.hevy_enabled or not profile.hevy_api_key:
            return "A integração com Hevy está desativada ou a chave API não está configurada. Por favor, ative-a nas configurações."

        try:
            # Hevy API limits pageSize to 10
            safe_page_size = min(page_size, 10)
            response = await hevy_service.get_routines(profile.hevy_api_key, page, safe_page_size)

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
    async def search_hevy_exercises(query: str) -> str:
        """
        Pesquisa o catálogo de exercícios do Hevy para encontrar o `exercise_template_id` correto.
        VOCÊ DEVE USAR ESTA FERRAMENTA ANTES DE CRIAR OU EDITAR UMA ROTINA para garantir que os IDs estão corretos.
        Exemplo de query: "supino", "agachamento", "leg press".
        """
        profile = database.get_user_profile(user_email)
        if not profile or not profile.hevy_enabled or not profile.hevy_api_key:
            return "Integração desativada."

        # Fetch ALL exercise templates to avoid missing data from first page only
        all_templates = await hevy_service.get_all_exercise_templates(profile.hevy_api_key)

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
    async def create_hevy_routine(
        title: str,
        exercises: list[dict],
        notes: str | None = None,
    ) -> str:
        """
        Cria uma nova rotina no Hevy.

        Args:
            title: Título da rotina (obrigatório)
            exercises: Lista de exercícios (obrigatório, mínimo 1)
            notes: Notas da rotina (opcional)

        Estrutura de exercises:
        [
          {
            "exercise_template_id": "ABC123",  # Obrigatório - use search_hevy_exercises
            "notes": "💪 Foco em forma, controle na descida",  # Opcional - instruções específicas
            "rest_seconds": 90,  # Opcional - tempo de descanso (60, 90, 120, 180 comum)
            "superset_id": 1,  # Opcional - mesmo ID = superset
            "sets": [
              {"type": "warmup", "weight_kg": 40, "reps": 12},
              {"type": "normal", "weight_kg": 80, "rep_range": {"start": 8, "end": 12}},
              {"type": "dropset", "weight_kg": 60, "reps": 15},
              {"type": "failure", "weight_kg": 70, "reps": 10}
            ]
          }
        ]

        Campos suportados em sets:
        - type: "normal" | "warmup" | "dropset" | "failure"
        - weight_kg: float (peso em kg)
        - reps: int (reps fixas) OU rep_range: {"start": int, "end": int}
        - duration_seconds: int (para exercícios cronometrados)
        - distance_meters: float (para cardio)

        Dicas:
        - Use emojis nas notas para melhor UX (💪, 🔥, 🔗)
        - Use rep_range para flexibilidade (ex: 8-12 reps)
        - Use superset_id para ligar exercícios (mesmo ID = superset)
        - Use rest_seconds para tempos de descanso específicos

        IMPORTANTE:
        1. Use `search_hevy_exercises` primeiro para obter IDs válidos
        2. exercises NÃO PODE estar vazio
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
            # Always use default folder (folder_id = None)
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

            result, error = await hevy_service.create_routine(profile.hevy_api_key, routine)

            if result:
                return f"✅ Rotina '{result.title}' criada com sucesso! ID: {result.id}"

            # Handle specific errors
            if error == "LIMIT_EXCEEDED":
                return "❌ Limite atingido: Sua conta gratuita do Hevy permite apenas 4 rotinas. Delete uma rotina existente ou faça upgrade para Hevy Pro."

            return f"❌ Falha ao criar rotina: {error}"
        except Exception as e:
            logger.error(f"Error in create_hevy_routine tool: {e}", exc_info=True)
            return f"Erro ao criar rotina: {str(e)}"

    return create_hevy_routine


def create_update_hevy_routine_tool(hevy_service, database, user_email: str):
    @tool
    async def update_hevy_routine(
        routine_title: str,
        new_title: str | None = None,
        exercises: list[dict] | None = None,
        notes: str | None = None,
    ) -> str:
        """
        Atualiza uma rotina existente no Hevy.

        Args:
            routine_title: Título da rotina a atualizar (use list_hevy_routines)
            new_title: Novo título (opcional)
            exercises: Lista COMPLETA de exercícios (opcional - substitui tudo)
            notes: Notas atualizadas (opcional)

        IMPORTANTE:
        1. Use o título exato de list_hevy_routines
        2. exercises substitui TODA a lista - inclua exercícios existentes se quiser mantê-los
        3. Suporta os mesmos campos de create_hevy_routine:
           - exercise.notes, rest_seconds, superset_id
           - set.type (warmup/normal/dropset/failure)
           - rep_range para flexibilidade
        4. Use search_hevy_exercises para validar IDs de novos exercícios

        Exemplos de uso:
        - Adicionar exercício: inclua todos os antigos + o novo
        - Remover exercício: inclua só os que quer manter
        - Mudar ordem: reordene a lista
        - Adicionar superset: adicione superset_id aos exercícios
        - Mudar reps fixas para range: use rep_range ao invés de reps
        - Atualizar notas: passe notes com novo texto
        """
        if not routine_title:
            return "Título da rotina é obrigatório para atualização."

        profile = database.get_user_profile(user_email)
        if not profile or not profile.hevy_enabled or not profile.hevy_api_key:
            return "Integração desativada."

        logger.info(
            f"update_hevy_routine called by {user_email}: "
            f"routine_title='{routine_title}', new_title='{new_title}', "
            f"notes='{notes}', exercises_count={len(exercises) if exercises else 'None'}"
        )

        try:
            # Buscar rotinas paginadas (limite da API é 10 por página)
            # Vamos tentar encontrar nas primeiras 5 páginas (50 rotinas)
            all_routines = []
            for p in range(1, 6):
                logger.info(f"Fetching routines from Hevy (page={p}, page_size=10)")
                response = await hevy_service.get_routines(
                    profile.hevy_api_key, page=p, page_size=10
                )
                if response and response.routines:
                    all_routines.extend(response.routines)
                    if p >= response.page_count:
                        break
                else:
                    break

            if not all_routines:
                key_masked = f"{profile.hevy_api_key[:4]}..." if profile.hevy_api_key else "MISSING"
                logger.warning(f"No routines returned for user {user_email} (Key starts with: {key_masked})")
                return "Nenhuma rotina encontrada na sua conta do Hevy. Certifique-se de que você criou rotinas no aplicativo Hevy antes de tentar atualizá-las."

            # Procurar rotina por título (case-insensitive match)
            target_routine = None
            routine_title_lower = routine_title.lower().strip()
            
            logger.info(f"Searching for routine '{routine_title}' among {len(all_routines)} routines")

            for r in all_routines:
                if r.title.lower().strip() == routine_title_lower:
                    target_routine = r
                    break

            if not target_routine:
                # Tentar match parcial fuzzy
                for r in all_routines:
                    if routine_title_lower in r.title.lower():
                        target_routine = r
                        break

            if not target_routine:
                available_titles = [r.title for r in all_routines[:5]]
                return f"Rotina '{routine_title}' não encontrada. Rotinas disponíveis: {', '.join(available_titles)}. Use o nome exato que aparece no Hevy."

            routine_id = target_routine.id
            logger.info(f"Found routine '{target_routine.title}' with ID {routine_id}")

            # Fetch current to preserve fields not being updated
            current = await hevy_service.get_routine_by_id(profile.hevy_api_key, routine_id)
            if not current:
                return f"Detalhes da rotina '{routine_title}' não puderam ser recuperados do Hevy."

            if new_title:
                current.title = new_title
            if notes is not None:
                current.notes = notes
            if exercises:
                logger.info(f"Assigning {len(exercises)} new exercises to routine '{target_routine.title}'")
                new_exercises = []
                for ex in exercises:
                    if not ex.get("exercise_template_id"):
                        return "Cada exercício atualizado deve ter um `exercise_template_id`."
                    if not ex.get("sets"):
                        ex["sets"] = [{"type": "normal", "weight_kg": 0, "reps": 10}]
                    
                    exercise_obj = HevyRoutineExercise(**ex)
                    logger.debug(f"Adding exercise: {exercise_obj.exercise_template_id}")
                    new_exercises.append(exercise_obj)
                current.exercises = new_exercises
            else:
                logger.info("No exercise updates provided in this tool call.")

            result = await hevy_service.update_routine(profile.hevy_api_key, routine_id, current)
            if result:
                return f"✅ Rotina '{result.title}' atualizada com sucesso!"
            return "Falha ao enviar atualização para o Hevy. Verifique os dados dos exercícios."
        except Exception as e:
            logger.error(f"Error in update_hevy_routine: {e}", exc_info=True)
            return f"Erro técnico na atualização: {str(e)}"

    return update_hevy_routine


def create_replace_hevy_exercise_tool(hevy_service, database, user_email: str):
    @tool
    async def replace_hevy_exercise(
        routine_title: str,
        old_exercise_name_or_id: str,
        new_exercise_id: str
    ) -> str:
        """
        Substitui um exercício por outro em uma rotina do Hevy, mantendo as séries e cargas existentes.
        
        Args:
            routine_title: Título da rotina (ex: "Pull", "Legs").
            old_exercise_name_or_id: Nome (fuzzy match) ou ID do exercício antigo a ser removido.
            new_exercise_id: ID do novo exercício (template ID) que entrará no lugar.
        """
        profile = database.get_user_profile(user_email)
        if not profile or not profile.hevy_enabled or not profile.hevy_api_key:
            return "Integração desativada."

        logger.info(f"replace_hevy_exercise: {routine_title} | {old_exercise_name_or_id} -> {new_exercise_id}")

        try:
            # 1. Buscar a rotina
            target_routine = None
            # Tentar buscar nas primeiras páginas
            for p in range(1, 6):
                response = await hevy_service.get_routines(profile.hevy_api_key, page=p, page_size=10)
                if not response or not response.routines:
                    break
                
                # Exact match first
                for r in response.routines:
                    if r.title.lower().strip() == routine_title.lower().strip():
                        target_routine = r
                        break
                if target_routine: break
                
                # Fuzzy match second
                for r in response.routines:
                    if routine_title.lower() in r.title.lower():
                        target_routine = r
                        break
                if target_routine: break
            
            if not target_routine:
                return f"Rotina '{routine_title}' não encontrada."

            # 2. Fetch full routine details
            current = await hevy_service.get_routine_by_id(profile.hevy_api_key, target_routine.id)
            if not current:
                return "Falha ao recuperar detalhes da rotina."

            # 3. Find and Swap Exercise
            found = False
            exercises_list = current.exercises
            
            target_old = old_exercise_name_or_id.lower().strip()
            
            for ex in exercises_list:
                # Check by ID
                if ex.exercise_template_id and ex.exercise_template_id.lower() == target_old:
                    ex.exercise_template_id = new_exercise_id
                    found = True
                    break
                
                # Check by Title (need to match title from GET response)
                if ex.title and (target_old in ex.title.lower() or ex.title.lower() in target_old):
                   ex.exercise_template_id = new_exercise_id
                   found = True
                   break

            if not found:
                current_names = [e.title for e in exercises_list if e.title]
                return f"Exercício '{old_exercise_name_or_id}' não encontrado na rotina '{current.title}'. Exercícios atuais: {', '.join(current_names)}"

            # 4. Clean Payload (Implicit via Pydantic + HevyService)
            # HevyRoutine Pydantic model ignores extras (index, etc)
            # HevyService.update_routine now strictly excludes forbidden fields.
            
            result = await hevy_service.update_routine(profile.hevy_api_key, target_routine.id, current)
            if result:
                 return f"✅ Substituição realizada com sucesso! '{old_exercise_name_or_id}' -> Novo ID {new_exercise_id}."
            
            return "Erro ao atualizar no Hevy (API retornou falha na validação)."

        except Exception as e:
            logger.error(f"Error in replace_hevy_exercise: {e}", exc_info=True)
            return f"Erro técnico: {str(e)}"

    return replace_hevy_exercise

