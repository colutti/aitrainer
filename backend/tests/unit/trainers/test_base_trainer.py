import pytest
from abc import ABC
from src.trainers.base_trainer import BaseTrainer


class ConcreteTrainer(BaseTrainer):
    """Concrete implementation of BaseTrainer for testing."""

    trainer_id = "test_trainer"
    name = "Test Trainer"
    gender = "Masculino"
    avatar_url = "assets/avatars/test.png"
    short_description = "Test trainer for unit tests"
    specialties = ["#test", "#unittest"]
    catchphrase = "Testing is important"
    background_story = "This trainer was created for testing purposes"

    def get_prompt_section(self) -> str:
        return "## Test Trainer\nThis is a test trainer prompt section."


class TestBaseTrainerInstantiation:
    """Tests for BaseTrainer instantiation and interface."""

    def test_base_trainer_is_abstract(self):
        """Verify BaseTrainer cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseTrainer()  # type: ignore

    def test_concrete_trainer_can_be_instantiated(self):
        """Verify concrete trainer can be instantiated."""
        trainer = ConcreteTrainer()
        assert trainer is not None
        assert isinstance(trainer, BaseTrainer)

    def test_trainer_is_abc_subclass(self):
        """Verify BaseTrainer is an abstract base class."""
        assert issubclass(BaseTrainer, ABC)


class TestTrainerAttributes:
    """Tests for trainer attribute properties."""

    def test_trainer_has_trainer_id(self):
        """Verify trainer has trainer_id attribute."""
        trainer = ConcreteTrainer()
        assert hasattr(trainer, "trainer_id")
        assert trainer.trainer_id == "test_trainer"

    def test_trainer_has_name(self):
        """Verify trainer has name attribute."""
        trainer = ConcreteTrainer()
        assert hasattr(trainer, "name")
        assert trainer.name == "Test Trainer"

    def test_trainer_has_gender(self):
        """Verify trainer has gender attribute."""
        trainer = ConcreteTrainer()
        assert hasattr(trainer, "gender")
        assert trainer.gender == "Masculino"

    def test_trainer_has_avatar_url(self):
        """Verify trainer has avatar_url attribute."""
        trainer = ConcreteTrainer()
        assert hasattr(trainer, "avatar_url")
        assert trainer.avatar_url == "assets/avatars/test.png"

    def test_trainer_has_short_description(self):
        """Verify trainer has short_description attribute."""
        trainer = ConcreteTrainer()
        assert hasattr(trainer, "short_description")
        assert trainer.short_description == "Test trainer for unit tests"

    def test_trainer_has_specialties(self):
        """Verify trainer has specialties attribute (list)."""
        trainer = ConcreteTrainer()
        assert hasattr(trainer, "specialties")
        assert isinstance(trainer.specialties, list)
        assert "#test" in trainer.specialties

    def test_trainer_has_catchphrase(self):
        """Verify trainer has catchphrase attribute."""
        trainer = ConcreteTrainer()
        assert hasattr(trainer, "catchphrase")
        assert trainer.catchphrase == "Testing is important"

    def test_trainer_has_background_story(self):
        """Verify trainer has background_story attribute."""
        trainer = ConcreteTrainer()
        assert hasattr(trainer, "background_story")
        assert trainer.background_story == "This trainer was created for testing purposes"


class TestToCardDict:
    """Tests for to_card_dict method."""

    def test_to_card_dict_returns_dict(self):
        """Verify to_card_dict returns a dictionary."""
        trainer = ConcreteTrainer()
        card_dict = trainer.to_card_dict()
        assert isinstance(card_dict, dict)

    def test_to_card_dict_has_required_keys(self):
        """Verify to_card_dict contains all required keys."""
        trainer = ConcreteTrainer()
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

    def test_to_card_dict_values_match_attributes(self):
        """Verify to_card_dict values match trainer attributes."""
        trainer = ConcreteTrainer()
        card_dict = trainer.to_card_dict()
        assert card_dict["trainer_id"] == trainer.trainer_id
        assert card_dict["name"] == trainer.name
        assert card_dict["gender"] == trainer.gender
        assert card_dict["avatar_url"] == trainer.avatar_url
        assert card_dict["short_description"] == trainer.short_description
        assert card_dict["specialties"] == trainer.specialties
        assert card_dict["catchphrase"] == trainer.catchphrase

    def test_to_card_dict_excludes_background_story(self):
        """Verify to_card_dict does not include background_story."""
        trainer = ConcreteTrainer()
        card_dict = trainer.to_card_dict()
        assert "background_story" not in card_dict


class TestGetPromptSection:
    """Tests for get_prompt_section abstract method."""

    def test_get_prompt_section_returns_string(self):
        """Verify get_prompt_section returns a string."""
        trainer = ConcreteTrainer()
        prompt_section = trainer.get_prompt_section()
        assert isinstance(prompt_section, str)

    def test_get_prompt_section_not_empty(self):
        """Verify get_prompt_section returns non-empty string."""
        trainer = ConcreteTrainer()
        prompt_section = trainer.get_prompt_section()
        assert len(prompt_section) > 0

    def test_get_prompt_section_is_callable(self):
        """Verify get_prompt_section is callable."""
        trainer = ConcreteTrainer()
        assert callable(trainer.get_prompt_section)
