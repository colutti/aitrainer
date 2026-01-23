from datetime import datetime
from src.core.logs import logger
from src.services.database import MongoDatabase
from src.services.llm_client import LLMClient
from src.prompts.summary_update_prompt import SUMMARY_UPDATE_PROMPT
from langchain_core.prompts import PromptTemplate


class HistoryCompactor:
    def __init__(self, database: MongoDatabase, llm_client: LLMClient):
        self.db = database
        self.llm_client = llm_client

    async def compact_history(self, user_email: str, active_window_size: int = 40, log_callback=None):
        """
        Identifies old messages outside the active window, summarizes them,
        and updates the user's long-term summary.
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
                if msg.sender == "student":
                    sender_label = "Aluno"
                elif msg.sender == "trainer":
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
        # Since we just want a string back, use simple invoke
        # We can use the simple_invoke method if it exists, or stream and join

        # LLMClient abstraction might need a direct generation method.
        # Using stream_simple for now and joining.
        response_text = ""
        try:
            generator = self.llm_client.stream_simple(
                prompt_template=prompt,
                input_data={
                    "current_summary": current_summary,
                    "new_lines": new_lines_text,
                },
                user_email=user_email,
                log_callback=log_callback,
            )
            async for chunk in generator:
                response_text += chunk
        except Exception as e:
            logger.error("LLM Error during compaction: %s", e)
            return

        if not response_text.strip():
            logger.warning("Empty summary generated. Aborting update.")
            return

        # 6. Atomic Update
        # Update profile with new summary and new timestamp using partial update
        # to prevent overwriting concurrent changes (e.g. Hevy settings)
        success = self.db.update_user_profile_fields(
            user_email,
            {
                "long_term_summary": response_text.strip(),
                "last_compaction_timestamp": new_last_ts_str,
            },
        )

        if success:
            logger.info("Compaction complete. Summary updated atomically.")
        else:
            logger.warning("Compaction complete but no fields were updated.")
