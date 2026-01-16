from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class UserProfileInput(BaseModel):
    """
    Data class to hold user configuration and profile data for input.
    """

    gender: str = Field(
        ..., description="User's gender", pattern="^(Masculino|Feminino)$"
    )
    age: int = Field(..., ge=18, le=100, description="Age between 18 and 100 years")
    weight: float = Field(
        ..., ge=30.0, le=500.0, description="Weight in kg between 30 and 500"
    )
    height: int = Field(..., ge=100, le=250, description="Height in cm between 100 and 250")
    goal: str = Field(..., min_length=5, description="User's goal")
    goal_type: str = Field(..., pattern="^(lose|gain|maintain)$", description="Type of goal: lose, gain, or maintain")
    target_weight: float | None = Field(None, ge=30.0, le=500.0, description="Target weight in kg (optional)")
    weekly_rate: float = Field(0.5, ge=0.0, le=2.0, description="Desired weekly weight change rate in kg")


class UserProfile(UserProfileInput):
    """
    Data class to hold user configuration and profile data.
    """
    email: str = Field(..., description="User's email")
    
    # Hevy Integration
    hevy_api_key: Optional[str] = Field(None, description="Hevy API key, encrypted")
    hevy_enabled: bool = Field(False, description="Integration enabled/disabled toggle")
    hevy_last_sync: Optional[datetime] = Field(None, description="Last successful sync timestamp")

    def get_profile_summary(self) -> str:
        """
        Generates a summary of the user's profile for use in prompts.

        Returns:
            str: Formatted summary of the user's profile as a markdown table.
        """
        return (
            f"| Campo | Valor |\n"
            f"|-------|-------|\n"
            f"| Gênero | {self.gender} |\n"
            f"| Idade | {self.age} anos |\n"
            f"| Peso | {self.weight}kg |\n"
            f"| Altura | {self.height}cm |\n"
            f"| Objetivo | {self.goal} |"
        )