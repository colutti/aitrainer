from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, model_validator

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
    goal: Optional[str] = Field(None, description="User's goal (legacy)")
    goal_type: str = Field(..., pattern="^(lose|gain|maintain)$", description="Type of goal: lose, gain, or maintain")
    target_weight: float | None = Field(None, ge=30.0, le=500.0, description="Target weight in kg (optional)")
    weekly_rate: float = Field(0.5, ge=0.0, le=2.0, description="Desired weekly weight change rate in kg")
    notes: Optional[str] = Field(None, max_length=1000, description="User observations/notes")

    # New V3 Field: Stores compacted history context
    long_term_summary: str | None = Field(None, description="Stores compacted history context")
    
    # New V3 Field: Tracks the timestamp of the last message included in the summary
    last_compaction_timestamp: str | None = Field(None, description="ISO timestamp of the last summarized message")

    @model_validator(mode="after")
    def validate_weekly_rate(self) -> "UserProfileInput":
        if self.goal_type in ("lose", "gain") and (self.weekly_rate is None or self.weekly_rate <= 0):
            raise ValueError("Weekly rate must be greater than 0 for lose or gain goals")
        return self


class UserProfile(UserProfileInput):
    """
    Data class to hold user configuration and profile data.
    """
    email: str = Field(..., description="User's email")
    password_hash: Optional[str] = Field(None, description="Hashed password for authentication")
    
    # Hevy Integration
    hevy_api_key: Optional[str] = Field(None, description="Hevy API key, encrypted")
    hevy_enabled: bool = Field(False, description="Integration enabled/disabled toggle")
    hevy_last_sync: Optional[datetime] = Field(None, description="Last successful sync timestamp")
    hevy_webhook_token: Optional[str] = Field(None, description="Unique token for webhook URL path")
    hevy_webhook_secret: Optional[str] = Field(None, description="Secret for Authorization header validation")

    def _goal_type_label(self) -> str:
        labels = {"lose": "Perder peso", "gain": "Ganhar massa", "maintain": "Manter peso"}
        return labels.get(self.goal_type, self.goal_type)

    def get_profile_summary(self) -> str:
        """
        Generates a summary of the user's profile for use in prompts.

        Returns:
            str: Formatted summary of the user's profile as key-value pairs.
        """
        return (
            f"**Gênero:** {self.gender}\n"
            f"**Idade:** {self.age} anos\n"
            f"**Peso Inicial:** {self.weight}kg\n"
            f"**Altura:** {self.height}cm\n"
            f"**Tipo de Objetivo:** {self._goal_type_label()}\n"
            f"**Taxa Semanal:** {self.weekly_rate}kg/semana\n"
            f"**Observações:** {self.notes or 'Nenhuma'}"
        )