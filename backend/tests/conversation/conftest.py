import shutil
import subprocess
import pytest


def podman_available() -> bool:
    if not shutil.which("podman"):
        return False
    result = subprocess.run(
        ["podman", "ps", "--filter", "name=fityq-dev_backend_1", "--format", "{{.Names}}"],
        capture_output=True, text=True, check=False,
    )
    return "fityq-dev_backend_1" in result.stdout


if not podman_available():
    pytest.skip("podman or fityq-dev_backend_1 container not available", allow_module_level=True)
