from pydantic import BaseModel, Field
from src.trainers.registry import TrainerRegistry


class TrainerProfileInput(BaseModel):
    """
    Editable fields of the trainer profile (user input).
    """

    trainer_type: str = Field(
        ...,
        description="The ID of the selected trainer (e.g., 'atlas', 'luna', 'sargento', 'sofia').",
    )


class TrainerProfile(TrainerProfileInput):
    """
    TrainerProfile model representing the complete profile (includes user_email).
    """

    user_email: str = Field(..., description="User's email")

    def get_trainer_profile_summary(self) -> str:
        """
        Generates a summary of the trainer's profile for use in prompts.
        Fetches the specific trainer implementation from the registry and returns its prompt section.

        Returns:
            str: Formatted summary of the trainer's profile.
        """
        registry = TrainerRegistry()
        trainer = registry.get_trainer(self.trainer_type)
        return trainer.get_prompt_section()
