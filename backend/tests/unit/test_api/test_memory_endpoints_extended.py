"""
Comprehensive tests for memory management endpoints.
Tests cover memory listing, deletion, and pagination operations.
"""

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pytest
from datetime import datetime, timedelta

from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_ai_trainer_brain, get_qdrant_client
from src.api.models.memory_item import MemoryItem, MemoryListResponse


client = TestClient(app)


# Fixtures
@pytest.fixture
def sample_memory():
    return {
        "id": "mem_001",
        "user_id": "test@example.com",
        "memory": "User prefers morning workouts at 6 AM",
        "created_at": "2024-01-20T10:00:00Z",
        "updated_at": "2024-01-20T10:00:00Z"
    }


@pytest.fixture
def sample_memories():
    """Generate sample memory items."""
    memories = []
    for i in range(5):
        created = datetime.now() - timedelta(days=i)
        memories.append({
            "id": f"mem_{i:03d}",
            "user_id": "test@example.com",
            "memory": f"Memory item {i}",
            "created_at": created.isoformat() + "Z",
            "updated_at": created.isoformat() + "Z"
        })
    return memories


# Test: GET /memory/list - Success Case
def test_list_memories_success(sample_memories):
    """Test retrieving paginated memories."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_qdrant = MagicMock()

    mock_brain.get_memories_paginated.return_value = (sample_memories[:3], 5)

    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
    app.dependency_overrides[get_qdrant_client] = lambda: mock_qdrant

    response = client.get(
        "/memory/list",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["memories"]) == 3
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total_pages"] == 1

    app.dependency_overrides = {}


# Test: GET /memory/list - Multiple Pages
def test_list_memories_pagination():
    """Test memory list pagination."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_qdrant = MagicMock()

    memories = [
        {
            "id": f"mem_{i:03d}",
            "user_id": "test@example.com",
            "memory": f"Memory {i}",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        for i in range(10)
    ]
    mock_brain.get_memories_paginated.return_value = (memories, 35)

    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
    app.dependency_overrides[get_qdrant_client] = lambda: mock_qdrant

    response = client.get(
        "/memory/list?page=2&page_size=10",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert data["total_pages"] == 4

    app.dependency_overrides = {}


# Test: GET /memory/list - Empty Memories
def test_list_memories_empty():
    """Test memory list when user has no memories."""
    app.dependency_overrides[verify_token] = lambda: "newuser@example.com"
    mock_brain = MagicMock()
    mock_qdrant = MagicMock()

    mock_brain.get_memories_paginated.return_value = ([], 0)

    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
    app.dependency_overrides[get_qdrant_client] = lambda: mock_qdrant

    response = client.get(
        "/memory/list",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["memories"] == []
    assert data["total"] == 0

    app.dependency_overrides = {}


# Test: GET /memory/list - Unauthorized
def test_list_memories_unauthorized():
    """Test memory list without authentication."""
    response = client.get("/memory/list")
    assert response.status_code == 403


# Test: GET /memory/list - Database Error
def test_list_memories_database_error():
    """Test memory list with database error."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_qdrant = MagicMock()

    mock_brain.get_memories_paginated.side_effect = Exception("Qdrant Error")

    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
    app.dependency_overrides[get_qdrant_client] = lambda: mock_qdrant

    response = client.get(
        "/memory/list",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 500
    data = response.json()
    assert "Failed to retrieve memories" in data["detail"]

    app.dependency_overrides = {}


# Test: GET /memory/list - Custom Page Size
def test_list_memories_custom_page_size():
    """Test memory list with custom page size."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_qdrant = MagicMock()

    mock_brain.get_memories_paginated.return_value = ([], 0)

    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
    app.dependency_overrides[get_qdrant_client] = lambda: mock_qdrant

    response = client.get(
        "/memory/list?page_size=20",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    call_kwargs = mock_brain.get_memories_paginated.call_args[1]
    assert call_kwargs["page_size"] == 20

    app.dependency_overrides = {}


# Test: DELETE /memory/{memory_id} - Success
def test_delete_memory_success(sample_memory):
    """Test successful memory deletion."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()

    mock_brain.get_memory_by_id.return_value = sample_memory
    mock_brain.delete_memory.return_value = None

    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.delete(
        "/memory/mem_001",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "deleted successfully" in data["message"]
    mock_brain.delete_memory.assert_called_once_with("mem_001")

    app.dependency_overrides = {}


# Test: DELETE /memory/{memory_id} - Not Found
def test_delete_memory_not_found():
    """Test deletion of non-existent memory."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()

    mock_brain.get_memory_by_id.return_value = None

    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.delete(
        "/memory/nonexistent",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 404
    data = response.json()
    assert "Memory not found" in data["detail"]

    app.dependency_overrides = {}


# Test: DELETE /memory/{memory_id} - Unauthorized Owner
def test_delete_memory_unauthorized_owner():
    """Test deleting memory owned by another user."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()

    mock_brain.get_memory_by_id.return_value = {
        "id": "mem_001",
        "user_id": "other@example.com"
    }

    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.delete(
        "/memory/mem_001",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 403
    data = response.json()
    assert "Not authorized" in data["detail"]

    app.dependency_overrides = {}


# Test: DELETE /memory/{memory_id} - Unauthorized (No Token)
def test_delete_memory_unauthorized():
    """Test deletion without authentication."""
    response = client.delete("/memory/mem_001")
    assert response.status_code == 403


# Test: DELETE /memory/{memory_id} - Database Error
def test_delete_memory_database_error():
    """Test deletion when database error occurs."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()

    mock_brain.get_memory_by_id.return_value = {
        "id": "mem_001",
        "user_id": "test@example.com"
    }
    mock_brain.delete_memory.side_effect = Exception("Deletion failed")

    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.delete(
        "/memory/mem_001",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 500
    data = response.json()
    assert "Failed to delete memory" in data["detail"]

    app.dependency_overrides = {}


# Test: GET /memory/list - Invalid Page Parameter
def test_list_memories_invalid_page():
    """Test memory list with invalid page parameter."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_qdrant = MagicMock()

    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
    app.dependency_overrides[get_qdrant_client] = lambda: mock_qdrant

    # Page 0 (should be minimum 1)
    response = client.get(
        "/memory/list?page=0",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 422

    app.dependency_overrides = {}


# Test: GET /memory/list - Excessive Page Size
def test_list_memories_excessive_page_size():
    """Test memory list with page size exceeding maximum."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_qdrant = MagicMock()

    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
    app.dependency_overrides[get_qdrant_client] = lambda: mock_qdrant

    # page_size exceeds maximum (51 > 50)
    response = client.get(
        "/memory/list?page_size=51",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 422

    app.dependency_overrides = {}


# Test: GET /memory/list - Large Number of Memories
def test_list_memories_large_collection():
    """Test memory list with large memory collection."""
    app.dependency_overrides[verify_token] = lambda: "veteran@example.com"
    mock_brain = MagicMock()
    mock_qdrant = MagicMock()

    memories = [
        {
            "id": f"mem_{i:06d}",
            "user_id": "veteran@example.com",
            "memory": f"Memory {i}",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        for i in range(10)
    ]
    mock_brain.get_memories_paginated.return_value = (memories, 5000)

    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
    app.dependency_overrides[get_qdrant_client] = lambda: mock_qdrant

    response = client.get(
        "/memory/list?page=100&page_size=10",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5000
    assert data["total_pages"] == 500

    app.dependency_overrides = {}
