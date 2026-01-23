
import unittest
from unittest.mock import MagicMock, AsyncMock
from src.services.hevy_tools import (
    create_list_hevy_routines_tool,
    create_search_hevy_exercises_tool,
    create_create_hevy_routine_tool,
    create_update_hevy_routine_tool,
)
from src.api.models.user_profile import UserProfile

class TestHevyTools(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_hevy_service = MagicMock()
        self.user_email = "test@example.com"
        
        # Default mock profile
        self.mock_profile = MagicMock(spec=UserProfile)
        self.mock_profile.hevy_enabled = True
        self.mock_profile.hevy_api_key = "test_api_key"
        self.mock_db.get_user_profile.return_value = self.mock_profile

    def test_list_routines_integration_disabled(self):
        """Test listing routines when integration is disabled."""
        self.mock_profile.hevy_enabled = False
        
        tool = create_list_hevy_routines_tool(self.mock_hevy_service, self.mock_db, self.user_email)
        result = tool.invoke({"page": 1})
        
        self.assertIn("integração com Hevy está desativada", result)
        self.mock_hevy_service.get_routines.assert_not_called()

    def test_list_routines_success(self):
        """Test listing routines successfully."""
        tool = create_list_hevy_routines_tool(self.mock_hevy_service, self.mock_db, self.user_email)
        
        # Mock async response
        mock_response = MagicMock()
        mock_response.page = 1
        mock_response.page_count = 1
        
        routine1 = MagicMock()
        routine1.title = "Treino A"
        routine1.notes = "Foco em força"
        
        ex1 = MagicMock()
        ex1.title = "Supino"
        routine1.exercises = [ex1]
        
        mock_response.routines = [routine1]
        
        self.mock_hevy_service.get_routines = AsyncMock(return_value=mock_response)
        
        result = tool.invoke({"page": 1})
        
        self.assertIn("Encontrei 1 rotinas", result)
        self.assertIn("Treino A", result)
        self.assertIn("Supino", result)

    def test_list_routines_empty(self):
        """Test listing routines when none found."""
        tool = create_list_hevy_routines_tool(self.mock_hevy_service, self.mock_db, self.user_email)
        
        mock_response = MagicMock()
        mock_response.routines = []
        self.mock_hevy_service.get_routines = AsyncMock(return_value=mock_response)
        
        result = tool.invoke({"page": 1})
        
        self.assertIn("Nenhuma rotina encontrada", result)

    def test_search_exercises_success(self):
        """Test searching exercises."""
        tool = create_search_hevy_exercises_tool(self.mock_hevy_service, self.mock_db, self.user_email)
        
        ex1 = MagicMock()
        ex1.title = "Supino Reto"
        ex1.id = "sup_123"
        ex1.primary_muscle_group = "Chest"
        
        ex2 = MagicMock()
        ex2.title = "Agachamento"
        ex2.id = "sqt_456"
        
        self.mock_hevy_service.get_all_exercise_templates = AsyncMock(return_value=[ex1, ex2])
        
        result = tool.invoke({"query": "supino"})
        
        self.assertIn("Supino Reto", result)
        self.assertIn("sup_123", result)
        self.assertNotIn("Agachamento", result)

    def test_search_exercises_no_match(self):
        """Test searching exercises with no match."""
        tool = create_search_hevy_exercises_tool(self.mock_hevy_service, self.mock_db, self.user_email)
        
        self.mock_hevy_service.get_all_exercise_templates = AsyncMock(return_value=[])
        
        result = tool.invoke({"query": "voador"})
        
        self.assertIn("Nenhum exercício encontrado", result)

    def test_create_routine_success(self):
        """Test creating a routine successfully."""
        tool = create_create_hevy_routine_tool(self.mock_hevy_service, self.mock_db, self.user_email)
        
        mock_created = MagicMock()
        mock_created.title = "Novo Treino"
        mock_created.id = "new_123"
        
        self.mock_hevy_service.create_routine = AsyncMock(return_value=(mock_created, None))
        
        result = tool.invoke({
            "title": "Novo Treino",
            "exercises": [{"exercise_template_id": "123", "sets": [{"type": "normal", "weight_kg": 10, "reps": 10}]}]
        })
        
        self.assertIn("criada com sucesso", result)
        self.assertIn("new_123", result)

    def test_create_routine_limit_exceeded(self):
        """Test creating routine when limit exceeded."""
        tool = create_create_hevy_routine_tool(self.mock_hevy_service, self.mock_db, self.user_email)
        
        self.mock_hevy_service.create_routine = AsyncMock(return_value=(None, "LIMIT_EXCEEDED"))
        
        result = tool.invoke({
            "title": "Novo Treino",
            "exercises": [{"exercise_template_id": "123"}]
        })
        
        self.assertIn("Limite atingido", result)

    def test_create_routine_validation_error(self):
        """Test validation errors in create routine."""
        tool = create_create_hevy_routine_tool(self.mock_hevy_service, self.mock_db, self.user_email)
        
        # Missing exercises
        result = tool.invoke({"title": "Empty Routine", "exercises": []})
        self.assertIn("deve conter pelo menos um exercício", result)
        
        # Missing title
        result = tool.invoke({"title": "", "exercises": [{}]})
        self.assertIn("título da rotina é obrigatório", result)

    def test_update_routine_success(self):
        """Test updating a routine successfully using title."""
        tool = create_update_hevy_routine_tool(self.mock_hevy_service, self.mock_db, self.user_email)

        # Mock list response
        routine1 = MagicMock()
        routine1.id = "routine_123"
        routine1.title = "Pull Workout"

        list_response = MagicMock()
        list_response.routines = [routine1]

        # Mock get by ID response
        current_routine = MagicMock()
        current_routine.id = "routine_123"
        current_routine.title = "Pull Workout"
        current_routine.notes = "Old notes"
        current_routine.exercises = []

        updated_routine = MagicMock()
        updated_routine.title = "Pull Workout"
        updated_routine.notes = "Updated!"

        self.mock_hevy_service.get_routines = AsyncMock(return_value=list_response)
        self.mock_hevy_service.get_routine_by_id = AsyncMock(return_value=current_routine)
        self.mock_hevy_service.update_routine = AsyncMock(return_value=updated_routine)

        # Call with TITLE instead of ID
        result = tool.invoke({
            "routine_title": "Pull Workout",
            "notes": "Updated!"
        })

        self.assertIn("atualizada com sucesso", result)
        self.assertEqual(current_routine.notes, "Updated!")

    def test_update_routine_fuzzy_match(self):
        """Test updating a routine with case-insensitive fuzzy matching."""
        tool = create_update_hevy_routine_tool(self.mock_hevy_service, self.mock_db, self.user_email)

        routine1 = MagicMock()
        routine1.id = "routine_123"
        routine1.title = "Pull Workout A"

        list_response = MagicMock()
        list_response.routines = [routine1]

        current_routine = MagicMock()
        current_routine.id = "routine_123"
        current_routine.title = "Pull Workout A"
        current_routine.exercises = []

        updated_routine = MagicMock()
        updated_routine.title = "Pull Workout A"

        self.mock_hevy_service.get_routines = AsyncMock(return_value=list_response)
        self.mock_hevy_service.get_routine_by_id = AsyncMock(return_value=current_routine)
        self.mock_hevy_service.update_routine = AsyncMock(return_value=updated_routine)

        # Call with partial/fuzzy title
        result = tool.invoke({
            "routine_title": "pull",  # lowercase, partial
            "notes": "Test"
        })

        self.assertIn("atualizada com sucesso", result)

    def test_update_routine_not_found(self):
        """Test updating a routine that is not in the list."""
        tool = create_update_hevy_routine_tool(self.mock_hevy_service, self.mock_db, self.user_email)

        # Mock list with some routines
        routine1 = MagicMock()
        routine1.title = "Other Routine"
        list_response = MagicMock()
        list_response.routines = [routine1]
        self.mock_hevy_service.get_routines = AsyncMock(return_value=list_response)

        result = tool.invoke({"routine_title": "NonExistent"})

        self.assertIn("não encontrada", result)
        self.assertIn("Rotinas disponíveis", result)
        self.assertIn("Other Routine", result)

    def test_update_routine_no_routines_at_all(self):
        """Test updating when user has no routines at all."""
        tool = create_update_hevy_routine_tool(self.mock_hevy_service, self.mock_db, self.user_email)

        # Mock empty list
        list_response = MagicMock()
        list_response.routines = []
        self.mock_hevy_service.get_routines = AsyncMock(return_value=list_response)

        result = tool.invoke({"routine_title": "Any"})

        self.assertIn("Nenhuma rotina encontrada", result)
