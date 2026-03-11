"""
Module for trainer implementation.
"""

from typing import Dict, List
from src.trainers.base_trainer import BaseTrainer
from src.trainers.atlas_trainer import AtlasTrainer
from src.trainers.luna_trainer import LunaTrainer
from src.trainers.sargento_trainer import SargentoTrainer
from src.trainers.sofia_trainer import SofiaTrainer
from src.trainers.gymbro_trainer import GymBroTrainer


class TrainerRegistry:
    """
    Singleton registry for managing available trainers.
    """

    _instance = None
    _trainers: Dict[str, BaseTrainer] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TrainerRegistry, cls).__new__(cls)
            cls._instance._initialize_trainers()
        return cls._instance

    def _initialize_trainers(self):
        """
        Instantiates specific trainer classes and registers them.
        """
        trainers = [
            AtlasTrainer(),
            LunaTrainer(),
            SargentoTrainer(),
            SofiaTrainer(),
            GymBroTrainer(),
        ]
        for trainer in trainers:
            self._trainers[trainer.trainer_id] = trainer

    def get_trainer(self, trainer_id: str) -> BaseTrainer:
        """
        Retrieves a trainer instance by ID. Returns 'atlas' if not found.
        """
        return self._trainers.get(trainer_id, self._trainers["atlas"])

    def get_all_trainers(self) -> List[BaseTrainer]:
        """
        Returns a list of all available trainer instances.
        """
        return list(self._trainers.values())

    def get_default_trainer(self) -> BaseTrainer:
        """
        Returns the default trainer (Atlas).
        """
        return self._trainers["atlas"]

    def list_trainers_for_api(self) -> List[dict]:
        """
        Returns list of dicts suitable for frontend consumption (cards).
        """
        return [t.to_card_dict() for t in self.get_all_trainers()]
