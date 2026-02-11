from src.trainers.registry import TrainerRegistry
from src.trainers.base_trainer import BaseTrainer
from src.trainers.atlas_trainer import AtlasTrainer
from src.trainers.luna_trainer import LunaTrainer
from src.trainers.sofia_trainer import SofiaTrainer
from src.trainers.sargento_trainer import SargentoTrainer
from src.trainers.gymbro_trainer import GymBroTrainer


class TestTrainerRegistrySingleton:
    """Tests for TrainerRegistry singleton pattern."""

    def test_trainer_registry_is_singleton(self):
        """Verify TrainerRegistry follows singleton pattern."""
        registry1 = TrainerRegistry()
        registry2 = TrainerRegistry()
        assert registry1 is registry2

    def test_trainer_registry_instantiation(self):
        """Verify TrainerRegistry can be instantiated."""
        registry = TrainerRegistry()
        assert registry is not None

    def test_trainer_registry_multiple_instances_are_same(self):
        """Verify multiple TrainerRegistry calls return same instance."""
        instances = [TrainerRegistry() for _ in range(5)]
        for instance in instances[1:]:
            assert instance is instances[0]


class TestTrainerRegistryInitialization:
    """Tests for TrainerRegistry initialization."""

    def test_registry_initializes_all_trainers(self):
        """Verify registry initializes all 5 trainers."""
        registry = TrainerRegistry()
        all_trainers = registry.get_all_trainers()
        assert len(all_trainers) == 5

    def test_registry_has_atlas_trainer(self):
        """Verify registry contains Atlas trainer."""
        registry = TrainerRegistry()
        trainer = registry.get_trainer("atlas")
        assert isinstance(trainer, AtlasTrainer)

    def test_registry_has_luna_trainer(self):
        """Verify registry contains Luna trainer."""
        registry = TrainerRegistry()
        trainer = registry.get_trainer("luna")
        assert isinstance(trainer, LunaTrainer)

    def test_registry_has_sofia_trainer(self):
        """Verify registry contains Sofia trainer."""
        registry = TrainerRegistry()
        trainer = registry.get_trainer("sofia")
        assert isinstance(trainer, SofiaTrainer)

    def test_registry_has_sargento_trainer(self):
        """Verify registry contains Sargento trainer."""
        registry = TrainerRegistry()
        trainer = registry.get_trainer("sargento")
        assert isinstance(trainer, SargentoTrainer)

    def test_registry_has_gymbro_trainer(self):
        """Verify registry contains GymBro trainer."""
        registry = TrainerRegistry()
        trainer = registry.get_trainer("gymbro")
        assert isinstance(trainer, GymBroTrainer)


class TestGetTrainer:
    """Tests for get_trainer method."""

    def test_get_trainer_by_id(self):
        """Verify get_trainer returns trainer by id."""
        registry = TrainerRegistry()
        trainer = registry.get_trainer("atlas")
        assert trainer.trainer_id == "atlas"

    def test_get_trainer_returns_base_trainer(self):
        """Verify get_trainer returns BaseTrainer subclass."""
        registry = TrainerRegistry()
        trainer = registry.get_trainer("luna")
        assert isinstance(trainer, BaseTrainer)

    def test_get_trainer_invalid_id_returns_default(self):
        """Verify get_trainer returns default (atlas) for invalid ID."""
        registry = TrainerRegistry()
        trainer = registry.get_trainer("nonexistent")
        assert trainer.trainer_id == "atlas"

    def test_get_trainer_with_empty_string_returns_default(self):
        """Verify get_trainer returns default for empty string."""
        registry = TrainerRegistry()
        trainer = registry.get_trainer("")
        assert trainer.trainer_id == "atlas"

    def test_get_trainer_all_valid_ids(self):
        """Verify get_trainer works for all valid trainer IDs."""
        registry = TrainerRegistry()
        valid_ids = ["atlas", "luna", "sofia", "sargento", "gymbro"]
        for trainer_id in valid_ids:
            trainer = registry.get_trainer(trainer_id)
            assert trainer.trainer_id == trainer_id


class TestGetAllTrainers:
    """Tests for get_all_trainers method."""

    def test_get_all_trainers_returns_list(self):
        """Verify get_all_trainers returns a list."""
        registry = TrainerRegistry()
        trainers = registry.get_all_trainers()
        assert isinstance(trainers, list)

    def test_get_all_trainers_count(self):
        """Verify get_all_trainers returns exactly 5 trainers."""
        registry = TrainerRegistry()
        trainers = registry.get_all_trainers()
        assert len(trainers) == 5

    def test_get_all_trainers_all_are_base_trainer(self):
        """Verify all returned trainers are BaseTrainer instances."""
        registry = TrainerRegistry()
        trainers = registry.get_all_trainers()
        for trainer in trainers:
            assert isinstance(trainer, BaseTrainer)

    def test_get_all_trainers_contains_unique_ids(self):
        """Verify all trainers have unique IDs."""
        registry = TrainerRegistry()
        trainers = registry.get_all_trainers()
        trainer_ids = [t.trainer_id for t in trainers]
        assert len(trainer_ids) == len(set(trainer_ids))

    def test_get_all_trainers_not_empty(self):
        """Verify get_all_trainers never returns empty list."""
        registry = TrainerRegistry()
        trainers = registry.get_all_trainers()
        assert len(trainers) > 0


class TestGetDefaultTrainer:
    """Tests for get_default_trainer method."""

    def test_get_default_trainer_returns_atlas(self):
        """Verify get_default_trainer returns Atlas."""
        registry = TrainerRegistry()
        trainer = registry.get_default_trainer()
        assert trainer.trainer_id == "atlas"

    def test_get_default_trainer_returns_base_trainer(self):
        """Verify get_default_trainer returns BaseTrainer instance."""
        registry = TrainerRegistry()
        trainer = registry.get_default_trainer()
        assert isinstance(trainer, BaseTrainer)

    def test_get_default_trainer_is_atlas_instance(self):
        """Verify get_default_trainer returns AtlasTrainer instance."""
        registry = TrainerRegistry()
        trainer = registry.get_default_trainer()
        assert isinstance(trainer, AtlasTrainer)


class TestListTrainersForAPI:
    """Tests for list_trainers_for_api method."""

    def test_list_trainers_for_api_returns_list(self):
        """Verify list_trainers_for_api returns a list."""
        registry = TrainerRegistry()
        trainers_list = registry.list_trainers_for_api()
        assert isinstance(trainers_list, list)

    def test_list_trainers_for_api_count(self):
        """Verify list_trainers_for_api returns 5 trainers."""
        registry = TrainerRegistry()
        trainers_list = registry.list_trainers_for_api()
        assert len(trainers_list) == 5

    def test_list_trainers_for_api_returns_dicts(self):
        """Verify list_trainers_for_api returns list of dicts."""
        registry = TrainerRegistry()
        trainers_list = registry.list_trainers_for_api()
        for trainer in trainers_list:
            assert isinstance(trainer, dict)

    def test_list_trainers_for_api_dicts_have_required_keys(self):
        """Verify each dict has required keys."""
        registry = TrainerRegistry()
        trainers_list = registry.list_trainers_for_api()
        required_keys = [
            "trainer_id",
            "name",
            "gender",
            "avatar_url",
            "short_description",
            "specialties",
            "catchphrase",
        ]
        for trainer in trainers_list:
            for key in required_keys:
                assert key in trainer

    def test_list_trainers_for_api_includes_all_trainer_ids(self):
        """Verify API list includes all trainer IDs."""
        registry = TrainerRegistry()
        trainers_list = registry.list_trainers_for_api()
        trainer_ids = [t["trainer_id"] for t in trainers_list]
        expected_ids = ["atlas", "luna", "sofia", "sargento", "gymbro"]
        for expected_id in expected_ids:
            assert expected_id in trainer_ids

    def test_list_trainers_for_api_no_background_story(self):
        """Verify API list does not include background_story."""
        registry = TrainerRegistry()
        trainers_list = registry.list_trainers_for_api()
        for trainer in trainers_list:
            assert "background_story" not in trainer


class TestTrainerRegistryConsistency:
    """Tests for consistency across registry methods."""

    def test_registry_consistency_across_calls(self):
        """Verify registry returns same trainer instances across calls."""
        registry = TrainerRegistry()
        trainer1 = registry.get_trainer("atlas")
        trainer2 = registry.get_trainer("atlas")
        assert trainer1 is trainer2

    def test_registry_all_trainers_retrievable_by_id(self):
        """Verify all trainers from get_all_trainers are retrievable by ID."""
        registry = TrainerRegistry()
        all_trainers = registry.get_all_trainers()
        for trainer in all_trainers:
            retrieved = registry.get_trainer(trainer.trainer_id)
            assert retrieved is trainer

    def test_registry_api_list_matches_get_all(self):
        """Verify API list count matches get_all_trainers count."""
        registry = TrainerRegistry()
        all_trainers = registry.get_all_trainers()
        api_list = registry.list_trainers_for_api()
        assert len(all_trainers) == len(api_list)
