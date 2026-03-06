import pytest
from unittest.mock import MagicMock
from src.services.metabolism_tools import create_reset_tdee_tracking_tool
from src.api.models.user_profile import UserProfile

@pytest.fixture
def mock_db():
    return MagicMock()

def test_reset_tdee_tracking_tool(mock_db):
    # Setup mock user profile
    profile = UserProfile(
        gender="Masculino", 
        age=30, 
        height=180, 
        goal_type="maintain", 
        email="test@user.com", 
        name="Test"
    )
    mock_db.get_user_profile.return_value = profile
    
    # This might fail initially because create_reset_tdee_tracking_tool is NOT defined yet
    from src.services.metabolism_tools import create_reset_tdee_tracking_tool
    
    tool = create_reset_tdee_tracking_tool(mock_db, "test@user.com")
    result = tool.invoke({"start_date_iso": "2026-03-06"})
    
    assert "sucesso" in result.lower()
    assert profile.tdee_start_date == "2026-03-06"
    mock_db.save_user_profile.assert_called_once_with(profile)
