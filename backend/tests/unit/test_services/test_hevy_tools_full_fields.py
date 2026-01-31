"""
Unit tests for Hevy tools - Full field validation.

Tests all validated fields from POC:
- exercise.notes, rest_seconds, superset_id
- set.type (warmup, normal, dropset, failure)
- rep_range
- UPDATE operations
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.hevy_tools import (
    create_create_hevy_routine_tool,
    create_update_hevy_routine_tool,
)


class TestCreateHevyRoutineFullFields:
    """Test CREATE with all validated fields."""

    @pytest.fixture
    def mock_hevy_service(self):
        service = MagicMock()
        service.create_routine = AsyncMock()
        return service

    @pytest.fixture
    def mock_database(self):
        db = MagicMock()
        profile = MagicMock()
        profile.hevy_enabled = True
        profile.hevy_api_key = "test-key"
        db.get_user_profile.return_value = profile
        return db

    @pytest.mark.asyncio
    async def test_exercise_notes_passed_to_service(
        self, mock_hevy_service, mock_database
    ):
        """Verify exercise.notes are included in create_routine call."""
        # Setup
        mock_routine = MagicMock()
        mock_routine.id = "routine-123"
        mock_routine.title = "Test Routine"
        mock_hevy_service.create_routine.return_value = (mock_routine, None)

        tool = create_create_hevy_routine_tool(
            mock_hevy_service, mock_database, "test@example.com"
        )

        # Execute
        await tool.ainvoke(
            {
                "title": "Test Routine",
                "exercises": [
                    {
                        "exercise_template_id": "ABC123",
                        "notes": "💪 Focus on form",
                        "sets": [{"type": "normal", "weight_kg": 80, "reps": 10}],
                    }
                ],
            }
        )

        # Assert
        mock_hevy_service.create_routine.assert_called_once()
        call_args = mock_hevy_service.create_routine.call_args
        routine_arg = call_args[0][1]  # Second positional arg
        assert routine_arg.exercises[0].notes == "💪 Focus on form"

    @pytest.mark.asyncio
    async def test_rep_range_passed_to_service(self, mock_hevy_service, mock_database):
        """Verify rep_range is preserved in payload."""
        # Setup
        mock_routine = MagicMock()
        mock_routine.id = "routine-123"
        mock_routine.title = "Test Routine"
        mock_hevy_service.create_routine.return_value = (mock_routine, None)

        tool = create_create_hevy_routine_tool(
            mock_hevy_service, mock_database, "test@example.com"
        )

        # Execute
        await tool.ainvoke(
            {
                "title": "Test Routine",
                "exercises": [
                    {
                        "exercise_template_id": "ABC123",
                        "sets": [
                            {
                                "type": "normal",
                                "weight_kg": 80,
                                "rep_range": {"start": 8, "end": 12},
                            }
                        ],
                    }
                ],
            }
        )

        # Assert
        mock_hevy_service.create_routine.assert_called_once()
        call_args = mock_hevy_service.create_routine.call_args
        routine_arg = call_args[0][1]
        set_data = routine_arg.exercises[0].sets[0]
        assert set_data.rep_range is not None
        assert set_data.rep_range.start == 8
        assert set_data.rep_range.end == 12

    @pytest.mark.asyncio
    async def test_rest_seconds_and_superset_passed(
        self, mock_hevy_service, mock_database
    ):
        """Verify rest_seconds and superset_id per exercise."""
        # Setup
        mock_routine = MagicMock()
        mock_routine.id = "routine-123"
        mock_routine.title = "Test Routine"
        mock_hevy_service.create_routine.return_value = (mock_routine, None)

        tool = create_create_hevy_routine_tool(
            mock_hevy_service, mock_database, "test@example.com"
        )

        # Execute
        await tool.ainvoke(
            {
                "title": "Test Routine",
                "exercises": [
                    {
                        "exercise_template_id": "ABC123",
                        "rest_seconds": 90,
                        "superset_id": 1,
                        "sets": [{"type": "normal", "weight_kg": 80, "reps": 10}],
                    },
                    {
                        "exercise_template_id": "DEF456",
                        "superset_id": 1,
                        "sets": [{"type": "normal", "weight_kg": 30, "reps": 12}],
                    },
                ],
            }
        )

        # Assert
        mock_hevy_service.create_routine.assert_called_once()
        call_args = mock_hevy_service.create_routine.call_args
        routine_arg = call_args[0][1]
        assert routine_arg.exercises[0].rest_seconds == 90
        assert routine_arg.exercises[0].superset_id == 1
        assert routine_arg.exercises[1].superset_id == 1

    @pytest.mark.asyncio
    async def test_all_set_types_supported(self, mock_hevy_service, mock_database):
        """Verify warmup, normal, dropset, failure types."""
        # Setup
        mock_routine = MagicMock()
        mock_routine.id = "routine-123"
        mock_routine.title = "Test Routine"
        mock_hevy_service.create_routine.return_value = (mock_routine, None)

        tool = create_create_hevy_routine_tool(
            mock_hevy_service, mock_database, "test@example.com"
        )

        # Execute
        await tool.ainvoke(
            {
                "title": "Test Routine",
                "exercises": [
                    {
                        "exercise_template_id": "ABC123",
                        "sets": [
                            {"type": "warmup", "weight_kg": 40, "reps": 12},
                            {"type": "normal", "weight_kg": 80, "reps": 10},
                            {"type": "dropset", "weight_kg": 60, "reps": 15},
                            {"type": "failure", "weight_kg": 70, "reps": 10},
                        ],
                    }
                ],
            }
        )

        # Assert
        mock_hevy_service.create_routine.assert_called_once()
        call_args = mock_hevy_service.create_routine.call_args
        routine_arg = call_args[0][1]
        sets = routine_arg.exercises[0].sets
        assert sets[0].type == "warmup"
        assert sets[1].type == "normal"
        assert sets[2].type == "dropset"
        assert sets[3].type == "failure"


class TestUpdateHevyRoutineFullFields:
    """Test UPDATE with all validated fields."""

    @pytest.fixture
    def mock_hevy_service(self):
        service = MagicMock()
        service.get_routines = AsyncMock()
        service.get_routine_by_id = AsyncMock()
        service.update_routine = AsyncMock()
        return service

    @pytest.fixture
    def mock_database(self):
        db = MagicMock()
        profile = MagicMock()
        profile.hevy_enabled = True
        profile.hevy_api_key = "test-key"
        db.get_user_profile.return_value = profile
        return db

    @pytest.fixture
    def mock_existing_routine(self):
        """Mock existing routine from Hevy."""
        routine = MagicMock()
        routine.id = "routine-123"
        routine.title = "Existing Routine"
        routine.notes = "Old notes"
        routine.exercises = [
            MagicMock(
                exercise_template_id="ABC123",
                notes="Old exercise notes",
                rest_seconds=60,
                sets=[MagicMock(type="normal", weight_kg=80, reps=10)],
            )
        ]
        return routine

    @pytest.mark.asyncio
    async def test_update_exercise_notes(
        self, mock_hevy_service, mock_database, mock_existing_routine
    ):
        """Verify updating exercise.notes works."""
        # Setup
        mock_response = MagicMock()
        mock_response.routines = [mock_existing_routine]
        mock_response.page_count = 1
        mock_hevy_service.get_routines.return_value = mock_response
        mock_hevy_service.get_routine_by_id.return_value = mock_existing_routine
        mock_hevy_service.update_routine.return_value = mock_existing_routine

        tool = create_update_hevy_routine_tool(
            mock_hevy_service, mock_database, "test@example.com"
        )

        # Execute
        await tool.ainvoke(
            {
                "routine_title": "Existing Routine",
                "exercises": [
                    {
                        "exercise_template_id": "ABC123",
                        "notes": "🔥 NEW notes with emoji",
                        "sets": [{"type": "normal", "weight_kg": 80, "reps": 10}],
                    }
                ],
            }
        )

        # Assert
        mock_hevy_service.update_routine.assert_called_once()
        call_args = mock_hevy_service.update_routine.call_args
        routine_arg = call_args[0][2]  # Third positional arg
        assert routine_arg.exercises[0].notes == "🔥 NEW notes with emoji"

    @pytest.mark.asyncio
    async def test_update_rep_range_and_rest_seconds(
        self, mock_hevy_service, mock_database, mock_existing_routine
    ):
        """Verify updating from fixed reps to rep_range and rest_seconds works."""
        # Setup
        mock_response = MagicMock()
        mock_response.routines = [mock_existing_routine]
        mock_response.page_count = 1
        mock_hevy_service.get_routines.return_value = mock_response
        mock_hevy_service.get_routine_by_id.return_value = mock_existing_routine
        mock_hevy_service.update_routine.return_value = mock_existing_routine

        tool = create_update_hevy_routine_tool(
            mock_hevy_service, mock_database, "test@example.com"
        )

        # Execute
        await tool.ainvoke(
            {
                "routine_title": "Existing Routine",
                "exercises": [
                    {
                        "exercise_template_id": "ABC123",
                        "rest_seconds": 120,
                        "sets": [
                            {
                                "type": "normal",
                                "weight_kg": 80,
                                "rep_range": {"start": 8, "end": 12},
                            }
                        ],
                    }
                ],
            }
        )

        # Assert
        mock_hevy_service.update_routine.assert_called_once()
        call_args = mock_hevy_service.update_routine.call_args
        routine_arg = call_args[0][2]
        assert routine_arg.exercises[0].rest_seconds == 120
        set_data = routine_arg.exercises[0].sets[0]
        assert set_data.rep_range is not None
        assert set_data.rep_range.start == 8
        assert set_data.rep_range.end == 12

    @pytest.mark.asyncio
    async def test_notes_none_preserves_existing(
        self, mock_hevy_service, mock_database, mock_existing_routine
    ):
        """Verify notes=None doesn't overwrite existing notes."""
        # Setup
        mock_response = MagicMock()
        mock_response.routines = [mock_existing_routine]
        mock_response.page_count = 1
        mock_hevy_service.get_routines.return_value = mock_response
        mock_hevy_service.get_routine_by_id.return_value = mock_existing_routine
        mock_hevy_service.update_routine.return_value = mock_existing_routine

        tool = create_update_hevy_routine_tool(
            mock_hevy_service, mock_database, "test@example.com"
        )

        # Execute - update without notes parameter (defaults to None)
        await tool.ainvoke(
            {
                "routine_title": "Existing Routine",
                "new_title": "New Title",
                # notes not provided = None
            }
        )

        # Assert
        mock_hevy_service.update_routine.assert_called_once()
        call_args = mock_hevy_service.update_routine.call_args
        routine_arg = call_args[0][2]
        # Notes should be preserved from existing routine
        assert routine_arg.notes == "Old notes"
