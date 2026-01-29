import pytest
from src.trainers.gymbro_trainer import GymBroTrainer
from src.trainers.base_trainer import BaseTrainer


class TestGymBroTrainerInstantiation:
    """Tests for GymBroTrainer instantiation."""

    def test_gymbro_trainer_can_be_instantiated(self):
        """Verify GymBroTrainer can be instantiated."""
        trainer = GymBroTrainer()
        assert trainer is not None

    def test_gymbro_trainer_is_base_trainer_subclass(self):
        """Verify GymBroTrainer is a BaseTrainer subclass."""
        trainer = GymBroTrainer()
        assert isinstance(trainer, BaseTrainer)


class TestGymBroTrainerAttributes:
    """Tests for GymBroTrainer attributes."""

    def test_gymbro_trainer_id(self):
        """Verify GymBro trainer_id is correct."""
        trainer = GymBroTrainer()
        assert trainer.trainer_id == "gymbro"

    def test_gymbro_name(self):
        """Verify GymBro name is correct."""
        trainer = GymBroTrainer()
        assert trainer.name == "Breno 'The Bro' Silva"

    def test_gymbro_gender(self):
        """Verify GymBro gender is correct."""
        trainer = GymBroTrainer()
        assert trainer.gender == "Masculino"

    def test_gymbro_avatar_url(self):
        """Verify GymBro avatar URL is correct."""
        trainer = GymBroTrainer()
        assert trainer.avatar_url == "assets/avatars/gymbro.png"

    def test_gymbro_short_description(self):
        """Verify GymBro short description is correct."""
        trainer = GymBroTrainer()
        assert trainer.short_description == "Seu parceiro de treino que sempre te bota pra cima!"

    def test_gymbro_specialties(self):
        """Verify GymBro specialties are correct."""
        trainer = GymBroTrainer()
        assert isinstance(trainer.specialties, list)
        assert "#parceria" in trainer.specialties
        assert "#motivação" in trainer.specialties
        assert "#lifestyle" in trainer.specialties
        assert len(trainer.specialties) == 3

    def test_gymbro_catchphrase(self):
        """Verify GymBro catchphrase is correct."""
        trainer = GymBroTrainer()
        assert trainer.catchphrase == "Bora, monstro! Hoje é dia de EVOLUIR! 🔥"

    def test_gymbro_background_story_not_empty(self):
        """Verify GymBro background story is not empty."""
        trainer = GymBroTrainer()
        assert len(trainer.background_story) > 0
        assert "academia" in trainer.background_story.lower()


class TestGymBroTrainerPromptSection:
    """Tests for GymBroTrainer get_prompt_section method."""

    def test_gymbro_get_prompt_section_returns_string(self):
        """Verify get_prompt_section returns a string."""
        trainer = GymBroTrainer()
        prompt = trainer.get_prompt_section()
        assert isinstance(prompt, str)

    def test_gymbro_get_prompt_section_not_empty(self):
        """Verify get_prompt_section returns non-empty string."""
        trainer = GymBroTrainer()
        prompt = trainer.get_prompt_section()
        assert len(prompt) > 0

    def test_gymbro_get_prompt_section_contains_name(self):
        """Verify get_prompt_section includes trainer name."""
        trainer = GymBroTrainer()
        prompt = trainer.get_prompt_section()
        assert trainer.name in prompt

    def test_gymbro_get_prompt_section_contains_gender(self):
        """Verify get_prompt_section includes gender."""
        trainer = GymBroTrainer()
        prompt = trainer.get_prompt_section()
        assert trainer.gender in prompt

    def test_gymbro_get_prompt_section_contains_motivational_keywords(self):
        """Verify get_prompt_section contains motivational keywords."""
        trainer = GymBroTrainer()
        prompt = trainer.get_prompt_section()
        motivational_keywords = ["motivação", "parça", "ginásio", "encorajador"]
        assert any(keyword in prompt.lower() for keyword in motivational_keywords)

    def test_gymbro_get_prompt_section_contains_vocabulary_section(self):
        """Verify get_prompt_section contains vocabulary section."""
        trainer = GymBroTrainer()
        prompt = trainer.get_prompt_section()
        assert "vocabulário" in prompt.lower() or "gírias" in prompt.lower()


class TestGymBroTrainerCardDict:
    """Tests for GymBroTrainer to_card_dict method."""

    def test_gymbro_to_card_dict_returns_dict(self):
        """Verify to_card_dict returns a dictionary."""
        trainer = GymBroTrainer()
        card_dict = trainer.to_card_dict()
        assert isinstance(card_dict, dict)

    def test_gymbro_to_card_dict_trainer_id(self):
        """Verify to_card_dict includes correct trainer_id."""
        trainer = GymBroTrainer()
        card_dict = trainer.to_card_dict()
        assert card_dict["trainer_id"] == "gymbro"

    def test_gymbro_to_card_dict_has_all_keys(self):
        """Verify to_card_dict has all required keys."""
        trainer = GymBroTrainer()
        card_dict = trainer.to_card_dict()
        required_keys = [
            "trainer_id",
            "name",
            "gender",
            "avatar_url",
            "short_description",
            "specialties",
            "catchphrase",
        ]
        for key in required_keys:
            assert key in card_dict

    def test_gymbro_to_card_dict_name(self):
        """Verify to_card_dict includes correct name."""
        trainer = GymBroTrainer()
        card_dict = trainer.to_card_dict()
        assert card_dict["name"] == "Breno 'The Bro' Silva"
