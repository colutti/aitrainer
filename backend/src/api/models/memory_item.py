"""
This module contains the Pydantic models for memory operations.
"""

from datetime import datetime
from pydantic import BaseModel


class MemoryItem(BaseModel):
    """Represents a single memory item from Mem0."""

    id: str
    memory: str
    translations: dict[str, str] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class MemoryListResponse(BaseModel):
    """Response model for the paginated memory list endpoint."""

    memories: list[MemoryItem]
    total: int
    page: int
    page_size: int
    total_pages: int
