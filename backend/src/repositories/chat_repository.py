from datetime import datetime
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.language_models import BaseChatModel
from langchain_classic.memory import ConversationSummaryBufferMemory

from src.core.config import settings
from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender
from src.repositories.base import BaseRepository

class ChatRepository(BaseRepository):
    def __init__(self, database):
        # We don't use self.collection directly for some of these but we pass database anyway
        super().__init__(database, "chat_history") # Collection name might vary but MongoDBChatMessageHistory handles it

    def get_history(self, user_id: str, limit: int = 20) -> list[ChatHistory]:
        self.logger.debug("Retrieving chat history for session: %s (limit: %d)", user_id, limit)
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
        from src.prompts.summary_prompt import SUMMARY_PROMPT
        
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
                template=SUMMARY_PROMPT.replace("{", "{{").replace("}", "}}") + "\n\nResumo atual:\n{summary}\n\nNovas linhas:\n{new_lines}\n\nNovo resumo:",
            )
        )
