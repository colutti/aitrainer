"""
Repository for scheduled events and future plans.

Handles CRUD operations with date-based filtering to exclude past events
from active queries, ensuring the AI always has current/future context.
"""

from datetime import datetime
from bson import ObjectId
from pymongo.database import Database

from src.api.models.scheduled_event import ScheduledEvent, ScheduledEventWithId
from src.repositories.base import BaseRepository


class EventRepository(BaseRepository):
    """
    Repository for managing scheduled events in MongoDB.

    Methods:
    - save_event: Create new event
    - get_active_events: Retrieve events to inject in prompt (filters past dates)
    - list_all_events: List all events including past ones (for UI/review)
    - delete_event: Remove event by ID
    - update_event: Update event details
    """

    def __init__(self, database: Database):
        """Initialize repository with 'events' collection."""
        super().__init__(database, "events")

    def save_event(self, event: ScheduledEvent) -> str:
        """
        Save a new event to the database.

        Args:
            event: ScheduledEvent model

        Returns:
            str: MongoDB inserted_id as string
        """
        result = self.collection.insert_one(event.model_dump())
        self.logger.info(
            "Event created: %s for user %s",
            event.title,
            event.user_email,
        )
        return str(result.inserted_id)

    def get_active_events(self, user_email: str) -> list[ScheduledEventWithId]:
        """
        Retrieve active events to inject in prompt.

        Filters:
        - user_email matches
        - active = True
        - date IS NULL (no deadline) OR date >= today (future)

        This ensures past events don't clutter the AI context.

        Args:
            user_email: User's email

        Returns:
            List of active events with future/no dates
        """
        today = datetime.now().strftime("%Y-%m-%d")

        query = {
            "user_email": user_email,
            "active": True,
            "$or": [{"date": None}, {"date": {"$gte": today}}],
        }

        cursor = (
            self.collection.find(query)
            .sort("date", 1)  # Sort by date ascending (None first, then future)
        )

        events = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            events.append(ScheduledEventWithId(**doc))

        self.logger.debug(
            "Retrieved %d active events for user: %s", len(events), user_email
        )
        return events

    def list_all_events(self, user_email: str) -> list[ScheduledEventWithId]:
        """
        List all events for a user (including past and inactive).

        Used for UI listing and review. Does not filter by date.

        Args:
            user_email: User's email

        Returns:
            All events (past, future, active, inactive)
        """
        cursor = (
            self.collection.find({"user_email": user_email})
            .sort("date", 1)
        )

        events = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            events.append(ScheduledEventWithId(**doc))

        self.logger.debug(
            "Listed %d total events for user: %s", len(events), user_email
        )
        return events

    def delete_event(self, event_id: str, user_email: str) -> bool:
        """
        Delete event by ID (verifies user ownership).

        Args:
            event_id: MongoDB _id
            user_email: User's email (for authorization)

        Returns:
            True if deleted, False if not found
        """
        result = self.collection.delete_one(
            {"_id": ObjectId(event_id), "user_email": user_email}
        )
        deleted = result.deleted_count > 0

        if deleted:
            self.logger.info(
                "Event deleted: %s for user %s",
                event_id,
                user_email,
            )
        else:
            self.logger.warning(
                "Event delete failed (not found or unauthorized): %s",
                event_id,
            )

        return deleted

    def update_event(
        self, event_id: str, user_email: str, update_data: dict
    ) -> bool:
        """
        Update event fields (title, description, date, recurrence, active).

        Args:
            event_id: MongoDB _id
            user_email: User's email (for authorization)
            update_data: Fields to update

        Returns:
            True if updated, False if not found
        """
        result = self.collection.update_one(
            {"_id": ObjectId(event_id), "user_email": user_email},
            {"$set": update_data},
        )
        updated = result.modified_count > 0

        if updated:
            self.logger.info(
                "Event updated: %s for user %s",
                event_id,
                user_email,
            )
        else:
            self.logger.warning(
                "Event update failed (not found or unauthorized): %s",
                event_id,
            )

        return updated
