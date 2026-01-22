import sys
import warnings

# Suppress Pydantic V1 compatibility warnings from langchain on Python 3.14+
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_core")

from urllib.parse import urlparse  # noqa: E402
from src.core.config import settings  # noqa: E402


def confirm_execution(script_name: str, additional_info: dict = None):
    """
    Displays a safety check banner and waits for user confirmation.
    """
    print("\n" + "!" * 60)
    print(f"⚠️  SAFETY CHECK: {script_name}")
    print("!" * 60)

    # Target Database Info
    try:
        parsed = urlparse(settings.MONGO_URI)
        host = parsed.hostname
        port = parsed.port
        # Mask credentials
        masked_uri = (
            f"{parsed.scheme}://{parsed.username}:****@{host}:{port}/{settings.DB_NAME}"
        )
    except Exception:
        masked_uri = "Unknown / Parse Error"

    print(f"🎯 TARGET DATABASE: {masked_uri}")
    print(f"📁 PROJECT ROOT:   {settings.model_config.get('env_file', '.env')}")

    if additional_info:
        for key, value in additional_info.items():
            print(f"ℹ️  {key.upper()}: {value}")

    print("-" * 60)

    # Special warning if NOT localhost
    if "localhost" not in masked_uri and "127.0.0.1" not in masked_uri:
        print("🛑 WARNING: You are connecting to a REMOTE/CLOUD database!")
        print("!" * 60)

    confirm = input("\nDo you want to proceed? Type 'OK' to continue: ")
    if confirm.strip().upper() != "OK":
        print("\n❌ Execution cancelled by user.")
        sys.exit(0)

    print("\n🚀 Proceeding with execution...\n")
