from abc import ABC, abstractmethod
from typing import List


class BaseTrainer(ABC):
    """
    Abstract base class for all AI trainers.
    Defines the interface that all specific trainer personalities must implement.
    """

    trainer_id: str
    name: str
    gender: str
    avatar_url: str = ""
    short_description: str = ""
    specialties: List[str] = []
    catchphrase: str = ""
    background_story: str = ""

    def to_card_dict(self) -> dict:
        """
        Returns a dictionary representation for the frontend card.
        """
        return {
            "trainer_id": self.trainer_id,
            "name": self.name,
            "gender": self.gender,
            "avatar_url": self.avatar_url,
            "short_description": self.short_description,
            "specialties": self.specialties,
            "catchphrase": self.catchphrase,
        }

    @abstractmethod
    def get_prompt_section(self) -> str:
        """
        Returns the prompt section defining this trainer's personality.
        """
        pass
