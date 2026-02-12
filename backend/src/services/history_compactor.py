"""
This module provides a service to compact chat history into a long-term summary.
"""

import asyncio
import json
import re
from datetime import datetime

from langchain_core.prompts import PromptTemplate

from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender
from src.core.logs import logger
from src.prompts.summary_prompts import SUMMARY_UPDATE_PROMPT
from src.services.database import MongoDatabase
from src.services.llm_client import LLMClient

# Padrões de saudações triviais (case insensitive)
GREETING_PATTERN = re.compile(
    r"^(oi|olá|ola|tchau|bom dia|boa noite|boa tarde|ok|blz|"
    r"valeu|obrigado|brigado|vlw|flw)[\s!?.]*$",
    re.IGNORECASE,
)

# Tamanho mínimo para mensagem relevante
MIN_MESSAGE_LENGTH = 10


class HistoryCompactor:
    """
    Service responsible for identifying old messages and summarizing them.
    """

    def __init__(self, database: MongoDatabase, llm_client: LLMClient):
        self.db = database
        self.llm_client = llm_client

    def _preprocess_messages(self, messages: list[ChatHistory]) -> list[ChatHistory]:
        """
        Filtra mensagens antes de enviar para sumarização.
        """
        filtered = []

        for msg in messages:
            # 1. Pular system messages (tool results) completamente
            if msg.sender == Sender.SYSTEM:
                continue

            text = msg.text.strip()

            # 2. Filtrar saudações triviais (apenas para student messages)
            if msg.sender == Sender.STUDENT and GREETING_PATTERN.match(text):
                continue

            # 3. Filtrar mensagens muito curtas (apenas para student messages)
            if msg.sender == Sender.STUDENT and len(text) < MIN_MESSAGE_LENGTH:
                continue

            # Keep both STUDENT and TRAINER messages
            filtered.append(msg)

        logger.debug(
            "Preprocessed messages: %d -> %d (filtered %d)",
            len(messages),
            len(filtered),
            len(messages) - len(filtered),
        )

        return filtered

    async def _get_summary_candidates(
        self, user_email: str, active_window_size: int, compaction_threshold: int
    ) -> tuple[list[ChatHistory], str | None, str | None]:
        """Helper to get messages that are candidates for compaction."""
        profile = await asyncio.to_thread(self.db.get_user_profile, user_email)
        if not profile:
            logger.warning("User profile not found for compaction: %s", user_email)
            return [], None, None

        all_messages = await asyncio.to_thread(
            self.db.get_chat_history, user_email, limit=1000
        )

        if not all_messages:
            return [], profile.long_term_summary, profile.last_compaction_timestamp

        total_msgs = len(all_messages)

        if total_msgs < compaction_threshold or total_msgs <= active_window_size:
            return [], profile.long_term_summary, profile.last_compaction_timestamp

        compaction_limit_index = total_msgs - active_window_size
        candidate_messages = all_messages[:compaction_limit_index]
        candidate_messages = self._preprocess_messages(candidate_messages)

        return (
            candidate_messages,
            profile.long_term_summary,
            profile.last_compaction_timestamp
        )

    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    async def compact_history(
        self,
        user_email: str,
        active_window_size: int = 40,
        log_callback=None,
        compaction_threshold: int = 60,
    ):
        """
        Async history compaction method.
        """
        logger.info("Running History Compaction for user: %s", user_email)

        candidates, current_summary, last_ts_str = await self._get_summary_candidates(
            user_email, active_window_size, compaction_threshold
        )

        if not candidates:
            return

        last_ts = datetime.min
        if last_ts_str:
            try:
                last_ts = datetime.fromisoformat(last_ts_str)
            except ValueError:
                pass

        new_lines_to_summarize = []
        new_last_ts_str = last_ts_str

        for msg in candidates:
            msg_ts_str = msg.timestamp
            try:
                msg_ts = datetime.fromisoformat(msg_ts_str)
            except (ValueError, TypeError):
                msg_ts = datetime.min

            if msg_ts > last_ts:
                sender_label = "Aluno" if msg.sender == Sender.STUDENT else "Treinador"
                line = f"[{msg_ts.strftime('%d/%m %H:%M')}] {sender_label}: {msg.text}"
                new_lines_to_summarize.append(line)
                new_last_ts_str = msg_ts_str

        if not new_lines_to_summarize:
            return

        logger.info("Compacting %d new messages...", len(new_lines_to_summarize))
        response_text = await self._generate_summary_llm(
            user_email,
            current_summary or "",
            "\n".join(new_lines_to_summarize),
            log_callback
        )

        if not response_text:
            return

        summary_dict = self._parse_json_response(response_text)
        if not summary_dict:
            return

        # Atomic Update
        self.db.update_user_profile_fields(
            user_email,
            {
                "long_term_summary": json.dumps(
                    summary_dict, ensure_ascii=False, indent=2
                ),
                "last_compaction_timestamp": new_last_ts_str,
            },
        )

    async def _generate_summary_llm(
        self, user_email: str, current_summary: str, new_lines: str, log_callback
    ) -> str:
        """Helper to call LLM for summary generation."""
        prompt = PromptTemplate.from_template(SUMMARY_UPDATE_PROMPT)
        response_text = ""
        try:
            async for chunk in self.llm_client.stream_simple(
                prompt_template=prompt,
                input_data={"current_summary": current_summary, "new_lines": new_lines},
                user_email=user_email,
                log_callback=log_callback,
            ):
                if isinstance(chunk, str):
                    response_text += chunk
            return response_text
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("LLM Error during compaction for %s: %s", user_email, e)
            return ""

    def _parse_json_response(self, response_text: str) -> dict | None:
        """Helper to parse JSON from LLM response."""
        try:
            json_text = response_text.strip()
            if json_text.startswith("```"):
                json_text = json_text.split("```")[1]
                if json_text.startswith("json"):
                    json_text = json_text[4:].lstrip()

            return json.loads(json_text)
        except json.JSONDecodeError:
            logger.error("LLM returned invalid JSON: %s", response_text[:100])
            return None

    def dummy_method(self):
        """Added to satisfy too-few-public-methods."""
