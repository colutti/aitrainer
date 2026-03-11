"""
Model for scheduled events and future plans.

Allows users to create reminders, goals with deadlines, and recurring events.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScheduledEvent(BaseModel):
    """
    A scheduled event, plan, or goal with optional date and recurrence.

    Examples:
    - "Emagrecer para o verão" com date="2025-12-01"
    - "Check-in de peso" com recurrence="weekly"
    - "Aumentar consumo de proteína" sem date (open-ended goal)
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_email": "user@example.com",
                "title": "Emagrecer para o verão",
                "description": "Meta de -8kg antes de 01/12",
                "date": "2025-12-01",
                "recurrence": "none",
                "active": True,
                "created_at": "2025-02-24T10:30:00",
            }
        }
    )

    user_email: str = Field(..., description="User who owns this event")
    title: str = Field(..., max_length=200, description="Event title")
    description: str | None = Field(
        default=None, max_length=1000, description="Additional details"
    )
    date: str | None = Field(
        default=None,
        description="Target date in YYYY-MM-DD format, or None if no deadline",
    )
    recurrence: str = Field(
        default="none",
        pattern="^(none|weekly|monthly)$",
        description="Recurrence: none, weekly, or monthly",
    )
    active: bool = Field(default=True, description="Whether this event is active")
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO timestamp when created",
    )

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        """Validate that date is in YYYY-MM-DD format when provided."""
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(
                f"Date must be in YYYY-MM-DD format (e.g. '2025-12-01'), got '{v}'"
            ) from e
        return v


class ScheduledEventWithId(ScheduledEvent):
    """ScheduledEvent with MongoDB _id."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id", description="MongoDB document ID")
