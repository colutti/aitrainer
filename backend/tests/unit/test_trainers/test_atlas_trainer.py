import pytest
from src.trainers.atlas_trainer import AtlasTrainer
from src.trainers.base_trainer import BaseTrainer


class TestAtlasTrainerInstantiation:
    """Tests for AtlasTrainer instantiation."""

    def test_atlas_trainer_can_be_instantiated(self):
        """Verify AtlasTrainer can be instantiated."""
        trainer = AtlasTrainer()
        assert trainer is not None

    def test_atlas_trainer_is_base_trainer_subclass(self):
        """Verify AtlasTrainer is a BaseTrainer subclass."""
        trainer = AtlasTrainer()
        assert isinstance(trainer, BaseTrainer)


class TestAtlasTrainerAttributes:
    """Tests for AtlasTrainer attributes."""

    def test_atlas_trainer_id(self):
        """Verify Atlas trainer_id is correct."""
        trainer = AtlasTrainer()
        assert trainer.trainer_id == "atlas"

    def test_atlas_name(self):
        """Verify Atlas name is correct."""
        trainer = AtlasTrainer()
        assert trainer.name == "Atlas Prime"

    def test_atlas_gender(self):
        """Verify Atlas gender is correct."""
        trainer = AtlasTrainer()
        assert trainer.gender == "Masculino"

    def test_atlas_avatar_url(self):
        """Verify Atlas avatar URL is correct."""
        trainer = AtlasTrainer()
        assert trainer.avatar_url == "assets/avatars/atlas.png"

    def test_atlas_short_description(self):
        """Verify Atlas short description is correct."""
        trainer = AtlasTrainer()
        assert trainer.short_description == "A eficiência é a única métrica que importa."

    def test_atlas_specialties(self):
        """Verify Atlas specialties are correct."""
        trainer = AtlasTrainer()
        assert isinstance(trainer.specialties, list)
        assert "#biomecânica" in trainer.specialties
        assert "#dados" in trainer.specialties
        assert "#hipertrofia" in trainer.specialties
        assert len(trainer.specialties) == 3

    def test_atlas_catchphrase(self):
        """Verify Atlas catchphrase is correct."""
        trainer = AtlasTrainer()
        assert trainer.catchphrase == "Seus músculos são máquinas biológicas. Vamos otimizá-las."

    def test_atlas_background_story_not_empty(self):
        """Verify Atlas background story is not empty."""
        trainer = AtlasTrainer()
        assert len(trainer.background_story) > 0
        assert "laboratório" in trainer.background_story.lower()


class TestAtlasTrainerPromptSection:
    """Tests for AtlasTrainer get_prompt_section method."""

    def test_atlas_get_prompt_section_returns_string(self):
        """Verify get_prompt_section returns a string."""
        trainer = AtlasTrainer()
        prompt = trainer.get_prompt_section()
        assert isinstance(prompt, str)

    def test_atlas_get_prompt_section_not_empty(self):
        """Verify get_prompt_section returns non-empty string."""
        trainer = AtlasTrainer()
        prompt = trainer.get_prompt_section()
        assert len(prompt) > 0

    def test_atlas_get_prompt_section_contains_name(self):
        """Verify get_prompt_section includes trainer name."""
        trainer = AtlasTrainer()
        prompt = trainer.get_prompt_section()
        assert trainer.name in prompt

    def test_atlas_get_prompt_section_contains_gender(self):
        """Verify get_prompt_section includes gender."""
        trainer = AtlasTrainer()
        prompt = trainer.get_prompt_section()
        assert trainer.gender in prompt

    def test_atlas_get_prompt_section_contains_scientific_keywords(self):
        """Verify get_prompt_section contains scientific keywords."""
        trainer = AtlasTrainer()
        prompt = trainer.get_prompt_section()
        scientific_keywords = ["Biomecânica", "sintética", "eficiência", "dados"]
        assert any(keyword in prompt for keyword in scientific_keywords)

    def test_atlas_get_prompt_section_contains_vocabulary_section(self):
        """Verify get_prompt_section contains vocabulary section."""
        trainer = AtlasTrainer()
        prompt = trainer.get_prompt_section()
        assert "Vocabulário" in prompt or "vocabulário" in prompt.lower()


class TestAtlasTrainerCardDict:
    """Tests for AtlasTrainer to_card_dict method."""

    def test_atlas_to_card_dict_returns_dict(self):
        """Verify to_card_dict returns a dictionary."""
        trainer = AtlasTrainer()
        card_dict = trainer.to_card_dict()
        assert isinstance(card_dict, dict)

    def test_atlas_to_card_dict_trainer_id(self):
        """Verify to_card_dict includes correct trainer_id."""
        trainer = AtlasTrainer()
        card_dict = trainer.to_card_dict()
        assert card_dict["trainer_id"] == "atlas"

    def test_atlas_to_card_dict_has_all_keys(self):
        """Verify to_card_dict has all required keys."""
        trainer = AtlasTrainer()
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

    def test_atlas_to_card_dict_specialties_count(self):
        """Verify to_card_dict specialties count."""
        trainer = AtlasTrainer()
        card_dict = trainer.to_card_dict()
        assert len(card_dict["specialties"]) == 3
