from pydantic import BaseModel


class ImportResult(BaseModel):
    """Result summary of a bulk data import."""

    created: int
    updated: int
    errors: int
    total_days: int
    error_messages: list[str] = []
