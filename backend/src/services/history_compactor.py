import json
import re
from datetime import datetime
from src.core.logs import logger
from src.services.database import MongoDatabase
from src.services.llm_client import LLMClient
from src.prompts.summary_prompts import SUMMARY_UPDATE_PROMPT
from langchain_core.prompts import PromptTemplate
from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender

# Padrões de saudações triviais (case insensitive)
GREETING_PATTERN = re.compile(
    r"^(oi|olá|ola|tchau|bom dia|boa noite|boa tarde|ok|blz|valeu|obrigado|brigado|vlw|flw)[\s!?.]*$",
    re.IGNORECASE,
)

# Tamanho mínimo para mensagem relevante
MIN_MESSAGE_LENGTH = 10


class HistoryCompactor:
    def __init__(self, database: MongoDatabase, llm_client: LLMClient):
        self.db = database
        self.llm_client = llm_client

    def _preprocess_messages(self, messages: list[ChatHistory]) -> list[ChatHistory]:
        """
        Filtra mensagens antes de enviar para sumarização.

        Mantém apenas mensagens do ALUNO que contêm fatos relevantes.
        Remove:
        - Mensagens de treinador/sistema (padrão Mem0: extrair fatos do usuário)
        - Saudações triviais (oi, tchau, ok, etc)
        - Mensagens muito curtas (< 10 chars)

        Args:
            messages: Lista de ChatHistory para filtrar

        Returns:
            Lista filtrada contendo apenas mensagens relevantes do aluno
        """
        filtered = []

        for msg in messages:
            # 1. Manter apenas mensagens do aluno
            if msg.sender != Sender.STUDENT:
                continue

            text = msg.text.strip()

            # 2. Filtrar saudações triviais
            if GREETING_PATTERN.match(text):
                continue

            # 3. Filtrar mensagens muito curtas
            if len(text) < MIN_MESSAGE_LENGTH:
                continue

            filtered.append(msg)

        logger.debug(
            "Preprocessed messages: %d -> %d (filtered %d)",
            len(messages),
            len(filtered),
            len(messages) - len(filtered),
        )

        return filtered

    async def compact_history(self, user_email: str, active_window_size: int = 40, log_callback=None, compaction_threshold: int = 60):  # Default matches config.MAX_SHORT_TERM_MEMORY_MESSAGES
        """
        Async history compaction method.
        Identifies old messages outside the active window, summarizes them,
        and updates the user's long-term summary.

        This method can be safely called from FastAPI background tasks as an async function.

        Args:
            user_email: User email
            active_window_size: Number of recent messages to keep (default 20)
            log_callback: Optional callback for logging
            compaction_threshold: Only compact if buffer >= threshold (default 30)
        """
        logger.info("Running History Compaction for user: %s", user_email)

        # 1. Fetch User Profile
        profile = self.db.get_user_profile(user_email)
        if not profile:
            logger.warning("User profile not found for compaction: %s", user_email)
            return

        # 2. Fetch ALL History (Abstracted via LangChain storage)
        # We fetch a larger limit to ensure we capture enough history to compact
        # Assuming database.get_chat_history returns a list of ChatHistory objects
        # sorted by timestamp ASC (oldest first).
        all_messages = self.db.get_chat_history(user_email, limit=1000)

        if not all_messages:
            logger.debug("No history to compact.")
            return

        total_msgs = len(all_messages)

        # BATCH: Only compact if buffer >= compaction_threshold
        # This reduces LLM calls (from every message to every 30+ messages)
        if total_msgs < compaction_threshold:
            logger.debug(
                "History size (%d) below compaction threshold (%d). Skipping.",
                total_msgs,
                compaction_threshold,
            )
            return

        if total_msgs <= active_window_size:
            logger.debug(
                "History size (%d) within active window (%d). Skipping.",
                total_msgs,
                active_window_size,
            )
            return

        # 3. Identify Candidates for Compaction
        # We want to compact everything OLDER than the active window.
        # Candidates = messages[0 : total - window]
        compaction_limit_index = total_msgs - active_window_size
        candidate_messages = all_messages[:compaction_limit_index]

        # 3.5 PRE-PROCESS: Filter to keep only relevant student messages
        candidate_messages = self._preprocess_messages(candidate_messages)

        if not candidate_messages:
            logger.debug("No relevant student messages to compact after preprocessing.")
            return

        # 4. Filter out already compacted messages based on timestamp
        last_ts_str = profile.last_compaction_timestamp
        last_ts = datetime.min
        if last_ts_str:
            try:
                last_ts = datetime.fromisoformat(last_ts_str)
            except ValueError:
                pass

        new_lines_to_summarize = []
        new_last_ts_str = last_ts_str

        for msg in candidate_messages:
            msg_ts_str = msg.timestamp
            try:
                msg_ts = datetime.fromisoformat(msg_ts_str)
            except (ValueError, TypeError):
                # If no timestamp, treat as very old or skip?
                # Let's include if it has content.
                msg_ts = datetime.min

            if msg_ts > last_ts:
                # This is a new message that needs compaction
                if msg.sender == Sender.STUDENT:
                    sender_label = "Aluno"
                elif msg.sender == Sender.TRAINER:
                    sender_label = "Treinador"
                else:
                    sender_label = "Sistema"

                line = f"[{msg_ts.strftime('%d/%m %H:%M')}] {sender_label}: {msg.text}"
                new_lines_to_summarize.append(line)
                new_last_ts_str = msg_ts_str

        if not new_lines_to_summarize:
            logger.debug("No NEW messages to summarize found.")
            return

        logger.info("Compacting %d new messages...", len(new_lines_to_summarize))

        # 5. Generate Summary
        current_summary = profile.long_term_summary or ""
        new_lines_text = "\n".join(new_lines_to_summarize)

        prompt = PromptTemplate.from_template(SUMMARY_UPDATE_PROMPT)
        response_text = ""
        try:
            # Collect chunks from the LLM stream
            # stream_simple is async generator, so we iterate it within the async context
            async for chunk in self.llm_client.stream_simple(
                prompt_template=prompt,
                input_data={
                    "current_summary": current_summary,
                    "new_lines": new_lines_text,
                },
                user_email=user_email,
                log_callback=log_callback,
            ):
                if isinstance(chunk, str):
                    response_text += chunk
        except Exception as e:
            logger.error("LLM Error during compaction: %s", e)
            logger.error("Full error details:", exc_info=True)
            return

        if not response_text.strip():
            logger.warning("Empty summary generated. Aborting update.")
            return

        # 6. Validate JSON Structure and Critical Categories
        try:
            # Remove markdown code blocks if present
            json_text = response_text.strip()
            if json_text.startswith("```"):
                # Extract JSON from markdown code block
                json_text = json_text.split("```")[1]
                if json_text.startswith("json"):
                    json_text = json_text[4:].lstrip()

            summary_dict = json.loads(json_text)
        except json.JSONDecodeError:
            logger.error("LLM returned invalid JSON: %s", response_text[:100])
            return

        # Validate critical categories exist
        critical_categories = ["health", "restrictions"]
        for cat in critical_categories:
            if cat not in summary_dict or not summary_dict.get(cat):
                logger.warning(
                    "⚠️  Category '%s' missing or empty in compacted summary for %s",
                    cat,
                    user_email,
                )

        # 7. Atomic Update
        # Store JSON as string in long_term_summary field
        success = self.db.update_user_profile_fields(
            user_email,
            {
                "long_term_summary": json.dumps(summary_dict, ensure_ascii=False, indent=2),
                "last_compaction_timestamp": new_last_ts_str,
            },
        )

        if success:
            logger.info(
                "Compaction complete. Summary updated atomically. Categories: %s",
                list(summary_dict.keys()),
            )
        else:
            logger.warning("Compaction complete but no fields were updated.")
