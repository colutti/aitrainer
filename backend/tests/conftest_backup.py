import warnings
import pytest

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
