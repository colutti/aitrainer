from .config import settings
from .logs import logger
from .models import ChatHistory, Sender
from factory import get_mem0_client


class RelevantMemory:
    def retrieve_relevant_memories(
        self, message: str, user_id: str
    ) -> list[ChatHistory]:
        """
        Retrieve and format the most relevant memories for a given user and message.

        This method searches for up to X relevant memory entries associated with the specified user and message.
        The results are formatted as a list of ChatHistory objects.

        Args:
            message (str): The input message to search relevant memories for.
            user_id (str): The unique identifier of the user whose memories are being retrieved.

        Returns:
            list[ChatHistory]: A list of ChatHistory objects containing up to X relevant memories.
        """
        logger.debug("Retrieving relevant memories for user: %s", user_id)
        memory = get_mem0_client()
        relevant_memories = memory.search(
            query=message, user_id=user_id, limit=settings.MAX_LONG_TERM_MEMORY_MESSAGES
        )
        logger.debug(
            "Total relevant memories retrieved: %d", len(relevant_memories["results"])
        )
        memories_chat_history_list = [
            ChatHistory(
                text=entry["memory"],
                sender=Sender(entry["metadata"].get("sender", "Trainer")),
                timestamp=entry["timestamp"],
            )
            for entry in relevant_memories["results"]
        ]
        return memories_chat_history_list

    def store_memory(self, message: str, user_id: str, sender: Sender):
        """
        Store a new memory entry for a given user.

        This method adds a new memory entry associated with the specified user and message.
        The sender indicates who is adding the memory (Sender.STUDENT ou Sender.TRAINER).

        Args:
            message (str): The memory content to be stored.
            user_id (str): The unique identifier of the user for whom the memory is being stored.
            sender (Sender): O remetente da memória (Sender.STUDENT ou Sender.TRAINER).
        """
        logger.debug("Storing new memory for user: %s", user_id)
        memory = get_mem0_client()
        memory.add(
            messages=message,
            user_id=user_id,
            metadata={"sender": sender.value},
        )
        logger.debug("Memory stored successfully for user: %s", user_id)
