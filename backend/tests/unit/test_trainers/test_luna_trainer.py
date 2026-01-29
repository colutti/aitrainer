import pytest
from src.trainers.luna_trainer import LunaTrainer
from src.trainers.base_trainer import BaseTrainer


class TestLunaTrainerInstantiation:
    """Tests for LunaTrainer instantiation."""

    def test_luna_trainer_can_be_instantiated(self):
        """Verify LunaTrainer can be instantiated."""
        trainer = LunaTrainer()
        assert trainer is not None

    def test_luna_trainer_is_base_trainer_subclass(self):
        """Verify LunaTrainer is a BaseTrainer subclass."""
        trainer = LunaTrainer()
        assert isinstance(trainer, BaseTrainer)


class TestLunaTrainerAttributes:
    """Tests for LunaTrainer attributes."""

    def test_luna_trainer_id(self):
        """Verify Luna trainer_id is correct."""
        trainer = LunaTrainer()
        assert trainer.trainer_id == "luna"

    def test_luna_name(self):
        """Verify Luna name is correct."""
        trainer = LunaTrainer()
        assert trainer.name == "Luna Stardust"

    def test_luna_gender(self):
        """Verify Luna gender is correct."""
        trainer = LunaTrainer()
        assert trainer.gender == "Feminino"

    def test_luna_avatar_url(self):
        """Verify Luna avatar URL is correct."""
        trainer = LunaTrainer()
        assert trainer.avatar_url == "assets/avatars/luna.png"

    def test_luna_short_description(self):
        """Verify Luna short description is correct."""
        trainer = LunaTrainer()
        assert trainer.short_description == "Seu corpo é um templo estelar."

    def test_luna_specialties(self):
        """Verify Luna specialties are correct."""
        trainer = LunaTrainer()
        assert isinstance(trainer.specialties, list)
        assert "#yoga" in trainer.specialties
        assert "#mindfulness" in trainer.specialties
        assert "#fluxo" in trainer.specialties
        assert len(trainer.specialties) == 3

    def test_luna_catchphrase(self):
        """Verify Luna catchphrase is correct."""
        trainer = LunaTrainer()
        assert trainer.catchphrase == "Respire o universo, expire as tensões."

    def test_luna_background_story_not_empty(self):
        """Verify Luna background story is not empty."""
        trainer = LunaTrainer()
        assert len(trainer.background_story) > 0
        assert "yoga" in trainer.background_story.lower()


class TestLunaTrainerPromptSection:
    """Tests for LunaTrainer get_prompt_section method."""

    def test_luna_get_prompt_section_returns_string(self):
        """Verify get_prompt_section returns a string."""
        trainer = LunaTrainer()
        prompt = trainer.get_prompt_section()
        assert isinstance(prompt, str)

    def test_luna_get_prompt_section_not_empty(self):
        """Verify get_prompt_section returns non-empty string."""
        trainer = LunaTrainer()
        prompt = trainer.get_prompt_section()
        assert len(prompt) > 0

    def test_luna_get_prompt_section_contains_name(self):
        """Verify get_prompt_section includes trainer name."""
        trainer = LunaTrainer()
        prompt = trainer.get_prompt_section()
        assert trainer.name in prompt

    def test_luna_get_prompt_section_contains_gender(self):
        """Verify get_prompt_section includes gender."""
        trainer = LunaTrainer()
        prompt = trainer.get_prompt_section()
        assert trainer.gender in prompt

    def test_luna_get_prompt_section_contains_holistic_keywords(self):
        """Verify get_prompt_section contains holistic/spiritual keywords."""
        trainer = LunaTrainer()
        prompt = trainer.get_prompt_section()
        holistic_keywords = ["holística", "espiritual", "cosmos", "energia"]
        assert any(keyword in prompt.lower() for keyword in holistic_keywords)

    def test_luna_get_prompt_section_contains_vocabulary_section(self):
        """Verify get_prompt_section contains vocabulary section."""
        trainer = LunaTrainer()
        prompt = trainer.get_prompt_section()
        assert "Vocabulário" in prompt or "vocabulário" in prompt.lower()


class TestLunaTrainerCardDict:
    """Tests for LunaTrainer to_card_dict method."""

    def test_luna_to_card_dict_returns_dict(self):
        """Verify to_card_dict returns a dictionary."""
        trainer = LunaTrainer()
        card_dict = trainer.to_card_dict()
        assert isinstance(card_dict, dict)

    def test_luna_to_card_dict_trainer_id(self):
        """Verify to_card_dict includes correct trainer_id."""
        trainer = LunaTrainer()
        card_dict = trainer.to_card_dict()
        assert card_dict["trainer_id"] == "luna"

    def test_luna_to_card_dict_has_all_keys(self):
        """Verify to_card_dict has all required keys."""
        trainer = LunaTrainer()
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

    def test_luna_to_card_dict_name(self):
        """Verify to_card_dict includes correct name."""
        trainer = LunaTrainer()
        card_dict = trainer.to_card_dict()
        assert card_dict["name"] == "Luna Stardust"
