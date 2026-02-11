from src.trainers.sargento_trainer import SargentoTrainer
from src.trainers.base_trainer import BaseTrainer


class TestSargentoTrainerInstantiation:
    """Tests for SargentoTrainer instantiation."""

    def test_sargento_trainer_can_be_instantiated(self):
        """Verify SargentoTrainer can be instantiated."""
        trainer = SargentoTrainer()
        assert trainer is not None

    def test_sargento_trainer_is_base_trainer_subclass(self):
        """Verify SargentoTrainer is a BaseTrainer subclass."""
        trainer = SargentoTrainer()
        assert isinstance(trainer, BaseTrainer)


class TestSargentoTrainerAttributes:
    """Tests for SargentoTrainer attributes."""

    def test_sargento_trainer_id(self):
        """Verify Sargento trainer_id is correct."""
        trainer = SargentoTrainer()
        assert trainer.trainer_id == "sargento"

    def test_sargento_name(self):
        """Verify Sargento name is correct."""
        trainer = SargentoTrainer()
        assert trainer.name == "Major Steel"

    def test_sargento_gender(self):
        """Verify Sargento gender is correct."""
        trainer = SargentoTrainer()
        assert trainer.gender == "Masculino"

    def test_sargento_avatar_url(self):
        """Verify Sargento avatar URL is correct."""
        trainer = SargentoTrainer()
        assert trainer.avatar_url == "assets/avatars/sargento.png"

    def test_sargento_short_description(self):
        """Verify Sargento short description is correct."""
        trainer = SargentoTrainer()
        assert trainer.short_description == "A dor é a fraqueza saindo do corpo!"

    def test_sargento_specialties(self):
        """Verify Sargento specialties are correct."""
        trainer = SargentoTrainer()
        assert isinstance(trainer.specialties, list)
        assert "#disciplina" in trainer.specialties
        assert "#força" in trainer.specialties
        assert "#sem_desculpas" in trainer.specialties
        assert len(trainer.specialties) == 3

    def test_sargento_catchphrase(self):
        """Verify Sargento catchphrase is correct."""
        trainer = SargentoTrainer()
        assert trainer.catchphrase == "CAIA NO CHÃO E ME PAGUE VINTE, RECRUTA!"

    def test_sargento_background_story_not_empty(self):
        """Verify Sargento background story is not empty."""
        trainer = SargentoTrainer()
        assert len(trainer.background_story) > 0
        assert "Veterano" in trainer.background_story


class TestSargentoTrainerPromptSection:
    """Tests for SargentoTrainer get_prompt_section method."""

    def test_sargento_get_prompt_section_returns_string(self):
        """Verify get_prompt_section returns a string."""
        trainer = SargentoTrainer()
        prompt = trainer.get_prompt_section()
        assert isinstance(prompt, str)

    def test_sargento_get_prompt_section_not_empty(self):
        """Verify get_prompt_section returns non-empty string."""
        trainer = SargentoTrainer()
        prompt = trainer.get_prompt_section()
        assert len(prompt) > 0

    def test_sargento_get_prompt_section_contains_name(self):
        """Verify get_prompt_section includes trainer name."""
        trainer = SargentoTrainer()
        prompt = trainer.get_prompt_section()
        assert trainer.name in prompt

    def test_sargento_get_prompt_section_contains_gender(self):
        """Verify get_prompt_section includes gender."""
        trainer = SargentoTrainer()
        prompt = trainer.get_prompt_section()
        assert trainer.gender in prompt

    def test_sargento_get_prompt_section_contains_military_keywords(self):
        """Verify get_prompt_section contains military keywords."""
        trainer = SargentoTrainer()
        prompt = trainer.get_prompt_section()
        military_keywords = ["RECRUTA", "Bootcamp", "Militar", "DISCIPLINA"]
        assert any(keyword in prompt for keyword in military_keywords)

    def test_sargento_get_prompt_section_contains_vocabulary_section(self):
        """Verify get_prompt_section contains vocabulary section."""
        trainer = SargentoTrainer()
        prompt = trainer.get_prompt_section()
        assert "Vocabulário" in prompt or "VOCABULÁRIO" in prompt


class TestSargentoTrainerCardDict:
    """Tests for SargentoTrainer to_card_dict method."""

    def test_sargento_to_card_dict_returns_dict(self):
        """Verify to_card_dict returns a dictionary."""
        trainer = SargentoTrainer()
        card_dict = trainer.to_card_dict()
        assert isinstance(card_dict, dict)

    def test_sargento_to_card_dict_trainer_id(self):
        """Verify to_card_dict includes correct trainer_id."""
        trainer = SargentoTrainer()
        card_dict = trainer.to_card_dict()
        assert card_dict["trainer_id"] == "sargento"

    def test_sargento_to_card_dict_has_all_keys(self):
        """Verify to_card_dict has all required keys."""
        trainer = SargentoTrainer()
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

    def test_sargento_to_card_dict_catchphrase(self):
        """Verify to_card_dict includes correct catchphrase."""
        trainer = SargentoTrainer()
        card_dict = trainer.to_card_dict()
        assert card_dict["catchphrase"] == "CAIA NO CHÃO E ME PAGUE VINTE, RECRUTA!"
