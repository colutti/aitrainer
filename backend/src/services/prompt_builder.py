"""
Prompt building and injection service.

Extracts prompt template construction from AITrainerBrain for better modularity:
- Building input_data dictionary
- Constructing ChatPromptTemplate with defensive injection
- Handling long_term_summary and memory placement
"""

from datetime import datetime
from typing import Any
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from src.core.config import settings
from src.core.logs import logger



class PromptBuilder:
    """Builds and constructs chat prompt templates with defensive injection."""

    @staticmethod
    def _format_agenda_section(agenda_events: list) -> str:
        """
        Format scheduled events into a readable agenda section.

        Args:
            agenda_events: List of ScheduledEventWithId objects

        Returns:
            Formatted string for agenda section, or empty string if no events
        """
        if not agenda_events:
            return ""

        lines = ["Eventos/planos ativos:"]
        for event in agenda_events:
            date_str = f"[{event.date}]" if event.date else "[sem prazo]"
            recur_str = f" (recorrente: {event.recurrence})" if event.recurrence != "none" else ""
            lines.append(f"- {date_str} {event.title}{recur_str}")

        return "\n".join(lines)

    @staticmethod
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def build_input_data(
        profile,
        trainer_profile_summary: str,
        user_profile_summary: str,
        relevant_memories_str: str,
        chat_history_summary: str,
        formatted_history_msgs,
        user_input: str,
        current_date: str | None = None,
        agenda_events: list | None = None,
    ) -> dict:
        """
        Constructs the input data dictionary for prompt template injection.

        Args:
            profile: UserProfile object
            trainer_profile_summary: Trainer description string
            user_profile_summary: User profile description string
            relevant_memories_str: Formatted memories string
            chat_history_summary: Legacy chat history string (for compatibility)
            formatted_history_msgs: List[BaseMessage] for MessagesPlaceholder
            user_input: Current user message
            current_date: Current date string (YYYY-MM-DD)
            agenda_events: List of ScheduledEventWithId for agenda section

        Returns:
            dict: Input data ready for prompt template
        """
        DIAS_PT = {
            0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira",
            3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo"
        }

        now = datetime.now()
        if not current_date:
            current_date = now.strftime("%Y-%m-%d")

        # Wrap user message with <msg> tag including current date/time
        date_str = now.strftime('%d/%m')
        time_str = now.strftime('%H:%M')
        user_message_with_tag = f'<msg data="{date_str}" hora="{time_str}">{user_input}</msg>'

        # Format agenda section
        agenda_section = PromptBuilder._format_agenda_section(agenda_events or [])

        return {
            "trainer_profile": trainer_profile_summary,
            "user_profile": user_profile_summary,
            "user_profile_obj": profile,  # Passed for extraction
            "relevant_memories": relevant_memories_str,
            "chat_history_summary": chat_history_summary,  # Legacy (removed from template V3)
            "chat_history": formatted_history_msgs,  # For MessagesPlaceholder
            "user_message": user_message_with_tag,
            "agenda_section": agenda_section,  # Agenda section for dynamic context
            "current_date": current_date,
            "day_of_week": DIAS_PT[now.weekday()],
            "current_time": now.strftime("%H:%M"),
        }

    @staticmethod
    def get_prompt_template(
        input_data: dict, is_telegram: bool = False
    ) -> ChatPromptTemplate:
        """
        Constructs and returns the chat prompt template with defensive injection.

        🛡️ DEFENSIVE INJECTION PATTERN (V3):
        - Move potentially 'dirty' content (with braces {}) to dedicated placeholders
        - Prevents LangChain from interpreting them as template variables
        - Use MessagesPlaceholder for chat history instead of string placeholder

        Args:
            input_data: Input data dictionary from build_input_data()
            is_telegram: Whether response should be Telegram-optimized

        Returns:
            ChatPromptTemplate: Ready-to-use prompt template
        """
        logger.debug("Constructing chat prompt template (is_telegram=%s).", is_telegram)

        # Get base template
        system_content = settings.PROMPT_TEMPLATE

        # 1. Inject Long-Term Summary
        user_profile = input_data.get("user_profile_obj")
        if user_profile and user_profile.long_term_summary:
            input_data["long_term_summary_section"] = (
                f"\n\n{user_profile.long_term_summary}"
            )
        else:
            input_data["long_term_summary_section"] = ""

        # 2. Ensure current_date exists
        if "current_date" not in input_data:
            input_data["current_date"] = datetime.now().strftime("%Y-%m-%d")

        # 3. Remove legacy chat_history_summary placeholder
        # We use MessagesPlaceholder instead
        system_content = system_content.replace("{chat_history_summary}", "")

        # 4. Add Telegram format if needed
        if is_telegram:
            system_content += (
                "\n\n--- \n"
                "⚠️ **FORMATO TELEGRAM (MOBILE)**: "
                "Responda de forma direta e concisa. Use Markdown simples. "
                "Evite tabelas e blocos de código extensos."
            )

        # 5. Build messages with MessagesPlaceholder for history
        messages: list[Any] = [("system", system_content)]
        messages.append(MessagesPlaceholder(variable_name="chat_history"))
        messages.append(("human", "{user_message}"))

        prompt_template = ChatPromptTemplate.from_messages(messages)

        # 6. Verify formatting and log
        try:
            rendered_prompt = prompt_template.format(**input_data)
            has_critical = "[CRÍTICO]" in rendered_prompt
            critical_check = "✅ Presente" if has_critical else "⚠️ Ausente"
            logger.debug(
                "🛡️ PROMPT BUILT: Critical Section: %s | Chars: %d",
                critical_check,
                len(rendered_prompt),
            )
        except KeyError as e:
            logger.error(
                "🛡️ ERROR: KeyError during prompt building: %s. Unescaped braces?",
                e,
            )
            raise

        return prompt_template
