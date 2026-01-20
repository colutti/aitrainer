"""
This module contains the AI trainer brain, which is responsible for interacting with the LLM.
"""

from datetime import datetime
from fastapi import BackgroundTasks
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from mem0 import Memory

from src.core.config import settings
from src.services.database import MongoDatabase
from src.services.llm_client import LLMClient
from src.services.workout_tools import create_save_workout_tool, create_get_workouts_tool
from src.services.nutrition_tools import create_save_nutrition_tool, create_get_nutrition_tool
from src.services.composition_tools import create_save_composition_tool, create_get_composition_tool
from src.core.logs import logger
from src.api.models.chat_history import ChatHistory
from src.api.models.user_profile import UserProfile
from src.api.models.sender import Sender
from src.api.models.trainer_profile import TrainerProfile


def _add_to_mem0_background(memory: Memory, user_email: str, user_input: str, response_text: str):
    """
    Background task function to add conversation to Mem0 (long-term memory).
    This runs asynchronously to avoid blocking the response stream.
    
    Args:
        memory (Memory): The Mem0 Memory client instance.
        user_email (str): The user's email.
        user_input (str): The user's input message.
        response_text (str): The AI's response message.
    """
    try:
        # Format as conversation messages so Mem0 extracts facts cleaner
        messages = [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": response_text},
        ]
        memory.add(messages, user_id=user_email)
        logger.info("Successfully added conversation turn to Mem0 for user: %s", user_email)
    except Exception as e:
        # Log error but don't crash - Mem0 storage is not critical for user experience
        logger.error("Failed to add memory to Mem0 for user %s: %s", user_email, e)


class AITrainerBrain:
    """
    Service class responsible for orchestrating AI trainer interactions.
    Uses LLMClient for LLM operations (abstracted from specific providers).
    """

    def _format_date(self, date_str: str) -> str:
        """Helper to format date strings."""
        if not date_str: return "Data desc."
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%d/%m")
        except (ValueError, AttributeError):
            return "Data desc."

    def __init__(
        self, database: MongoDatabase, llm_client: LLMClient, memory: Memory
    ):
        self._database: MongoDatabase = database
        self._llm_client: LLMClient = llm_client
        self._memory: Memory = memory

    def _get_prompt_template(self, input_data: dict, is_telegram: bool = False) -> ChatPromptTemplate:
        """Constructs and returns the chat prompt template."""
        logger.debug("Constructing chat prompt template (is_telegram=%s).", is_telegram)
        
        system_content = settings.PROMPT_TEMPLATE
        if is_telegram:
            system_content += (
                "\n\n--- \n"
                "⚠️ **FORMATO TELEGRAM (MOBILE)**: "
                "O usuário está enviando mensagens via Telegram. Responda de forma direta e concisa. "
                "Use Markdown simples (negrito e itálico). Evite tabelas muito largas ou blocos de código extensos que não cabem na tela do celular."
            )

        prompt_template = ChatPromptTemplate.from_messages(
            [("system", system_content), ("human", "{user_message}")]
        )
        rendered_prompt = prompt_template.format(**input_data)
        
        # --- PROMPT INSPECTOR (DEBUG) ---
        # Checks if Critical Section is present and populated
        critical_check = "✅ Presente" if "## 🚨 Fatos Críticos" in rendered_prompt else "❌ Ausente"
        logger.debug("🛡️ PROMPT ANATOMY CHECK: Critical Section: %s | Total Chars: %d", critical_check, len(rendered_prompt))
        # -------------------------------
        
        # Flatten prompt for single-line logging
        single_line_prompt = rendered_prompt.replace("\n", "\\n")
        logger.debug("📤 PROMPT ENVIADO AO LLM: %s", single_line_prompt)
        return prompt_template

    # _extract_conversation_text removed (obsolete)

    def get_chat_history(self, session_id: str) -> list[ChatHistory]:
        """
        Retrieves the chat history for a given session ID.

        Args:
            session_id (str): The session ID.

        Returns:
            list[ChatHistory]: A list of chat messages.
        """
        logger.debug("Attempting to retrieve chat history for session: %s", session_id)
        return self._database.get_chat_history(session_id)
    
    def _normalize_mem0_results(self, results, source: str) -> list[dict]:
        """Helper to normalize Mem0 results."""
        normalized = []
        data = results.get("results", []) if isinstance(results, dict) else results
        for mem in data:
            if text := mem.get("memory", ""):
                normalized.append({
                    "text": text,
                    "created_at": mem.get("created_at", ""),
                    "source": source
                })
        return normalized

    def _retrieve_critical_facts(self, user_id: str) -> list[dict]:
        """
        Busca explícita por fatos críticos (saúde, lesões, objetivos) que devem ter precedência.
        Garante que 'alergia', 'lesão', etc. sejam recuperados mesmo se semântica falhar.
        """
        critical_keywords = "alergia lesão dor objetivo meta restrição médico cirurgia"
        results = self._memory.search(user_id=user_id, query=critical_keywords, limit=5)
        return self._normalize_mem0_results(results, source="critical")

    def _retrieve_semantic_memories(self, user_id: str, query: str, limit: int = 5) -> list[dict]:
        """Busca contexto semântico baseado no input atual."""
        results = self._memory.search(user_id=user_id, query=query, limit=limit)
        return self._normalize_mem0_results(results, source="semantic")

    def _retrieve_recent_memories(self, user_id: str, limit: int = 5) -> list[dict]:
        """Busca memórias recém-adicionadas (contexto temporal de curto prazo expandido)."""
        try:
            # get_all returns newest first usually
            results = self._memory.get_all(user_id=user_id, limit=limit)
            return self._normalize_mem0_results(results, source="recent")
        except Exception:
            return []

    def _retrieve_hybrid_memories(self, user_input: str, user_id: str) -> dict:
        """
        Retrieves memories using Hybrid Search (Critical + Semantic + Recent).
        Returns a structured dictionary to allow explicit prompt placement.
        """
        logger.debug("Retrieving HYBRID memories for user: %s", user_id)
        
        # 1. Critical Facts (Always fetch)
        critical = self._retrieve_critical_facts(user_id)
        
        # 2. Semantic Context (Based on input)
        semantic = self._retrieve_semantic_memories(user_id, user_input)
        
        # 3. Recent (Temporal context)
        recent = self._retrieve_recent_memories(user_id)
        
        # Deduplicate (prefer Critical > Semantic > Recent)
        seen_texts = set()
        unique_critical = []
        for m in critical:
            if m["text"] not in seen_texts:
                unique_critical.append(m)
                seen_texts.add(m["text"])
                
        unique_semantic = []
        for m in semantic:
            if m["text"] not in seen_texts:
                unique_semantic.append(m)
                seen_texts.add(m["text"])
                
        unique_recent = []
        for m in recent:
            if m["text"] not in seen_texts:
                unique_recent.append(m)
                seen_texts.add(m["text"])

        return {
            "critical": unique_critical,
            "semantic": unique_semantic,
            "recent": unique_recent
        }

    def get_user_profile(self, email: str) -> UserProfile | None:
        """
        Retrieves a user profile from the database.
        """
        return self._database.get_user_profile(email)

    def get_trainer_profile(self, email: str) -> TrainerProfile | None:
        """
        Retrieves a trainer profile from the database.
        """
        return self._database.get_trainer_profile(email)

    def save_user_profile(self, profile: UserProfile):
        """
        Saves a user profile to the database.
        """
        self._database.save_user_profile(profile)

    def save_trainer_profile(self, profile: TrainerProfile):
        """
        Saves a trainer profile to the database.
        """
        self._database.save_trainer_profile(profile)

    def _get_or_create_user_profile(self, user_email: str) -> UserProfile:
        """Retrieves user profile or creates a default one if not found."""
        profile = self.get_user_profile(user_email)
        if not profile:
            logger.info("User profile not found, creating default for user: %s", user_email)
            profile = UserProfile(
                email=user_email,
                gender="Masculino",
                age=30,
                weight=70.0,
                height=175,
                goal="Melhorar condicionamento",
                goal_type="maintain"
            )
            self.save_user_profile(profile)
        return profile

    def _get_or_create_trainer_profile(self, user_email: str) -> TrainerProfile:
        """Retrieves trainer profile or creates a default one if not found."""
        trainer_profile_obj = self._database.get_trainer_profile(user_email)
        if not trainer_profile_obj:
            logger.info("Trainer profile not found, creating default for user: %s", user_email)
            trainer_profile_obj = TrainerProfile(
                user_email=user_email,
                trainer_type="atlas"
            )
            self.save_trainer_profile(trainer_profile_obj)
        return trainer_profile_obj

    def _add_to_mongo_history(self, user_email: str, user_input: str, response_text: str, trainer_type: str):
        """
        Adds the user input and AI response to MongoDB chat history (synchronous).
        
        Args:
            user_email (str): The user's email.
            user_input (str): The user's input message.
            response_text (str): The AI's response message.
            trainer_type (str): The active trainer profile type.
        """
        now = datetime.now().isoformat()
        user_message = ChatHistory(
            sender=Sender.STUDENT, text=user_input, timestamp=now, trainer_type=trainer_type
        )
        ai_message = ChatHistory(
            sender=Sender.TRAINER, text=response_text, timestamp=now, trainer_type=trainer_type
        )

        # Save to MongoDB (Session History) - synchronous
        self._database.add_to_history(user_message, user_email, trainer_type)
        self._database.add_to_history(ai_message, user_email, trainer_type)
        logger.info("Successfully saved conversation to MongoDB for user: %s (trainer: %s)", user_email, trainer_type)

    def _format_memory_messages(
        self,
        messages: list,
        current_trainer_type: str,
    ) -> str:
        """
        Formats LangChain messages with trainer context for the prompt.
        Uses compact single-line format:
        [DD/MM HH:MM] 🧑 Aluno: msg
        [DD/MM HH:MM] 🏋️ VOCÊ (Treinador): msg
        [DD/MM HH:MM] 🏋️ EX-TREINADOR [Type]: msg
        """
        if not messages:
            return "Nenhuma mensagem anterior."
        
        formatted = []
        for msg in messages:
            # Extract timestamp if available
            timestamp_str = ""
            if hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                ts = msg.additional_kwargs.get("timestamp", "")
                if ts:
                    try:
                        dt = datetime.fromisoformat(ts)
                        timestamp_str = f"[{dt.strftime('%d/%m %H:%M')}] "
                    except (ValueError, TypeError):
                        pass
            
            # Clean message content - single line
            content = " ".join(msg.content.split())
            
            # Check if it's a summary (SystemMessage with moving_summary_buffer content)
            if hasattr(msg, 'type') and msg.type == "system":
                formatted.append(f"📜 [RESUMO]: {content}")
            elif isinstance(msg, HumanMessage):
                formatted.append(f"{timestamp_str}🧑 Aluno: {content}")
            elif isinstance(msg, AIMessage):
                trainer_type = msg.additional_kwargs.get("trainer_type", current_trainer_type)
                if trainer_type == current_trainer_type:
                    formatted.append(f"{timestamp_str}🏋️ VOCÊ (Treinador): {content}")
                else:
                    formatted.append(
                        f"{timestamp_str}🏋️ EX-TREINADOR [{trainer_type}]: {content}"
                    )
            else:
                # Fallback for unknown message types
                formatted.append(f"{timestamp_str}> {content}")
        
        return "\n".join(formatted)

    def send_message_ai(
        self, user_email: str, user_input: str, background_tasks: BackgroundTasks = None, is_telegram: bool = False
    ):
        """
        Generates LLM response, summarizing history if needed.
        This function assumes one chat session per user (user_email is used as session_id).

        If the conversation history exceeds 20 messages, it will:
        1. Separate old messages (first 10) from recent messages (remaining)
        2. Summarize old messages and merge with existing summary
        3. Prune the chat history, keeping only recent messages
        4. Update the conversation summary in the database

        Args:
            user_email (str): The user's email, also used as session ID.
            user_input (str): The user's input message.

        Yields:
            str: Individual chunks of the AI trainer's response.
        """
        logger.info("Generating workout stream for user: %s", user_email)

        profile = self._get_or_create_user_profile(user_email)
        trainer_profile_obj = self._get_or_create_trainer_profile(user_email)

        # Retrieve Hybrid Memories
        hybrid_memories = self._retrieve_hybrid_memories(user_input, user_email)
        
        # Format memories into sections for the prompt
        # TODO: Move this formatting logic to Prompt Template in Phase 2
        memory_sections = []
        
        if hybrid_memories["critical"]:
            sec = ["## 🚨 Fatos Críticos (ATENÇÃO MÁXIMA):"]
            for mem in hybrid_memories["critical"]:
                dt = self._format_date(mem.get("created_at"))
                sec.append(f"- ⚠️ ({dt}) {mem['text']}")
            memory_sections.append("\n".join(sec))
            
        if hybrid_memories["semantic"]:
            sec = ["## 🧠 Contexto Relacionado:"]
            for mem in hybrid_memories["semantic"]:
                dt = self._format_date(mem.get("created_at"))
                sec.append(f"- ({dt}) {mem['text']}")
            memory_sections.append("\n".join(sec))
            
        if hybrid_memories["recent"]:
            sec = ["## 📅 Fatos Recentes:"]
            for mem in hybrid_memories["recent"]:
                dt = self._format_date(mem.get("created_at"))
                sec.append(f"- ({dt}) {mem['text']}")
            memory_sections.append("\n".join(sec))

        relevant_memories_str = "\n\n".join(memory_sections) if memory_sections else "Nenhum conhecimento prévio relevante encontrado."

        current_trainer_type = trainer_profile_obj.trainer_type or "atlas"
        
        # Get conversation memory with summarization support
        conversation_memory = self._database.get_conversation_memory(
            session_id=user_email,
            llm=self._llm_client._llm,  # Use same LLM for summarization
            max_token_limit=settings.SUMMARY_MAX_TOKEN_LIMIT,
        )
        
        # Load memory variables (includes summary + recent messages if buffer exceeded)
        memory_vars = conversation_memory.load_memory_variables({})
        chat_history_messages = memory_vars.get("chat_history", [])
        
        # Format messages with trainer context
        chat_history_summary = self._format_memory_messages(
            chat_history_messages,
            current_trainer_type=current_trainer_type,
        )

        trainer_profile_summary = trainer_profile_obj.get_trainer_profile_summary()
        user_profile_summary = profile.get_profile_summary()

        # Build input data and generate response
        input_data = {
            "trainer_profile": trainer_profile_summary,
            "user_profile": user_profile_summary,
            "relevant_memories": relevant_memories_str,
            "chat_history_summary": chat_history_summary,
            "user_message": user_input,
        }

        prompt_template = self._get_prompt_template(input_data, is_telegram=is_telegram)
        
        # Create workout tracking tools with injected dependencies
        save_workout_tool = create_save_workout_tool(self._database, user_email)
        get_workouts_tool = create_get_workouts_tool(self._database, user_email)
        
        # Create nutrition tracking tools
        save_nutrition_tool = create_save_nutrition_tool(self._database, user_email)
        get_nutrition_tool = create_get_nutrition_tool(self._database, user_email)
        
        # Create composition tracking tools
        save_composition_tool = create_save_composition_tool(self._database, user_email)
        get_composition_tool = create_get_composition_tool(self._database, user_email)
        
        # Create Hevy tools
        from src.services.hevy_tools import (
            create_list_hevy_routines_tool,
            create_create_hevy_routine_tool,
            create_update_hevy_routine_tool,
            create_search_hevy_exercises_tool
        )
        from src.services.hevy_service import HevyService
        hevy_service = HevyService(workout_repository=self._database.workouts_repo)
        
        list_hevy_routines_tool = create_list_hevy_routines_tool(hevy_service, self._database, user_email)
        create_hevy_routine_tool = create_create_hevy_routine_tool(hevy_service, self._database, user_email)
        update_hevy_routine_tool = create_update_hevy_routine_tool(hevy_service, self._database, user_email)
        search_hevy_exercises_tool = create_search_hevy_exercises_tool(hevy_service, self._database, user_email)
        
        # Create profile management tools
        from src.services.profile_tools import create_get_user_goal_tool, create_update_user_goal_tool
        get_user_goal_tool = create_get_user_goal_tool(self._database, user_email)
        update_user_goal_tool = create_update_user_goal_tool(self._database, user_email)
        
        tools = [
            save_workout_tool, 
            get_workouts_tool, 
            save_nutrition_tool, 
            get_nutrition_tool,
            save_composition_tool,
            get_composition_tool,
            list_hevy_routines_tool,
            create_hevy_routine_tool,
            update_hevy_routine_tool,
            search_hevy_exercises_tool,
            get_user_goal_tool,
            update_user_goal_tool
        ]
        
        full_response = []
        for chunk in self._llm_client.stream_with_tools(
            prompt_template=prompt_template, input_data=input_data, tools=tools
        ):
            full_response.append(chunk)
            yield chunk

        final_response = "".join(full_response)
        # Flatten response for single-line logging
        flat_response = final_response.replace("\n", "\\n")
        log_response = (flat_response[:500] + "...") if len(flat_response) > 500 else flat_response
        logger.debug("LLM responded with: %s", log_response)

        # Save to MongoDB synchronously
        self._add_to_mongo_history(user_email, user_input, final_response, current_trainer_type)
        
        if background_tasks:
            # We removed the restriction 'if not write_tool_was_called' because mixed messages
            # (e.g. "updated goal AND have allergy") were causing critical facts (allergy) to be lost.
            # Mem0 handles deduplication reasonably well, or we can refine later. Priority is capturing facts.
            background_tasks.add_task(
                _add_to_mem0_background,
                memory=self._memory,
                user_email=user_email,
                user_input=user_input,
                response_text=final_response
            )
            logger.info("Scheduled Mem0 background task for user: %s", user_email)

    def send_message_sync(
        self, user_email: str, user_input: str, is_telegram: bool = False
    ) -> str:
        """
        Synchronous version of send_message_ai for Telegram.
        Returns complete response instead of streaming.
        Also saves to MongoDB history.
        
        Args:
            user_email: User's email address.
            user_input: User's message text.
            
        Returns:
            Complete AI response as string.
        """
        # Collect all chunks from the generator
        response_parts = []
        
        # Create a dummy BackgroundTasks for the generator
        from fastapi import BackgroundTasks
        background_tasks = BackgroundTasks()
        
        for chunk in self.send_message_ai(
            user_email=user_email,
            user_input=user_input,
            background_tasks=background_tasks,
            is_telegram=is_telegram
        ):
            response_parts.append(chunk)
        
        return "".join(response_parts)

    def generate_insight_stream(self, user_email: str, weeks: int = 3):
        """
        Generates a focused AI insight about metabolism using RAW data.
        Streams the response.
        """
        logger.info("Generating metabolism insight stream for user: %s (weeks=%d)", user_email, weeks)
        
        from src.services.metabolism_cache import MetabolismInsightCache
        from src.services.raw_metabolism_data import RawMetabolismDataService
        
        cache = MetabolismInsightCache(self._database)
        raw_service = RawMetabolismDataService(self._database)
        
        # 1. Fetch Raw Data
        data = raw_service.get_raw_data_for_insight(user_email, lookback_weeks=weeks)
        weight_logs = data["weight_logs"]
        nutrition_logs = data["nutrition_logs"]
        profile = data["user_profile"]
        
        if not profile:
            profile = self._get_or_create_user_profile(user_email)

        trainer_profile_obj = self._get_or_create_trainer_profile(user_email)
        trainer_summary = trainer_profile_obj.get_trainer_profile_summary()
        current_trainer_type = trainer_profile_obj.trainer_type or "atlas"
        
        # Prepare User Goal Dict for Cache Key
        user_goal = {
            "goal_type": profile.goal_type,
            "weekly_rate": profile.weekly_rate,
            "target_weight": profile.target_weight
        }
        
        # 2. Check Cache with NEW Strategy
        cached_insight = cache.get(user_email, weight_logs, nutrition_logs, user_goal, current_trainer_type)
        if cached_insight:
            yield cached_insight
            return

        # 3. Construct System Prompt
        system_prompt = f"""# 🏋️ Treinador Pessoal - Análise Metabólica

{trainer_summary}

---

## 🎨 Contexto de Exibição
- Este texto será exibido no **Hero Card** do dashboard de metabolismo
- O aluno verá esta análise ao abrir a página
- Você deve ser DIRETO e VISUAL (hero = destaque)

## 📋 Sua Tarefa
Analise os dados brutos de PESO e DIETA fornecidos pelo aluno e dê sua **OPINIÃO como treinador**:

1. **Tendência:** O que os números mostram? (calculando você mesmo)
2. **Alertas:** Padrões preocupantes, gaps, inconsistências?
3. **Próximo passo:** Uma ação concreta para esta semana.

## ⚠️ Regras de Formato
- **Máximo 100 palavras**
- Use **Emojis** moderadamente para alertas (ex: ⚠️, 🎯, 🔥)
- Vá direto à análise (sem saudações)
- Use **negrito** para insights acionáveis
"""

        # 4. Construct User Prompt (Raw Data)
        start_date_str = data["period"]["start_date"].strftime("%d/%m")
        end_date_str = data["period"]["end_date"].strftime("%d/%m")
        
        # Limit tables to reasonable size (e.g. 30 most recent rows) to avoid context overflow
        # Logs are already sorted ascending, so take last 30
        clipped_weight_logs = weight_logs[-30:]
        clipped_nutrition_logs = nutrition_logs[-30:]
        
        weight_table = raw_service.format_weight_logs_table(clipped_weight_logs)
        nutrition_table = raw_service.format_nutrition_logs_table(clipped_nutrition_logs)
        
        goal_labels = {"lose": "Perder peso", "gain": "Ganhar massa", "maintain": "Manter peso"}
        goal_label = goal_labels.get(profile.goal_type, profile.goal_type)
        
        target_weight_Line = f"- **Peso meta:** {profile.target_weight} kg" if profile.target_weight else ""
        
        user_prompt_content = f"""## 🎯 Meu Objetivo
- **Objetivo:** {goal_label}
- **Taxa desejada:** {profile.weekly_rate} kg/semana
- **Peso ao cadastrar:** {profile.weight} kg
- **Dados pessoais:** {profile.height}cm, {profile.age} anos, {profile.gender}
{target_weight_Line}

## ⚖️ Minhas Pesagens ({start_date_str} - {end_date_str})

{weight_table}

## 🍽️ Minha Dieta

{nutrition_table}

Analise meus dados e me dê seu feedback como treinador.
"""

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{user_prompt_content}")
        ])
        
        input_data = {"user_prompt_content": user_prompt_content}
        
        # Log the full prompt in a single line for easy reading in server logs
        # Replace newlines with spaces to prevent log splitting
        clean_system = system_prompt.replace('\n', ' ')
        clean_user = user_prompt_content.replace('\n', ' ')
        
        logger.info(f"📤 INSIGHT PROMPT ENVIADO | SYSTEM: {clean_system} | USER: {clean_user}")
        
        # 5. Stream & Collect for Cache
        full_content = []
        for chunk in self._llm_client.stream_simple(prompt_template, input_data):
            full_content.append(chunk)
            yield chunk
            
        # 6. Save to Cache
        cache.set(user_email, weight_logs, nutrition_logs, user_goal, current_trainer_type, "".join(full_content))

    def get_all_memories(self, user_id: str, limit: int = 50) -> list[dict]:
        """
        Retrieves all memories for a given user from Mem0.

        Args:
            user_id (str): The user's email/ID.
            limit (int): Maximum number of memories to return.

        Returns:
            list[dict]: List of memory dictionaries with id, memory, created_at, updated_at.
        """
        logger.info("Retrieving memories for user: %s (limit: %d)", user_id, limit)
        try:
            result = self._memory.get_all(user_id=user_id)
            logger.debug("Raw Mem0 get_all response type: %s", type(result))
            
            # Debug: log actual response structure
            if isinstance(result, dict):
                logger.debug("Mem0 response keys: %s", result.keys())
                logger.debug("Mem0 full response: %s", result)

            memories = result if isinstance(result, list) else result.get("memories", result.get("results", []))
            logger.info("Retrieved %d memories from Mem0 for user: %s", len(memories), user_id)


            # Sort by created_at descending (newest first) and limit
            memories.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            limited_memories = memories[:limit]

            logger.debug("Returning %d memories after sorting and limiting", len(limited_memories))
            return limited_memories
        except Exception as e:
            logger.error("Failed to retrieve memories for user %s: %s", user_id, e)
            raise

    def delete_memory(self, memory_id: str) -> bool:
        """
        Deletes a specific memory from Mem0.

        Args:
            memory_id (str): The unique ID of the memory to delete.

        Returns:
            bool: True if deletion was successful.
        """
        logger.info("Attempting to delete memory: %s", memory_id)
        try:
            self._memory.delete(memory_id=memory_id)
            logger.info("Successfully deleted memory: %s", memory_id)
            return True
        except Exception as e:
            logger.error("Failed to delete memory %s: %s", memory_id, e)
            raise

    def get_memory_by_id(self, memory_id: str) -> dict | None:
        """
        Retrieves a specific memory by ID.
        
        Args:
            memory_id (str): The unique ID of the memory.
            
        Returns:
            dict | None: The memory object if found, otherwise None.
        """
        try:
            return self._memory.get(memory_id)
        except Exception as e:
            logger.error("Failed to get memory %s: %s", memory_id, e)
            return None

    def get_memories_paginated(
        self,
        user_id: str,
        page: int,
        page_size: int,
        qdrant_client,
        collection_name: str
    ) -> tuple[list[dict], int]:
        """
        Retrieves memories for a user with pagination via Qdrant scroll.

        Args:
            user_id: The user's email/ID
            page: Page number (1-indexed)
            page_size: Number of memories per page
            qdrant_client: Qdrant client for direct access
            collection_name: Qdrant collection name

        Returns:
            tuple: (list of memories, total count)
        """
        from qdrant_client import models as qdrant_models

        logger.info(
            "Retrieving paginated memories for user: %s (page: %d, size: %d)",
            user_id, page, page_size
        )

        try:
            # Filter by user_id
            user_filter = qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="user_id",
                        match=qdrant_models.MatchValue(value=user_id)
                    )
                ]
            )

            # Get total count for this user
            count_result = qdrant_client.count(
                collection_name=collection_name,
                count_filter=user_filter
            )
            total = count_result.count
            logger.debug("Total memories for user %s: %d", user_id, total)

            if total == 0:
                logger.info("No memories found for user: %s", user_id)
                return [], 0

            # Calculate offset for pagination
            offset = (page - 1) * page_size

            # Get all points for this user and manually paginate
            # Note: Qdrant scroll doesn't support direct offset, so we scroll and skip
            all_points = []
            next_offset = None

            while True:
                points, next_offset = qdrant_client.scroll(
                    collection_name=collection_name,
                    scroll_filter=user_filter,
                    limit=100,  # Fetch in batches
                    offset=next_offset,
                    with_payload=True
                )
                all_points.extend(points)
                if next_offset is None:
                    break

            # Sort by created_at descending (newest first)
            all_points.sort(
                key=lambda p: p.payload.get("created_at", "") if p.payload else "",
                reverse=True
            )

            # Apply pagination
            paginated_points = all_points[offset:offset + page_size]

            # Convert to memory dictionaries
            memories = []
            for point in paginated_points:
                payload = point.payload or {}
                memories.append({
                    "id": payload.get("id", str(point.id)),
                    "memory": payload.get("memory", payload.get("data", "")),
                    "created_at": payload.get("created_at"),
                    "updated_at": payload.get("updated_at"),
                })

            logger.info(
                "Returning %d memories for user %s (page %d of %d)",
                len(memories), user_id, page, (total + page_size - 1) // page_size
            )
            return memories, total

        except Exception as e:
            logger.error("Failed to retrieve paginated memories for user %s: %s", user_id, e)
            raise
