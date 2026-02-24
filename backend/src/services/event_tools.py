"""
LangChain tools for managing scheduled events and future plans.

The AI can create, list, update, and delete events via conversation.
Events are injected into the prompt context to guide coaching decisions.
"""

from datetime import datetime
from langchain_core.tools import tool
from pymongo.database import Database

from src.repositories.event_repository import EventRepository
from src.core.logs import logger


def _validate_date_format(date: str | None) -> str | None:
    """Validate YYYY-MM-DD format, return error string if invalid."""
    if date is None:
        return None
    try:
        datetime.strptime(date, "%Y-%m-%d")
        return None
    except ValueError:
        return f"❌ Data inválida: '{date}'. Use o formato YYYY-MM-DD (ex: '2025-12-01')"


def create_create_event_tool(database: Database, user_email: str):
    """
    Factory function to create a create_event tool with injected dependencies.

    Args:
        database: MongoDB database connection
        user_email: User's email for ownership

    Returns:
        Callable tool for creating events
    """
    repo = EventRepository(database)

    @tool
    def create_event(
        title: str,
        description: str | None = None,
        date: str | None = None,
        recurrence: str = "none",
    ) -> str:
        """
        Cria um novo evento, plano ou meta para o aluno.

        Argumentos:
        - title: Título do evento (ex: "Emagrecer para o verão")
        - description: Detalhes adicionais (opcional)
        - date: Data alvo em YYYY-MM-DD (opcional - se None, é meta sem prazo)
        - recurrence: "none" | "weekly" | "monthly" (padrão: "none")

        Exemplos:
        - create_event(title="Emagrecer para o verão", date="2025-12-01")
        - create_event(title="Check-in de peso", recurrence="weekly")
        - create_event(title="Aumentar consumo de proteína")

        Retorna: String com confirmação e ID do evento
        """
        from src.api.models.scheduled_event import ScheduledEvent

        try:
            event = ScheduledEvent(
                user_email=user_email,
                title=title,
                description=description,
                date=date,
                recurrence=recurrence,
                active=True,
                created_at=datetime.now().isoformat(),
            )

            event_id = repo.save_event(event)
            logger.info("Event created: %s (ID: %s) for user %s", title, event_id, user_email)

            return (
                f"✅ Evento criado com sucesso!\n"
                f"📌 **{title}**\n"
                f"{'📅 Data: ' + date if date else '📅 Sem prazo'}\n"
                f"🔄 Recorrência: {recurrence}\n"
                f"ID: {event_id}"
            )
        except Exception as e:
            logger.error("Error creating event: %s", e)
            return f"❌ Erro ao criar evento: {str(e)}"

    return create_event


def create_list_events_tool(database: Database, user_email: str):
    """
    Factory function to create a list_events tool with injected dependencies.

    Args:
        database: MongoDB database connection
        user_email: User's email for ownership

    Returns:
        Callable tool for listing events
    """
    repo = EventRepository(database)

    @tool
    def list_events() -> str:
        """
        Lista todos os eventos, planos e metas ativas do aluno.

        Retorna: String formatada com lista de eventos
        """
        try:
            events = repo.get_active_events(user_email)

            if not events:
                return (
                    "📋 Você não tem eventos ativos no momento.\n"
                    "Use create_event() para adicionar metas e planos."
                )

            lines = ["📋 **Seus eventos e planos:**\n"]
            for event in events:
                date_str = f"📅 {event.date}" if event.date else "📅 Sem prazo"
                recur_str = f" | 🔄 {event.recurrence}" if event.recurrence != "none" else ""
                desc_str = f"\n   {event.description}" if event.description else ""

                lines.append(f"- **{event.title}** ({event.id})\n  {date_str}{recur_str}{desc_str}")

            return "\n".join(lines)
        except Exception as e:
            logger.error("Error listing events: %s", e)
            return f"❌ Erro ao listar eventos: {str(e)}"

    return list_events


def create_delete_event_tool(database: Database, user_email: str):
    """
    Factory function to create a delete_event tool with injected dependencies.

    Args:
        database: MongoDB database connection
        user_email: User's email for authorization

    Returns:
        Callable tool for deleting events
    """
    repo = EventRepository(database)

    @tool
    def delete_event(event_id: str) -> str:
        """
        Deleta um evento, plano ou meta.

        Argumentos:
        - event_id: ID do evento a deletar (ver com list_events)

        Retorna: String com confirmação ou erro
        """
        try:
            success = repo.delete_event(event_id, user_email)

            if success:
                logger.info("Event deleted: %s for user %s", event_id, user_email)
                return f"✅ Evento removido com sucesso! (ID: {event_id})"
            else:
                return (
                    f"❌ Evento não encontrado ou não autorizado (ID: {event_id})\n"
                    "Use list_events() para ver seus eventos."
                )
        except Exception as e:
            logger.error("Error deleting event: %s", e)
            return f"❌ Erro ao deletar evento: {str(e)}"

    return delete_event


def create_update_event_tool(database: Database, user_email: str):
    """
    Factory function to create an update_event tool with injected dependencies.

    Args:
        database: MongoDB database connection
        user_email: User's email for authorization

    Returns:
        Callable tool for updating events
    """
    repo = EventRepository(database)

    @tool
    def update_event(
        event_id: str,
        title: str | None = None,
        description: str | None = None,
        date: str | None = None,
        recurrence: str | None = None,
        clear_date: bool = False,
    ) -> str:
        """
        Atualiza um evento, plano ou meta existente.

        Argumentos:
        - event_id: ID do evento (ver com list_events)
        - title: Novo título (opcional)
        - description: Nova descrição (opcional)
        - date: Nova data em YYYY-MM-DD (opcional)
        - recurrence: Nova recorrência (opcional)
        - clear_date: True para remover o prazo (tornar meta sem data)

        Retorna: String com confirmação ou erro
        """
        try:
            update_data = {}
            if title is not None:
                update_data["title"] = title
            if description is not None:
                update_data["description"] = description
            if clear_date:
                update_data["date"] = None
            elif date is not None:
                date_err = _validate_date_format(date)
                if date_err:
                    return date_err
                update_data["date"] = date
            if recurrence is not None:
                update_data["recurrence"] = recurrence

            if not update_data:
                return "⚠️ Nenhum campo para atualizar. Especifique title, description, date ou recurrence."

            success = repo.update_event(event_id, user_email, update_data)

            if success:
                logger.info("Event updated: %s for user %s", event_id, user_email)
                return f"✅ Evento atualizado com sucesso! (ID: {event_id})"
            else:
                return (
                    f"❌ Evento não encontrado ou não autorizado (ID: {event_id})\n"
                    "Use list_events() para ver seus eventos."
                )
        except Exception as e:
            logger.error("Error updating event: %s", e)
            return f"❌ Erro ao atualizar evento: {str(e)}"

    return update_event
