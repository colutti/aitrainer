"""Regression tests for the production env sync script."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_deploy_prod_env_sync_rejects_placeholder_values(tmp_path: Path) -> None:
    """Reject placeholder env values before they reach Cloud Run."""
    env_file = tmp_path / "backend.env.prod"
    env_file.write_text("SECRET_KEY=ok\nMONGO_URI=CHANGE_ME_MONGO_URI\n", encoding="utf-8")

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    gcloud = fake_bin / "gcloud"
    gcloud.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
    gcloud.chmod(0o755)

    result = subprocess.run(
        ["bash", "scripts/deploy/deploy_prod_env.sh"],
        cwd=Path(__file__).resolve().parents[2],
        env={
            **os.environ,
            "PATH": f"{fake_bin}:{os.environ['PATH']}",
            "ENV_BACKEND_FILE": str(env_file),
            "ENV_FRONTEND_FILE": str(tmp_path / "missing-frontend.env.prod"),
        },
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "placeholder values detected" in result.stderr
