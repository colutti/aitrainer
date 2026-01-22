from pydantic import BaseModel
from src.api.models.sender import Sender
from datetime import datetime, MINYEAR


class ChatHistory(BaseModel):
    """
    Represents a single chat message in the history between the user and the AI trainer.

    Attributes:
        text (str): The content of the message.
        sender (Sender): The sender of the message (Student or Trainer).
        timestamp (str): ISO formatted timestamp of when the message was sent.
    """

    text: str
    sender: Sender
    timestamp: str  # ISO formatted timestamp
    trainer_type: str | None = None  # Track which trainer was active
    summarized: bool = (
        False  # Track if this message has been included in long-term summary
    )

    def _get_clean_text(self) -> str:
        """
        Returns the chat message text, removing control characters and
        formatting the text to be readable on a single line.
        """
        return " ".join(self.text.split())

    def _get_formatted_timestamp(self) -> str:
        """
        Returns the timestamp formatted as DD/MM/YYYY HH:MM.
        Falls back to the raw timestamp if parsing fails.
        """
        try:
            dt = datetime.fromisoformat(self.timestamp)
            return dt.strftime("%d/%m/%Y %H:%M")
        except (ValueError, TypeError):
            return self.timestamp

    def _get_sender_label(self) -> str:
        """
        Returns a readable sender label with emoji.
        """
        if self.sender == Sender.STUDENT:
            return "🧑 Aluno"
        if self.sender == Sender.SYSTEM:
            return "⚙️ Sistema"
        return "🏋️ Treinador"

    def __str__(self) -> str:
        """
        Returns a readable representation of the chat message.
        """
        return (
            f"**{self._get_sender_label()}** ({self._get_formatted_timestamp()}):\n"
            f"> {self._get_clean_text()}"
        )

    @staticmethod
    def from_mongodb_chat_message_history(history) -> list["ChatHistory"]:
        """
        Converts a MongoDB chat message history object into a list of ChatHistory instances.

        Args:
            history: An object containing a list of messages,
                each with content, type, and additional_kwargs.

        Returns:
            list[ChatHistory]: A list of ChatHistory objects constructed
                from the provided message history.
        """
        chat_history = []
        for msg in history.messages:
            if msg.type == "human":
                sender = Sender.STUDENT
            elif msg.type == "system":
                sender = Sender.SYSTEM
            else:
                sender = Sender.TRAINER

            chat_history.append(
                ChatHistory(
                    text=msg.content,
                    sender=sender,
                    timestamp=msg.additional_kwargs.get(
                        "timestamp", datetime(MINYEAR, 1, 1).isoformat()
                    ),
                    trainer_type=msg.additional_kwargs.get("trainer_type"),
                )
            )
        # order the results by timestamp
        chat_history.sort(key=lambda x: x.timestamp)

        return chat_history

    @staticmethod
    def to_string_list(chat_history: list["ChatHistory"]) -> list[str]:
        """
        Converts a list of ChatHistory objects into a list of strings that
        represents the conversation history in a readable format.

        Args:
            chat_history: List of ChatHistory objects.

        Returns:
            list[str]: List of formatted strings, one for each message.
        """
        return [str(msg) for msg in chat_history]

    @staticmethod
    def format_as_string(
        chat_history: list["ChatHistory"],
        empty_message: str = "Nenhuma mensagem anterior.",
    ) -> str:
        """
        Formats a list of ChatHistory into a single string with visual separators.

        Args:
            chat_history: List of ChatHistory objects.
            empty_message: Message to be returned if the list is empty.

        Returns:
            str: Formatted string with all messages, or the empty list message.
        """
        if not chat_history:
            return empty_message
        return "\n\n---\n\n".join(ChatHistory.to_string_list(chat_history))

    @staticmethod
    def format_with_trainer_context(
        chat_history: list["ChatHistory"],
        current_trainer_type: str,
        empty_message: str = "Nenhuma mensagem anterior.",
    ) -> str:
        """
        Formats history with specific handling for previous trainers.
        """
        if not chat_history:
            return empty_message

        formatted = []
        for msg in chat_history:
            if msg.sender == Sender.STUDENT:
                # User messages: always as-is
                formatted.append(str(msg))
            elif msg.trainer_type == current_trainer_type:
                # Current trainer: as-is
                formatted.append(str(msg))
            else:
                # Previous trainer: neutralize
                trainer_name = msg.trainer_type or "Desconhecido"
                clean_text = msg._get_clean_text()
                formatted.append(
                    f"**🏋️ Treinador [PERFIL ANTERIOR: {trainer_name}]** ({msg._get_formatted_timestamp()}):\n"
                    f"> [Contexto] {clean_text}"
                )

        return "\n\n---\n\n".join(formatted)
