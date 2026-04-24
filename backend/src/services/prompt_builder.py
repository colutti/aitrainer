"""
Prompt building and injection service.

In the OpenRouter preset architecture, this builder is responsible for:
- Building input_data dictionary
- Building runtime context payload (PROMPT_CONTEXT_V1)
- Constructing ChatPromptTemplate with a minimal local system message
"""

from datetime import datetime
import json
from typing import Any
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from src.core.logs import logger
from src.core.config import settings
from src.services.plan_service import format_plan_snapshot


class PromptBuilder:
    """Builds and constructs chat prompt templates with runtime context injection."""

    RUNTIME_CONTEXT_PROMPT = (
        "RUNTIME_CONTEXT_JSON (PROMPT_CONTEXT_V1):\n"
        "{runtime_context_json}"
    )

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
            recur_str = (
                f" (recorrente: {event.recurrence})"
                if event.recurrence != "none"
                else ""
            )
            lines.append(f"- {date_str} {event.title}{recur_str}")

        return "\n".join(lines)

    @staticmethod
    def _format_metabolism_section(metabolism_data: dict | None) -> str:
        """Format official metabolism and daily-target context for prompt grounding."""
        if not metabolism_data:
            return ""

        macro_targets = metabolism_data.get("macro_targets") or {}

        def _field(block: dict, key: str) -> str:
            value = block.get(key)
            return str(value) if value is not None else "indisponivel"

        return (
            "Fonte oficial (algoritmo adaptativo):\n"
            f"- TDEE atual: {_field(metabolism_data, 'tdee')} kcal\n"
            f"- Meta diaria atual: {_field(metabolism_data, 'daily_target')} kcal\n"
            f"- Objetivo: {_field(metabolism_data, 'goal_type')} "
            f"({_field(metabolism_data, 'goal_weekly_rate')} kg/semana)\n"
            f"- Confianca do algoritmo: {_field(metabolism_data, 'confidence')}\n"
            "- Macros de referencia do algoritmo:\n"
            f"  - Proteina: {_field(macro_targets, 'protein_g')} g\n"
            f"  - Carboidratos: {_field(macro_targets, 'carbs_g')} g\n"
            f"  - Gorduras: {_field(macro_targets, 'fat_g')} g"
        )

    @staticmethod
    # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    def build_input_data(
        profile,
        trainer_profile_summary: str,
        user_profile_summary: str,
        formatted_history_msgs,
        user_input: str,
        current_date: str | None = None,
        agenda_events: list | None = None,
        plan_snapshot=None,
        metabolism_data: dict | None = None,
    ) -> dict:
        """
        Constructs the input data dictionary for prompt template injection.

        Args:
            profile: UserProfile object
            trainer_profile_summary: Trainer description string
            user_profile_summary: User profile description string
            formatted_history_msgs: List[BaseMessage] for MessagesPlaceholder
            user_input: Current user message
            current_date: Current date string (YYYY-MM-DD)
            agenda_events: List of ScheduledEventWithId for agenda section

        Returns:
            dict: Input data ready for prompt template
        """
        dias_pt = {
            0: "Segunda-feira",
            1: "Terça-feira",
            2: "Quarta-feira",
            3: "Quinta-feira",
            4: "Sexta-feira",
            5: "Sábado",
            6: "Domingo",
        }

        now = datetime.now()
        if not current_date:
            current_date = now.strftime("%Y-%m-%d")

        # Wrap user message with <msg> tag including current date/time
        date_str = now.strftime("%d/%m")
        time_str = now.strftime("%H:%M")
        user_message_with_tag = (
            f'<msg data="{date_str}" hora="{time_str}">{user_input}</msg>'
        )

        # Format agenda section
        agenda_section = PromptBuilder._format_agenda_section(agenda_events or [])
        plan_section = format_plan_snapshot(plan_snapshot)
        has_active_plan = plan_snapshot is not None
        metabolism_section = PromptBuilder._format_metabolism_section(metabolism_data)
        raw_timezone = getattr(profile, "timezone", None)
        user_timezone = (
            raw_timezone
            if isinstance(raw_timezone, str) and raw_timezone
            else "Europe/Madrid"
        )
        raw_user_name = getattr(profile, "display_name", None)
        user_name = raw_user_name if isinstance(raw_user_name, str) and raw_user_name else "Aluno"
        runtime_context = {
            "contract_version": settings.PROMPT_CONTEXT_CONTRACT_VERSION,
            "session": {
                "current_date": current_date,
                "current_time": now.strftime("%H:%M"),
                "day_of_week": dias_pt[now.weekday()],
                "user_timezone": user_timezone,
                "channel": "app",
            },
            "trainer": {
                "name": PromptBuilder._extract_trainer_name(trainer_profile_summary),
                "profile": trainer_profile_summary,
            },
            "user": {
                "name": user_name,
                "profile": user_profile_summary,
            },
            "agenda": {
                "events_summary": agenda_section,
            },
            "metabolism": {
                "summary": metabolism_section,
            },
            "plan": {
                "summary": plan_section,
                "has_active_plan": has_active_plan,
            },
        }

        return {
            "trainer_profile": trainer_profile_summary,
            "trainer_name": runtime_context["trainer"]["name"],
            "user_profile": user_profile_summary,
            "user_profile_obj": profile,  # Passed for extraction
            "user_name": user_name,
            "user_timezone": user_timezone,
            "chat_history": formatted_history_msgs,  # For MessagesPlaceholder
            "user_message": user_message_with_tag,
            "agenda_section": agenda_section,  # Agenda section for dynamic context
            "plan_section": plan_section,
            "metabolism_section": metabolism_section,
            "current_date": current_date,
            "day_of_week": dias_pt[now.weekday()],
            "current_time": now.strftime("%H:%M"),
            "runtime_context": runtime_context,
            "runtime_context_json": json.dumps(
                runtime_context, ensure_ascii=True, sort_keys=True
            ),
        }

    @staticmethod
    def _extract_trainer_name(trainer_profile_summary: str) -> str:
        if "**Nome:**" in trainer_profile_summary:
            try:
                return (
                    trainer_profile_summary.split("**Nome:**")[1].split("\n")[0].strip()
                )
            except (IndexError, AttributeError):
                pass
        return "Treinador"

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
        logger.debug(
            "Constructing chat prompt template with runtime context (is_telegram=%s).",
            is_telegram,
        )

        input_data.setdefault("runtime_context", {})
        runtime_context = dict(input_data["runtime_context"])
        session = dict(runtime_context.get("session") or {})
        session["channel"] = "telegram" if is_telegram else "app"
        runtime_context["session"] = session
        input_data["runtime_context"] = runtime_context
        input_data["runtime_context_json"] = json.dumps(
            runtime_context, ensure_ascii=True, sort_keys=True
        )

        # 4. Build messages with MessagesPlaceholder for history
        messages: list[Any] = [("system", PromptBuilder.RUNTIME_CONTEXT_PROMPT)]
        messages.append(MessagesPlaceholder(variable_name="chat_history"))
        messages.append(("human", "{user_message}"))

        prompt_template = ChatPromptTemplate.from_messages(messages)

        # 5. Verify formatting and log
        try:
            rendered_prompt = prompt_template.format(**input_data)
            logger.debug(
                "Prompt built with runtime context | Chars: %d",
                len(rendered_prompt),
            )
        except KeyError as e:
            logger.error(
                "🛡️ ERROR: KeyError during prompt building: %s. Unescaped braces?",
                e,
            )
            raise

        return prompt_template
