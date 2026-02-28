"""
Hevy integration tools for AI trainer.
"""
# pylint: disable=too-many-locals,broad-exception-caught,too-many-return-statements,too-many-branches,too-many-statements,line-too-long,missing-function-docstring
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
            response = await hevy_service.get_routines(
                profile.hevy_api_key, page, safe_page_size
            )

            if not response or not response.routines:
                logger.info("[list_hevy_routines] No routines found")
                return "Nenhuma rotina encontrada no Hevy."

            logger.info(
                "[list_hevy_routines] Found %d routines", len(response.routines)
            )
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
            logger.error("[list_hevy_routines] Error: %s", e)
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
        all_templates = await hevy_service.get_all_exercise_templates(
            profile.hevy_api_key
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
            "[create_hevy_routine] Called with: title='%s', exercises count=%d",
            title,
            len(exercises) if exercises else 0,
        )
        if exercises:
            for i, ex in enumerate(exercises[:3]):  # Log first 3
                logger.info("[create_hevy_routine] Exercise %d: %s", i, ex)

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

            result, error = await hevy_service.create_routine(
                profile.hevy_api_key, routine
            )

            if result:
                return f"✅ Rotina '{result.title}' criada com sucesso! ID: {result.id}"

            # Handle specific errors
            if error == "LIMIT_EXCEEDED":
                return "❌ Limite atingido: Sua conta gratuita do Hevy permite apenas 4 rotinas. Delete uma rotina existente ou faça upgrade para Hevy Pro."

            return f"❌ Falha ao criar rotina: {error}"
        except Exception as e:
            logger.error("Error in create_hevy_routine tool: %s", e, exc_info=True)
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
            exercises: Lista COMPLETA de exercícios (opcional). Use para mudar a estrutura, ordem, reps ou adicionar notas específicas de cada exercício.
            notes: Descrição GERAL da rotina (opcional). NÃO use para descrever exercícios individuais.

        IMPORTANTE:
        - Para mudar QUALQUER coisa nos exercícios (reps, ordem, incluir notas de execução), você DEVE enviar a lista `exercises` completa.
        - O campo `notes` aqui é apenas para a descrição que aparece no topo da rotina no Hevy.
        - `exercises` substitui toda a lista atual. Mantenha os exercícios existentes se quiser apenas adicionar um novo.
        """
        if not routine_title:
            return "Título da rotina é obrigatório para atualização."

        profile = database.get_user_profile(user_email)
        if not profile or not profile.hevy_enabled or not profile.hevy_api_key:
            return "Integração desativada."

        logger.info(
            "update_hevy_routine called by %s: "
            "routine_title='%s', new_title='%s', "
            "notes='%s', exercises_count=%s",
            user_email,
            routine_title,
            new_title,
            notes,
            len(exercises) if exercises else "None",
        )

        try:
            # Buscar rotinas paginadas (limite da API é 10 por página)
            # Vamos tentar encontrar nas primeiras 5 páginas (50 rotinas)
            all_routines = []
            for p in range(1, 6):
                logger.info("Fetching routines from Hevy (page=%d, page_size=10)", p)
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
                key_masked = (
                    f"{profile.hevy_api_key[:4]}..."
                    if profile.hevy_api_key
                    else "MISSING"
                )
                logger.warning(
                    "No routines returned for user %s (Key starts with: %s)",
                    user_email,
                    key_masked,
                )
                return "Nenhuma rotina encontrada na sua conta do Hevy. Certifique-se de que você criou rotinas no aplicativo Hevy antes de tentar atualizá-las."

            # Procurar rotina por título (case-insensitive match)
            target_routine = None
            routine_title_lower = routine_title.lower().strip()

            logger.info(
                "Searching for routine '%s' among %d routines",
                routine_title,
                len(all_routines),
            )

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
            logger.info(
                "Found routine '%s' with ID %s", target_routine.title, routine_id
            )

            # Fetch current to preserve fields not being updated
            current = await hevy_service.get_routine_by_id(
                profile.hevy_api_key, routine_id
            )
            if not current:
                return f"Detalhes da rotina '{routine_title}' não puderam ser recuperados do Hevy."

            if new_title:
                current.title = new_title
            if notes is not None:
                current.notes = notes
            if exercises:
                logger.info(
                    "Assigning %d new exercises to routine '%s'",
                    len(exercises),
                    target_routine.title,
                )
                new_exercises = []
                for ex in exercises:
                    if not ex.get("exercise_template_id"):
                        return "Cada exercício atualizado deve ter um `exercise_template_id`."
                    if not ex.get("sets"):
                        ex["sets"] = [{"type": "normal", "weight_kg": 0, "reps": 10}]

                    exercise_obj = HevyRoutineExercise(**ex)
                    logger.debug(
                        "Adding exercise: %s", exercise_obj.exercise_template_id
                    )
                    new_exercises.append(exercise_obj)
                current.exercises = new_exercises
            else:
                logger.info("No exercise updates provided in this tool call.")

            result = await hevy_service.update_routine(
                profile.hevy_api_key, routine_id, current
            )
            if result:
                msg = f"✅ Rotina '{result.title}' atualizada com sucesso!"
                if notes and not exercises:
                    msg += " (Nota: Apenas a descrição geral foi alterada. Se pretendia mudar a estrutura do treino, envie a lista de 'exercises')."
                return msg
            return "Falha ao enviar atualização para o Hevy. Verifique os dados dos exercícios."
        except Exception as e:
            logger.error("Error in update_hevy_routine: %s", e, exc_info=True)
            return f"Erro técnico na atualização: {str(e)}"

    return update_hevy_routine


def create_replace_hevy_exercise_tool(hevy_service, database, user_email: str):
    """
    Creates a tool to replace an exercise in a Hevy routine.
    """
    @tool
    async def replace_hevy_exercise(
        routine_title: str, old_exercise_name_or_id: str, new_exercise_id: str
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

        logger.info(
            "replace_hevy_exercise: %s | %s -> %s",
            routine_title,
            old_exercise_name_or_id,
            new_exercise_id,
        )

        try:
            # 1. Buscar a rotina
            target_routine = None
            # Tentar buscar nas primeiras páginas
            for p in range(1, 6):
                response = await hevy_service.get_routines(
                    profile.hevy_api_key, page=p, page_size=10
                )
                if not response or not response.routines:
                    break

                # Exact match first
                for r in response.routines:
                    if r.title.lower().strip() == routine_title.lower().strip():
                        target_routine = r
                        break
                if target_routine:
                    break

                # Fuzzy match second
                for r in response.routines:
                    if routine_title.lower() in r.title.lower():
                        target_routine = r
                        break
                if target_routine:
                    break

            if not target_routine:
                return f"Rotina '{routine_title}' não encontrada."

            # 2. Fetch full routine details
            current = await hevy_service.get_routine_by_id(
                profile.hevy_api_key, target_routine.id
            )
            if not current:
                return "Falha ao recuperar detalhes da rotina."

            # 3. Find and Swap Exercise
            found = False
            exercises_list = current.exercises

            target_old = old_exercise_name_or_id.lower().strip()

            for ex in exercises_list:
                # Check by ID
                if (
                    ex.exercise_template_id
                    and ex.exercise_template_id.lower() == target_old
                ):
                    ex.exercise_template_id = new_exercise_id
                    found = True
                    break

                # Check by Title (need to match title from GET response)
                if ex.title and (
                    target_old in ex.title.lower() or ex.title.lower() in target_old
                ):
                    ex.exercise_template_id = new_exercise_id
                    found = True
                    break

            if not found:
                current_names = [e.title for e in exercises_list if e.title]
                return f"Exercício '{old_exercise_name_or_id}' não encontrado na rotina '{current.title}'. Exercícios atuais: {', '.join(current_names)}"

            # 4. Clean Payload (Implicit via Pydantic + HevyService)
            # HevyRoutine Pydantic model ignores extras (index, etc)
            # HevyService.update_routine now strictly excludes forbidden fields.

            result = await hevy_service.update_routine(
                profile.hevy_api_key, target_routine.id, current
            )
            if result:
                return f"✅ Substituição realizada com sucesso! '{old_exercise_name_or_id}' -> Novo ID {new_exercise_id}."

            return "Erro ao atualizar no Hevy (API retornou falha na validação)."

        except Exception as e:
            logger.error("Error in replace_hevy_exercise: %s", e, exc_info=True)
            return f"Erro técnico: {str(e)}"

    return replace_hevy_exercise


def create_get_hevy_routine_detail_tool(hevy_service, database, user_email: str):
    @tool
    async def get_hevy_routine_detail(routine_title_or_id: str) -> str:
        """
        Obtém detalhes COMPLETOS de uma rotina do Hevy incluindo:
        - Nome, notas e ID da rotina
        - Lista completa de exercícios com IDs, nomes, rest_seconds, superset_id
        - Para cada exercício: lista de sets com tipo, peso, reps, rep_range, duração

        **IMPORTANTE**: Use SEMPRE esta ferramenta ANTES de tentar modificar uma rotina.
        Isso garante que você veja o estado atual e não perca dados.

        Args:
            routine_title_or_id: Título ou ID da rotina (ex: "Full Body A" ou "routine-123")

        Retorna: Descrição estruturada dos detalhes da rotina
        """
        profile = database.get_user_profile(user_email)
        if not profile or not profile.hevy_enabled or not profile.hevy_api_key:
            return "A integração com Hevy está desativada ou a chave API não está configurada."

        try:
            logger.debug(
                "[get_hevy_routine_detail] Request for routine: %s (user: %s)",
                routine_title_or_id,
                user_email,
            )

            # First, fetch all routines to find the matching one
            logger.debug("[get_hevy_routine_detail] Fetching all routines...")
            routines_resp = await hevy_service.get_routines(
                profile.hevy_api_key, page=1, page_size=50
            )

            if not routines_resp or not routines_resp.routines:
                logger.warning("[get_hevy_routine_detail] No routines found in Hevy")
                return "Nenhuma rotina encontrada no Hevy."

            logger.debug(
                "[get_hevy_routine_detail] Found %d routines",
                len(routines_resp.routines),
            )

            # Find routine by title or ID
            target_routine = None
            search_key = routine_title_or_id.lower()

            for r in routines_resp.routines:
                if r.id == routine_title_or_id or (
                    r.title and r.title.lower() == search_key
                ):
                    target_routine = r
                    logger.debug(
                        "[get_hevy_routine_detail] Found matching routine: %s (ID: %s)",
                        r.title,
                        r.id,
                    )
                    break

            if not target_routine:
                logger.warning(
                    "[get_hevy_routine_detail] Routine not found: %s",
                    routine_title_or_id,
                )
                return f"Rotina '{routine_title_or_id}' não encontrada."

            # Fetch full details of the routine
            logger.debug(
                "[get_hevy_routine_detail] Fetching full details for routine ID: %s",
                target_routine.id,
            )
            routine = await hevy_service.get_routine_by_id(
                profile.hevy_api_key, target_routine.id
            )

            if not routine:
                logger.error(
                    "[get_hevy_routine_detail] Failed to load routine details: %s",
                    target_routine.id,
                )
                return f"Não consegui carregar os detalhes da rotina '{target_routine.title}'."

            logger.info(
                "[get_hevy_routine_detail] Successfully loaded routine: %s with %d exercises",
                routine.title,
                len(routine.exercises) if routine.exercises else 0,
            )

            # Format detailed response
            result = f"📋 **{routine.title}** (ID: {routine.id})\n"
            if routine.notes:
                result += f"📝 Notas: {routine.notes}\n"
            result += "\n"

            if not routine.exercises:
                result += "Nenhum exercício nesta rotina.\n"
                return result

            result += f"🏋️ **Exercícios ({len(routine.exercises)})**:\n\n"

            for i, ex in enumerate(routine.exercises, 1):
                ex_name = ex.title if ex.title else f"(ID: {ex.exercise_template_id})"
                result += f"{i}. **{ex_name}**\n"
                result += f"   ID do Exercício: {ex.exercise_template_id}\n"

                if ex.rest_seconds is not None:
                    result += f"   Descanso: {ex.rest_seconds}s\n"
                if ex.superset_id is not None:
                    result += f"   Superset ID: {ex.superset_id}\n"
                if ex.notes:
                    result += f"   Notas: {ex.notes}\n"

                if ex.sets:
                    result += f"   Séries ({len(ex.sets)}):\n"
                    for j, s in enumerate(ex.sets, 1):
                        set_desc = f"      {j}. {s.type.upper()}"

                        if s.weight_kg is not None:
                            set_desc += f" - {s.weight_kg}kg"

                        if s.rep_range:
                            if s.rep_range.end is not None:
                                set_desc += f" x {s.rep_range.start}-{s.rep_range.end}"
                            else:
                                set_desc += f" x {s.rep_range.start}"
                        elif s.reps is not None:
                            set_desc += f" x {s.reps}"

                        if s.duration_seconds is not None:
                            set_desc += f" ({s.duration_seconds}s)"

                        result += set_desc + "\n"
                else:
                    result += "      Nenhuma série registrada.\n"

                result += "\n"

            return result

        except Exception as e:
            logger.error("Error in get_hevy_routine_detail: %s", e, exc_info=True)
            return f"Erro ao carregar detalhes da rotina: {str(e)}"

    return get_hevy_routine_detail


def create_set_routine_rest_and_ranges_tool(hevy_service, database, user_email: str):
    @tool
    async def set_routine_rest_and_ranges(
        routine_title_or_id: str,
        rest_seconds: int = 90,
        rep_range_start: int = 8,
        rep_range_end: int = 12,
    ) -> str:
        """
        Ferramenta especializada para atualizar rest_seconds e rep_range de uma rotina.

        Operação segura: busca a rotina atual, aplica as mudanças nos exercícios existentes,
        e envia o payload completo de volta ao Hevy (preservando todos os outros campos).

        **Uso recomendado**: Use quando quiser ajustar descansos ou ranges de uma rotina existente.

        Args:
            routine_title_or_id: Título ou ID da rotina (ex: "Full Body A")
            rest_seconds: Descanso padrão em segundos (default: 90s)
            rep_range_start: Início do range de reps (default: 8)
            rep_range_end: Fim do range de reps (default: 12)

        Retorna: Confirmação da atualização com resumo das mudanças
        """
        profile = database.get_user_profile(user_email)
        if not profile or not profile.hevy_enabled or not profile.hevy_api_key:
            return "A integração com Hevy está desativada ou a chave API não está configurada."

        try:
            logger.info(
                "[set_routine_rest_and_ranges] Starting: routine=%s, rest=%d, range=%d-%d",
                routine_title_or_id,
                rest_seconds,
                rep_range_start,
                rep_range_end,
            )

            # 1. Fetch current state
            logger.debug(
                "[set_routine_rest_and_ranges] Fetching all routines to find match..."
            )
            routines_resp = await hevy_service.get_routines(
                profile.hevy_api_key, page=1, page_size=50
            )

            if not routines_resp or not routines_resp.routines:
                logger.warning("[set_routine_rest_and_ranges] No routines found")
                return "Nenhuma rotina encontrada no Hevy."

            # Find routine
            target_routine = None
            search_key = routine_title_or_id.lower()

            for r in routines_resp.routines:
                if r.id == routine_title_or_id or (
                    r.title and r.title.lower() == search_key
                ):
                    target_routine = r
                    break

            if not target_routine:
                logger.warning(
                    "[set_routine_rest_and_ranges] Routine not found: %s",
                    routine_title_or_id,
                )
                return f"Rotina '{routine_title_or_id}' não encontrada."

            # 2. Fetch full details
            logger.debug(
                "[set_routine_rest_and_ranges] Fetching full routine details: %s",
                target_routine.id,
            )
            current = await hevy_service.get_routine_by_id(
                profile.hevy_api_key, target_routine.id
            )

            if not current:
                logger.error(
                    "[set_routine_rest_and_ranges] Failed to load routine: %s",
                    target_routine.id,
                )
                return f"Não consegui carregar a rotina '{target_routine.title}'."

            if not current.exercises:
                logger.warning(
                    "[set_routine_rest_and_ranges] Routine has no exercises: %s",
                    target_routine.id,
                )
                return f"A rotina '{current.title}' não tem exercícios para atualizar."

            # 3. Apply changes to all exercises
            logger.debug(
                "[set_routine_rest_and_ranges] Applying changes to %d exercises",
                len(current.exercises),
            )

            changes_summary = []
            updated_count = 0

            for ex in current.exercises:
                # Update rest_seconds
                old_rest = ex.rest_seconds
                ex.rest_seconds = rest_seconds
                if old_rest != rest_seconds:
                    changes_summary.append(
                        f"  - {ex.title or ex.exercise_template_id}: descanso {old_rest}s → {rest_seconds}s"
                    )
                    updated_count += 1

                # Update sets with new rep_range
                if ex.sets:
                    for s in ex.sets:
                        if s.type == "normal":  # Only update normal sets
                            old_range = (
                                f"{s.rep_range.start}-{s.rep_range.end}"
                                if s.rep_range
                                else "N/A"
                            )
                            s.rep_range = {
                                "start": rep_range_start,
                                "end": rep_range_end,
                            }
                            logger.debug(
                                "[set_routine_rest_and_ranges] Updated rep_range: %s → %d-%d",
                                old_range,
                                rep_range_start,
                                rep_range_end,
                            )

            # 4. Send updated routine back to Hevy
            logger.info(
                "[set_routine_rest_and_ranges] Sending updated routine to Hevy..."
            )
            result = await hevy_service.update_routine(
                profile.hevy_api_key, current.id, current
            )

            if result:
                logger.info(
                    "[set_routine_rest_and_ranges] Successfully updated routine: %s",
                    current.title,
                )
                summary = f"✅ Rotina '{current.title}' atualizada com sucesso!\n\n"
                summary += "📊 Mudanças aplicadas:\n"
                summary += f"  - Descanso: {rest_seconds}s em todos os exercícios\n"
                summary += f"  - Rep Range: {rep_range_start}-{rep_range_end} em séries normais\n"
                summary += f"  - Total de exercícios atualizados: {len(current.exercises)}\n"

                if changes_summary:
                    summary += "\nDetalhes:\n" + "\n".join(changes_summary[:10])
                    if len(changes_summary) > 10:
                        summary += f"\n  ... e mais {len(changes_summary) - 10}"

                return summary

            logger.error(
                "[set_routine_rest_and_ranges] Failed to update routine in Hevy"
            )
            return "Erro ao atualizar a rotina no Hevy (validação da API)."

        except Exception as e:
            logger.error(
                "[set_routine_rest_and_ranges] Exception: %s", e, exc_info=True
            )
            return f"Erro técnico ao atualizar rotina: {str(e)}"

    return set_routine_rest_and_ranges


def create_trigger_hevy_import_tool(hevy_service, database, user_email: str):
    @tool
    async def trigger_hevy_import(
        days_back: int = 7
    ) -> str:
        """
        Dispara a importação de treinos do Hevy para o sistema.
        Use esta ferramenta APENAS se a integração com o Hevy estiver ATIVA e o aluno pedir para sincronizar ou importar os treinos.
        
        Args:
            days_back: Quantidade de dias para trás que os treinos devem ser buscados (padrão é 7).
        """
        profile = database.get_user_profile(user_email)
        if not profile or not profile.hevy_enabled or not profile.hevy_api_key:
            return "A integração com Hevy está desativada ou a chave API não está configurada. Por favor, ative-a nas configurações."
            
        try:
            from datetime import datetime, timezone, timedelta
            from_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            
            logger.info("[trigger_hevy_import] Starting import for user %s, %d days back", user_email, days_back)
            
            result = await hevy_service.import_workouts(
                user_email=user_email,
                api_key=profile.hevy_api_key,
                from_date=from_date
            )
            
            imported = result.get("imported", 0)
            skipped = result.get("skipped", 0)
            failed = result.get("failed", 0)
            
            return f"A importação do Hevy foi concluída com sucesso! Detalhes:\n- {imported} novos treinos importados\n- {skipped} treinos ignorados (já existiam)\n- {failed} importações falharam."
            
        except Exception as e:
            logger.error("[trigger_hevy_import] Error: %s", e, exc_info=True)
            return f"Erro ao disparar a importação do Hevy: {str(e)}"
            
    return trigger_hevy_import
