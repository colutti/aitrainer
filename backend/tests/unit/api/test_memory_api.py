"""
Unit tests for the memory API endpoints.
"""

import unittest
from unittest.mock import MagicMock
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_ai_trainer_brain, get_qdrant_client

def mock_unauthenticated_user():
    """Raises HTTPException for unauthenticated user."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
    )

class TestMemoryApi(unittest.TestCase):
    """
    Tests for the memory management API endpoints.
    """

    def setUp(self):
        """
        Set up the test client before each test.
        """
        self.client = TestClient(app)

    def tearDown(self):
        """
        Clean up dependency overrides after each test.
        """
        app.dependency_overrides = {}

    def _setup_pagination_mock(self, memories: list, total: int):
        """Helper to set up pagination mock with brain returning the expected data."""
        mock_brain = MagicMock()
        mock_brain.get_memories_paginated.return_value = (memories, total)
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        # Mock Qdrant client (not directly used since brain is mocked)
        mock_qdrant = MagicMock()
        app.dependency_overrides[get_qdrant_client] = lambda: mock_qdrant

        return mock_brain

    def test_list_memories_success(self):
        """
        Test successful retrieval of first page of memories.
        """
        # Arrange
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        memories = [
            {
                "id": "mem_123",
                "memory": "User prefers morning workouts",
                "created_at": "2026-01-03T08:00:00Z",
                "updated_at": None,
            },
            {
                "id": "mem_456",
                "memory": "User has left knee problem",
                "created_at": "2026-01-02T10:30:00Z",
                "updated_at": None,
            },
        ]
        mock_brain = self._setup_pagination_mock(memories, total=25)

        # Act
        response = self.client.get(
            "/memory/list?page=1&page_size=10",
            headers={"Authorization": "Bearer test_token"},
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["memories"]), 2)
        self.assertEqual(data["total"], 25)
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["page_size"], 10)
        self.assertEqual(data["total_pages"], 3)
        self.assertEqual(data["memories"][0]["memory"], "User prefers morning workouts")
        mock_brain.get_memories_paginated.assert_called_once()

    def test_list_memories_pagination(self):
        """
        Test retrieval of middle page of memories.
        """
        # Arrange
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        memories = [
            {
                "id": "mem_789",
                "memory": "User completed 10 workouts this month",
                "created_at": "2026-01-01T08:00:00Z",
                "updated_at": None,
            }
        ]
        self._setup_pagination_mock(memories, total=25)

        # Act
        response = self.client.get(
            "/memory/list?page=2&page_size=10",
            headers={"Authorization": "Bearer test_token"},
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["page"], 2)
        self.assertEqual(data["total"], 25)
        self.assertEqual(data["total_pages"], 3)

    def test_list_memories_empty(self):
        """
        Test retrieval of memories when user has no memories.
        """
        # Arrange
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        self._setup_pagination_mock([], total=0)

        # Act
        response = self.client.get(
            "/memory/list", headers={"Authorization": "Bearer test_token"}
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["memories"]), 0)
        self.assertEqual(data["total"], 0)
        self.assertEqual(data["total_pages"], 0)

    def test_list_memories_unauthorized(self):
        """
        Test retrieval of memories without authentication.
        """
        # Arrange
        app.dependency_overrides[verify_token] = mock_unauthenticated_user

        # Act
        response = self.client.get("/memory/list")

        # Assert
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Not authenticated"})

    def test_list_memories_database_error(self):
        """Test memory list with database error."""
        app.dependency_overrides[verify_token] = lambda: "test@example.com"
        mock_brain = MagicMock()
        mock_brain.get_memories_paginated.side_effect = Exception("Qdrant Error")
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        response = self.client.get(
            "/memory/list",
            headers={"Authorization": "Bearer test_token"}
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn("Failed to retrieve memories", response.json()["detail"])

    def test_list_memories_invalid_params(self):
        """Test memory list with invalid parameters."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        
        # Invalid page (0)
        response = self.client.get(
            "/memory/list?page=0",
            headers={"Authorization": "Bearer test_token"}
        )
        self.assertEqual(response.status_code, 422)

        # Excessive page size (51)
        response = self.client.get(
            "/memory/list?page_size=51",
            headers={"Authorization": "Bearer test_token"}
        )
        self.assertEqual(response.status_code, 422)

    def test_delete_memory_success(self):
        """
        Test successful deletion of a memory.
        """
        # Arrange
        user_email = "test@test.com"
        app.dependency_overrides[verify_token] = lambda: user_email
        mock_brain = MagicMock()
        mock_brain.get_memory_by_id.return_value = {
            "id": "mem_123",
            "user_id": user_email,
        }
        mock_brain.delete_memory.return_value = True
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        # Act
        response = self.client.delete(
            "/memory/mem_123", headers={"Authorization": "Bearer test_token"}
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Memory deleted successfully"})
        mock_brain.get_memory_by_id.assert_called_once_with("mem_123", user_email)
        mock_brain.delete_memory.assert_called_once_with("mem_123", user_email)

    def test_delete_memory_not_owner(self):
        """
        Test deletion of memory belonging to another user returns 403.
        """
        # Arrange
        user_email = "test@test.com"
        app.dependency_overrides[verify_token] = lambda: user_email
        mock_brain = MagicMock()
        mock_brain.get_memory_by_id.return_value = {
            "id": "mem_123",
            "user_id": "other@test.com",
        }
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        # Act
        response = self.client.delete(
            "/memory/mem_123", headers={"Authorization": "Bearer test_token"}
        )

        # Assert
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(), {"detail": "Not authorized to delete this memory"}
        )
        mock_brain.get_memory_by_id.assert_called_once_with("mem_123", user_email)

    def test_delete_memory_not_found(self):
        """
        Test deletion of non-existent memory returns 404.
        """
        # Arrange
        user_email = "test@test.com"
        app.dependency_overrides[verify_token] = lambda: user_email
        mock_brain = MagicMock()
        mock_brain.get_memory_by_id.return_value = None
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        # Act
        response = self.client.delete(
            "/memory/mem_xxx", headers={"Authorization": "Bearer test_token"}
        )

        # Assert
        self.assertEqual(response.status_code, 404)
        mock_brain.get_memory_by_id.assert_called_once_with("mem_xxx", user_email)

    def test_delete_memory_failure(self):
        """
        Test deletion of memory when delete operation fails.
        """
        # Arrange
        user_email = "test@test.com"
        app.dependency_overrides[verify_token] = lambda: user_email
        mock_brain = MagicMock()
        mock_brain.get_memory_by_id.return_value = {
            "id": "mem_123",
            "user_id": user_email,
        }
        mock_brain.delete_memory.side_effect = Exception("Qdrant error")
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        # Act
        response = self.client.delete(
            "/memory/mem_123", headers={"Authorization": "Bearer test_token"}
        )

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "Failed to delete memory"})
        mock_brain.get_memory_by_id.assert_called_once_with("mem_123", user_email)
        mock_brain.delete_memory.assert_called_once_with("mem_123", user_email)

if __name__ == "__main__":
    unittest.main()
