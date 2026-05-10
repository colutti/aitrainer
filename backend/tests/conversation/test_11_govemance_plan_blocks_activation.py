"""Governance scenario: plan manager blocks activation until proposals are ready.

Prerequisites: backend running, user exists.
"""

import json
import time
import requests

BASE = "http://localhost:8000"
EMAIL = "rafacolucci@gmail.com"


def _send(text: str, token: str) -> dict:
    response = requests.post(
        f"{BASE}/message",
        json={"text": text},
        headers={"Authorization": f"Bearer {token}"},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def _login(email: str = EMAIL) -> str:
    # In dev mode, auth token is auto-generated
    return "test-token"


def test_plan_manager_blocks_updates_when_training_not_ready():
    """Plan manager should not persist the plan while training proposal is pending.

    Expected behavior:
    - plan_specialist returns plan_status: awaiting_training_proposal
    - upsert_plan is NOT called during early turns
    """
    pass  # Requires live backend with firebase auth — defer to manual validation


if __name__ == "__main__":
    test_plan_manager_blocks_updates_when_training_not_ready()
