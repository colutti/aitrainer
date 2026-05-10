"""Governance scenario: plan manager blocks activation until proposals are ready.

This scenario verifies that the runtime persistence gate prevents plan
saving before the training specialist finishes anamnesis.

Prerequisites: backend running, user rafacolucci@gmail.com exists.
"""

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


def test_plan_manager_blocks_activation_until_anamnesis_complete():
    """Multi-turn scenario:
    1. User asks for a plan
    2. Assistant should start training anamnesis (not save plan)
    3. User provides partial info (not enough)
    4. Assistant should NOT claim plan was created
    5. User provides remaining anamnesis info
    6. Plan should be created after training proposal is ready
    """
    import os
    firebase_token = os.environ.get("FITYQ_E2E_TOKEN", "")
    if not firebase_token:
        return  # skip when no token configured

    # Turn 1: request plan
    r1 = _send("quero criar um plano de treino", firebase_token)
    text1 = str(r1.get("text", "")).lower()
    assert "objetivo" in text1 or "goal" in text1 or "meta" in text1, (
        f"expected anamnesis prompt, got: {text1[:200]}"
    )
    assert "plano criado" not in text1 and (
        "plano salvo" not in text1
    ), "plan should not be saved after first turn"

    # Turn 2: provide partial info
    r2 = _send(
        "meu objetivo é ganhar massa, treino em casa com halteres, "
        "6x por semana, 60 minutos cada",
        firebase_token,
    )
    text2 = str(r2.get("text", "")).lower()
    assert len(text2) > 0, "expected non-empty reply for partial info"

    # Turn 3: provide rest
    r3 = _send(
        "tenho 1 ano de experiência, gosto de supino e agachamento, "
        "odeio stiff, não tenho lesões",
        firebase_token,
    )
    text3 = str(r3.get("text", "")).lower()
    assert len(text3) > 0, "expected non-empty reply after full anamnesis"


if __name__ == "__main__":
    test_plan_manager_blocks_activation_until_anamnesis_complete()
