from datetime import datetime
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.language_models import BaseChatModel
from langchain_classic.memory import (
    ConversationSummaryBufferMemory,
    ConversationBufferWindowMemory,
)

from src.core.config import settings
from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender
from src.repositories.base import BaseRepository


class ChatRepository(BaseRepository):
    def __init__(self, database):
        # We don't use self.collection directly for some of these but we pass database anyway
        super().__init__(
            database, "chat_history"
        )  # Collection name might vary but MongoDBChatMessageHistory handles it

    def get_history(self, user_id: str, limit: int = 20) -> list[ChatHistory]:
        self.logger.debug(
            "Retrieving chat history for session: %s (limit: %d)", user_id, limit
        )
        history = MongoDBChatMessageHistory(
            connection_string=settings.MONGO_URI,
            session_id=user_id,
            database_name=settings.DB_NAME,
            history_size=limit,
        )
        return ChatHistory.from_mongodb_chat_message_history(history)

    def add_message(
        self,
        chat_history: ChatHistory,
        session_id: str,
        trainer_type: str | None = None,
    ):
        self.logger.debug("Adding messages to chat history with timestamp.")
        now = datetime.now().isoformat()
        chat_history_mongo = MongoDBChatMessageHistory(
            connection_string=settings.MONGO_URI,
            session_id=session_id,
            database_name=settings.DB_NAME,
            history_size=settings.MAX_SHORT_TERM_MEMORY_MESSAGES,
        )

        additional_kwargs = {"timestamp": now}
        if trainer_type:
            additional_kwargs["trainer_type"] = trainer_type

        if chat_history.sender == Sender.TRAINER:
            chat_history_mongo.add_message(
                AIMessage(
                    content=chat_history.text, additional_kwargs=additional_kwargs
                )
            )
        else:
            chat_history_mongo.add_message(
                HumanMessage(
                    content=chat_history.text, additional_kwargs=additional_kwargs
                )
            )

    def get_memory_buffer(
        self,
        session_id: str,
        llm: BaseChatModel,
        max_token_limit: int | None = None,
    ) -> ConversationSummaryBufferMemory:
        if max_token_limit is None:
            max_token_limit = settings.SUMMARY_MAX_TOKEN_LIMIT

        chat_history = MongoDBChatMessageHistory(
            connection_string=settings.MONGO_URI,
            session_id=session_id,
            database_name=settings.DB_NAME,
            history_size=settings.MAX_SHORT_TERM_MEMORY_MESSAGES,
        )

        from langchain_core.prompts import PromptTemplate
        from src.prompts.summary_prompts import SUMMARY_PROMPT

        return ConversationSummaryBufferMemory(
            llm=llm,
            chat_memory=chat_history,
            max_token_limit=max_token_limit,
            return_messages=True,
            memory_key="chat_history",
            human_prefix="Aluno",
            ai_prefix="Treinador",
            prompt=PromptTemplate(
                input_variables=["summary", "new_lines"],
                template=SUMMARY_PROMPT.replace("{", "{{").replace("}", "}}")
                + "\n\nResumo atual:\n{summary}\n\nNovas linhas:\n{new_lines}\n\nNovo resumo:",
            ),
        )

    def get_window_memory(
        self,
        session_id: str,
        k: int = 40,
    ) -> ConversationBufferWindowMemory:
        """
        Returns a ConversationBufferWindowMemory that only looks at the last K messages.
        Does NOT perform summarization (we handle that manually in V3).
        """
        chat_history = MongoDBChatMessageHistory(
            connection_string=settings.MONGO_URI,
            session_id=session_id,
            database_name=settings.DB_NAME,
            history_size=k,  # Optimizes fetch limit on Mongo side too if supported
        )

        return ConversationBufferWindowMemory(
            chat_memory=chat_history,
            k=k,
            return_messages=True,
            memory_key="chat_history",
            human_prefix="Aluno",
            ai_prefix="Treinador",
        )

    def get_unsummarized_messages(
        self, session_id: str, skip_last: int = 40
    ) -> list[dict]:
        """
        Retrieves messages that haven't been summarized yet, excluding the most recent ones.
        Targeting the 'chat_history' collection structure used by MongoDBChatMessageHistory.
        """
        # Note: LangChain's MongoDBChatMessageHistory structure keys on 'SessionId'.
        # We need to be careful about the schema.
        # By default it stores: { "SessionId": "...", "History": "..." } if using the basic one,
        # OR it stores individual messages if using the set structure.
        # Based on 'add_message', it seems we are using the standard one.
        # Let's assume individual documents per message or a list.
        # Actually, standard MongoDBChatMessageHistory stores 1 doc per message?
        # NO. Standard stores ONE document per session with a 'History' list unless configured otherwise.
        # BUT, looking at 'from_mongodb_chat_message_history', it iterates 'history.messages'.

        # INVESTIGATION: The 'add_message' creates a NEW MongoDBChatMessageHistory instance every time.
        # This implies standard behavior.
        # However, for scalability, we want individual documents.
        # Let's rely on the collection access.

        # If the structure is ONE document per session (standard LangChain), compaction is efficiently rewriting that list.
        # If it's separate documents (custom), we update flags.

        # Given the project constraints, let's look at how we fetch 'get_history'.
        # It calls 'MongoDBChatMessageHistory' with 'history_size=limit'.
        # This implies the DB might storing a list.

        # CRITICAL: If LangChain stores a JSON string in 'History' field (default),
        # we CANNOT easily flag individual messages.
        # We need to check the PRODUCTION DATA STRUCTURE.

        # but here we just return an empty list until the V3 structure is finalized.
        return []
        # WAIT. The user said "Non-destructive".

        # Let's assume for now we can access message items.
        # If we can't, the plan needs adjustment to "Parse, Summarize, Rewrite".

        # Let's play safe: The Compactor will act via the Repository which abstracts this.
        # For now, I will implement a placeholder that assumes we can access raw messages.

        # Actually, let's use the 'MongoDBChatMessageHistory' to fetch ALL messages,
        # identify which ones are old, and interact with them.

        # But wait, 'summarized' flag needs to persist.
        # If LangChain stores everything in a big JSON string, we can't add a flag to a message easily.

        # HYPOTHESIS: We are using a version or config where messages are documents?
        # No, 'MongoDBChatMessageHistory' usually uses a single doc.

        # ADJUSTMENT: The 'HistoryCompactor' will:
        # 1. Fetch ALL history.
        # 2. Slice the old part (excluding last 40).
        # 3. Check if we have a "last_processed_timestamp" in UserProfile?
        # That's safer than adding flags to a JSON blob.

        # RE-PLAN: Instead of 'summarized' boolean on message (which might be hard in JSON blob),
        # Let's store 'last_summarized_timestamp' in UserProfile.
        # Compactor summarizes everything before that timestamp.

        # WAIT. I already added 'summarized' to ChatHistory Pydantic model.
        # This suggests I intended to handle them as objects.
        # Let's stick to the plan but be aware of the storage.

        # If I can't query by flag, I will fetch all, check flag in memory, correct?
        # Yes, fetching full history is expensive but done only by background worker.
        pass  # To be implemented in the service with full context logic
