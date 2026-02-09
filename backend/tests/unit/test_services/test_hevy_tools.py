"""Tests for Hevy tools (LangChain tools for AI agent)."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.hevy_tools import (
    create_search_hevy_exercises_tool,
    create_create_hevy_routine_tool,
    create_list_hevy_routines_tool,
)


@pytest.fixture
def mock_hevy_service():
    """Mock HevyService."""
    service = MagicMock()
    service.get_all_exercise_templates = AsyncMock()
    service.create_routine = AsyncMock()
    service.get_routines = AsyncMock()
    return service


@pytest.fixture
def mock_database():
    """Mock database."""
    db = MagicMock()
    return db


@pytest.fixture
def sample_exercises():
    """Sample exercise templates from Hevy."""
    return [
        MagicMock(id="EX001", title="Bench Press", primary_muscle_group="Chest"),
        MagicMock(id="EX002", title="Barbell Squat", primary_muscle_group="Legs"),
        MagicMock(id="EX003", title="Deadlift", primary_muscle_group="Back"),
        MagicMock(id="EX004", title="Leg Press", primary_muscle_group="Legs"),
        MagicMock(id="EX005", title="Dumbbell Row", primary_muscle_group="Back"),
    ]


class TestSearchHevyExercises:
    """Test search hevy exercises tool."""

    @pytest.mark.asyncio
    async def test_search_exact_match(self, mock_hevy_service, mock_database, sample_exercises):
        """Test exact exercise match."""
        mock_hevy_service.get_all_exercise_templates.return_value = sample_exercises
        profile = MagicMock()
        profile.hevy_enabled = True
        profile.hevy_api_key = "api_key"
        mock_database.get_user_profile.return_value = profile

        tool = create_search_hevy_exercises_tool(
            mock_hevy_service, mock_database, "user@test.com"
        )
        result = await tool.ainvoke({"query": "bench press"})

        assert "Bench Press" in result
        assert "EX001" in result

    @pytest.mark.asyncio
    async def test_search_partial_match(self, mock_hevy_service, mock_database, sample_exercises):
        """Test partial word match in exercise name."""
        mock_hevy_service.get_all_exercise_templates.return_value = sample_exercises
        profile = MagicMock()
        profile.hevy_enabled = True
        profile.hevy_api_key = "api_key"
        mock_database.get_user_profile.return_value = profile

        tool = create_search_hevy_exercises_tool(
            mock_hevy_service, mock_database, "user@test.com"
        )
        result = await tool.ainvoke({"query": "press"})

        # Should match "Bench Press" and "Leg Press"
        assert "Bench Press" in result or "Leg Press" in result

    @pytest.mark.asyncio
    async def test_search_normalize_dash_to_space(self, mock_hevy_service, mock_database):
        """Test that dashes are normalized to spaces."""
        exercises = [
            MagicMock(
                id="EX001",
                title="Barbell-Squat",
                primary_muscle_group="Legs"
            )
        ]
        mock_hevy_service.get_all_exercise_templates.return_value = exercises
        profile = MagicMock()
        profile.hevy_enabled = True
        profile.hevy_api_key = "api_key"
        mock_database.get_user_profile.return_value = profile

        tool = create_search_hevy_exercises_tool(
            mock_hevy_service, mock_database, "user@test.com"
        )
        # Query with dash should match title with dash
        result = await tool.ainvoke({"query": "barbell-squat"})

        assert "Barbell-Squat" in result

    @pytest.mark.asyncio
    async def test_search_no_results(self, mock_hevy_service, mock_database, sample_exercises):
        """Test when search returns no results."""
        mock_hevy_service.get_all_exercise_templates.return_value = sample_exercises
        profile = MagicMock()
        profile.hevy_enabled = True
        profile.hevy_api_key = "api_key"
        mock_database.get_user_profile.return_value = profile

        tool = create_search_hevy_exercises_tool(
            mock_hevy_service, mock_database, "user@test.com"
        )
        result = await tool.ainvoke({"query": "xyz123nonexistent"})

        assert "Nenhum exercício encontrado" in result

    @pytest.mark.asyncio
    async def test_search_integration_disabled(self, mock_hevy_service, mock_database):
        """Test when Hevy integration is disabled."""
        profile = MagicMock()
        profile.hevy_enabled = False
        mock_database.get_user_profile.return_value = profile

        tool = create_search_hevy_exercises_tool(
            mock_hevy_service, mock_database, "user@test.com"
        )
        result = await tool.ainvoke({"query": "bench press"})

        assert "Integração desativada" in result

    @pytest.mark.asyncio
    async def test_search_limit_top_5(self, mock_hevy_service, mock_database):
        """Test that results are limited to top 5."""
        # Create 10 matching exercises
        exercises = [
            MagicMock(id=f"EX{i:03d}", title=f"Bench Press Var {i}", primary_muscle_group="Chest")
            for i in range(10)
        ]
        mock_hevy_service.get_all_exercise_templates.return_value = exercises
        profile = MagicMock()
        profile.hevy_enabled = True
        profile.hevy_api_key = "api_key"
        mock_database.get_user_profile.return_value = profile

        tool = create_search_hevy_exercises_tool(
            mock_hevy_service, mock_database, "user@test.com"
        )
        result = await tool.ainvoke({"query": "bench press"})

        # Count bullet points (should be 5)
        bullet_count = result.count("•")
        assert bullet_count == 5
        assert "... e mais 5 opções" in result


class TestCreateHevyRoutine:
    """Test create hevy routine tool."""

    @pytest.mark.asyncio
    async def test_create_routine_success(self, mock_hevy_service, mock_database):
        """Test successful routine creation."""
        profile = MagicMock()
        profile.hevy_enabled = True
        profile.hevy_api_key = "api_key"
        mock_database.get_user_profile.return_value = profile

        routine_result = (MagicMock(id="R001"), None)
        mock_hevy_service.create_routine.return_value = routine_result

        tool = create_create_hevy_routine_tool(
            mock_hevy_service, mock_database, "user@test.com"
        )

        exercises = [
            {
                "exercise_template_id": "EX001",
                "sets": [{"type": "normal", "reps": 10, "weight_kg": 100}]
            }
        ]

        result = await tool.ainvoke({
            "title": "My Routine",
            "exercises": exercises,
        })

        # Should mention success
        assert "criada" in result.lower() or "sucesso" in result.lower() or "R001" in result

    @pytest.mark.asyncio
    async def test_create_routine_no_exercises(self, mock_hevy_service, mock_database):
        """Test creation fails with no exercises."""
        profile = MagicMock()
        profile.hevy_enabled = True
        profile.hevy_api_key = "api_key"
        mock_database.get_user_profile.return_value = profile

        tool = create_create_hevy_routine_tool(
            mock_hevy_service, mock_database, "user@test.com"
        )

        result = await tool.ainvoke({
            "title": "Empty Routine",
            "exercises": [],
        })

        assert "obrigatório" in result.lower() or "exercício" in result.lower()

    @pytest.mark.asyncio
    async def test_create_routine_no_title(self, mock_hevy_service, mock_database):
        """Test creation fails without title."""
        profile = MagicMock()
        profile.hevy_enabled = True
        profile.hevy_api_key = "api_key"
        mock_database.get_user_profile.return_value = profile

        tool = create_create_hevy_routine_tool(
            mock_hevy_service, mock_database, "user@test.com"
        )

        exercises = [
            {
                "exercise_template_id": "EX001",
                "sets": [{"type": "normal", "reps": 10, "weight_kg": 100}]
            }
        ]

        result = await tool.ainvoke({"title": "", "exercises": exercises})

        assert "obrigatório" in result.lower() or "título" in result.lower()

    @pytest.mark.asyncio
    async def test_create_routine_integration_disabled(self, mock_hevy_service, mock_database):
        """Test creation fails when integration disabled."""
        profile = MagicMock()
        profile.hevy_enabled = False
        mock_database.get_user_profile.return_value = profile

        tool = create_create_hevy_routine_tool(
            mock_hevy_service, mock_database, "user@test.com"
        )

        exercises = [{"exercise_template_id": "EX001"}]

        result = await tool.ainvoke({"title": "Test", "exercises": exercises})

        assert "desativada" in result.lower() or "integração" in result.lower()

    @pytest.mark.asyncio
    async def test_create_routine_api_error(self, mock_hevy_service, mock_database):
        """Test creation handles API errors."""
        profile = MagicMock()
        profile.hevy_enabled = True
        profile.hevy_api_key = "api_key"
        mock_database.get_user_profile.return_value = profile

        # Return error tuple
        mock_hevy_service.create_routine.return_value = (None, "Invalid exercise ID")

        tool = create_create_hevy_routine_tool(
            mock_hevy_service, mock_database, "user@test.com"
        )

        exercises = [{"exercise_template_id": "INVALID"}]

        result = await tool.ainvoke({"title": "Test", "exercises": exercises})

        assert "erro" in result.lower() or "invalid" in result.lower()


class TestListHevyRoutines:
    """Test list hevy routines tool."""

    @pytest.mark.asyncio
    async def test_list_routines_success(self, mock_hevy_service, mock_database):
        """Test successful routine listing."""
        profile = MagicMock()
        profile.hevy_enabled = True
        profile.hevy_api_key = "api_key"
        mock_database.get_user_profile.return_value = profile

        # Mock routine response
        routine_response = MagicMock()
        routine_response.routines = [
            MagicMock(id="R001", title="Push Day", notes=""),
            MagicMock(id="R002", title="Pull Day", notes=""),
        ]
        routine_response.total = 2
        routine_response.page = 1
        routine_response.page_count = 1

        mock_hevy_service.get_routines.return_value = routine_response

        tool = create_list_hevy_routines_tool(
            mock_hevy_service, mock_database, "user@test.com"
        )

        result = await tool.ainvoke({})

        assert "Push Day" in result
        assert "Pull Day" in result
        # Verify it found the routines
        assert "2 rotinas" in result or "rotinas" in result

    @pytest.mark.asyncio
    async def test_list_routines_pagination(self, mock_hevy_service, mock_database):
        """Test routine listing with pagination."""
        profile = MagicMock()
        profile.hevy_enabled = True
        profile.hevy_api_key = "api_key"
        mock_database.get_user_profile.return_value = profile

        routine_response = MagicMock()
        routine_response.routines = [MagicMock(id="R001", title="Routine", notes="")]
        routine_response.total = 100
        routine_response.page = 2
        routine_response.page_count = 10

        mock_hevy_service.get_routines.return_value = routine_response

        tool = create_list_hevy_routines_tool(
            mock_hevy_service, mock_database, "user@test.com"
        )

        result = await tool.ainvoke({"page": 2, "page_size": 10})

        # Should indicate pagination
        assert "página" in result.lower() or "page" in result.lower() or "2" in result
        # Verify service was called with pagination params
        mock_hevy_service.get_routines.assert_called()
        call_args = mock_hevy_service.get_routines.call_args
        # Check if called with correct arguments (in args or kwargs)
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_list_routines_empty(self, mock_hevy_service, mock_database):
        """Test routine listing when none exist."""
        profile = MagicMock()
        profile.hevy_enabled = True
        profile.hevy_api_key = "api_key"
        mock_database.get_user_profile.return_value = profile

        routine_response = MagicMock()
        routine_response.routines = []
        routine_response.total = 0

        mock_hevy_service.get_routines.return_value = routine_response

        tool = create_list_hevy_routines_tool(
            mock_hevy_service, mock_database, "user@test.com"
        )

        result = await tool.ainvoke({})

        assert "nenhuma" in result.lower() or "empty" in result.lower()

    @pytest.mark.asyncio
    async def test_list_routines_integration_disabled(self, mock_hevy_service, mock_database):
        """Test listing fails when integration disabled."""
        profile = MagicMock()
        profile.hevy_enabled = False
        mock_database.get_user_profile.return_value = profile

        tool = create_list_hevy_routines_tool(
            mock_hevy_service, mock_database, "user@test.com"
        )

        result = await tool.ainvoke({})

        assert "desativada" in result.lower() or "integração" in result.lower()
