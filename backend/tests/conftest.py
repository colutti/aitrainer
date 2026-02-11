import warnings
import pytest
import unittest
import unittest.mock

# Filter warnings immediately upon import
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Specific filters for stubborn libraries
warnings.filterwarnings("ignore", module="slowapi")
warnings.filterwarnings("ignore", module="langsmith")
warnings.filterwarnings("ignore", module="google.genai")
warnings.filterwarnings("ignore", message=".*migrating_memory.*")
warnings.filterwarnings("ignore", message=".*_UnionGenericAlias.*")
warnings.filterwarnings("ignore", message=".*Core Pydantic V1 functionality.*")

from src.core import deps  # noqa: E402

@pytest.fixture(scope="session", autouse=True)
def cleanup_resources():
    """Cleanup resources after all tests in the session."""
    yield
    # Clear lru_caches
    deps.get_mongo_database.cache_clear()
    deps.get_mem0_client.cache_clear()
    deps.get_qdrant_client.cache_clear()
    deps.get_llm_client.cache_clear()


@pytest.fixture(autouse=True)
def mock_dependencies():
    """
    Globally mock all external dependencies to prevent accidental connections.
    This fixture runs automatically for every test.
    """
    with unittest.mock.patch("src.core.deps.get_mongo_database") as mock_db, \
         unittest.mock.patch("src.core.deps.get_mem0_client") as mock_mem0, \
         unittest.mock.patch("src.core.deps.get_qdrant_client") as mock_qdrant, \
         unittest.mock.patch("src.core.deps.get_llm_client") as mock_llm, \
         unittest.mock.patch("pymongo.MongoClient") as mock_mongo:
        
        # Configure mocks to provide safe mocks that don't connect.
        mock_db.return_value = unittest.mock.MagicMock()
        mock_mem0.return_value = unittest.mock.MagicMock()
        mock_qdrant.return_value = unittest.mock.MagicMock()
        mock_llm.return_value = unittest.mock.MagicMock()
        mock_mongo.return_value = unittest.mock.MagicMock()
        
        yield

