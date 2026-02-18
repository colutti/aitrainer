from src.trainers.sofia_trainer import SofiaTrainer
from src.trainers.base_trainer import BaseTrainer


class TestSofiaTrainerInstantiation:
    """Tests for SofiaTrainer instantiation."""

    def test_sofia_trainer_can_be_instantiated(self):
        """Verify SofiaTrainer can be instantiated."""
        trainer = SofiaTrainer()
        assert trainer is not None

    def test_sofia_trainer_is_base_trainer_subclass(self):
        """Verify SofiaTrainer is a BaseTrainer subclass."""
        trainer = SofiaTrainer()
        assert isinstance(trainer, BaseTrainer)


class TestSofiaTrainerAttributes:
    """Tests for SofiaTrainer attributes."""

    def test_sofia_trainer_id(self):
        """Verify Sofia trainer_id is correct."""
        trainer = SofiaTrainer()
        assert trainer.trainer_id == "sofia"

    def test_sofia_name(self):
        """Verify Sofia name is correct."""
        trainer = SofiaTrainer()
        assert trainer.name == "Dra. Sofia Pulse"

    def test_sofia_gender(self):
        """Verify Sofia gender is correct."""
        trainer = SofiaTrainer()
        assert trainer.gender == "Feminino"

    def test_sofia_avatar_url(self):
        """Verify Sofia avatar URL is correct."""
        trainer = SofiaTrainer()
        assert trainer.avatar_url == "assets/avatars/sofia.png"

    def test_sofia_short_description(self):
        """Verify Sofia short description is correct."""
        trainer = SofiaTrainer()
        assert trainer.short_description == "Saúde inteligente para mulheres modernas."

    def test_sofia_specialties(self):
        """Verify Sofia specialties are correct."""
        trainer = SofiaTrainer()
        assert isinstance(trainer.specialties, list)
        assert "#saúdefeminina" in trainer.specialties
        assert "#hormônios" in trainer.specialties
        assert "#metabolismo" in trainer.specialties
        assert len(trainer.specialties) == 3

    def test_sofia_catchphrase(self):
        """Verify Sofia catchphrase is correct."""
        trainer = SofiaTrainer()
        assert trainer.catchphrase == "Vamos hackear seu metabolismo com ciência e carinho."

    def test_sofia_background_story_not_empty(self):
        """Verify Sofia background story is not empty."""
        trainer = SofiaTrainer()
        assert len(trainer.background_story) > 0
        assert "PhD" in trainer.background_story


class TestSofiaTrainerPromptSection:
    """Tests for SofiaTrainer get_prompt_section method."""

    def test_sofia_get_prompt_section_returns_string(self):
        """Verify get_prompt_section returns a string."""
        trainer = SofiaTrainer()
        prompt = trainer.get_prompt_section()
        assert isinstance(prompt, str)

    def test_sofia_get_prompt_section_not_empty(self):
        """Verify get_prompt_section returns non-empty string."""
        trainer = SofiaTrainer()
        prompt = trainer.get_prompt_section()
        assert len(prompt) > 0

    def test_sofia_get_prompt_section_contains_name(self):
        """Verify get_prompt_section includes trainer name."""
        trainer = SofiaTrainer()
        prompt = trainer.get_prompt_section()
        assert trainer.name in prompt

    def test_sofia_get_prompt_section_contains_gender(self):
        """Verify get_prompt_section includes gender."""
        trainer = SofiaTrainer()
        prompt = trainer.get_prompt_section()
        assert trainer.gender in prompt

    def test_sofia_get_prompt_section_contains_medical_keywords(self):
        """Verify get_prompt_section contains medical/scientific keywords."""
        trainer = SofiaTrainer()
        prompt = trainer.get_prompt_section()
        medical_keywords = ["médica", "hormonal", "metabolismo", "científica"]
        assert any(keyword in prompt.lower() for keyword in medical_keywords)

    def test_sofia_get_prompt_section_contains_vocabulary_section(self):
        """Verify get_prompt_section contains vocabulary section."""
        trainer = SofiaTrainer()
        prompt = trainer.get_prompt_section()
        assert "Vocabulário" in prompt or "vocabulário" in prompt.lower()


class TestSofiaTrainerCardDict:
    """Tests for SofiaTrainer to_card_dict method."""

    def test_sofia_to_card_dict_returns_dict(self):
        """Verify to_card_dict returns a dictionary."""
        trainer = SofiaTrainer()
        card_dict = trainer.to_card_dict()
        assert isinstance(card_dict, dict)

    def test_sofia_to_card_dict_trainer_id(self):
        """Verify to_card_dict includes correct trainer_id."""
        trainer = SofiaTrainer()
        card_dict = trainer.to_card_dict()
        assert card_dict["trainer_id"] == "sofia"

    def test_sofia_to_card_dict_has_all_keys(self):
        """Verify to_card_dict has all required keys."""
        trainer = SofiaTrainer()
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

    def test_sofia_to_card_dict_gender(self):
        """Verify to_card_dict includes correct gender."""
        trainer = SofiaTrainer()
        card_dict = trainer.to_card_dict()
        assert card_dict["gender"] == "Feminino"
