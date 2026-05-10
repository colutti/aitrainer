"""Test T11: governance gate blocks activation until training proposal is ready."""

import json
import subprocess
import time

import requests

BASE = "http://localhost:8000"
EMAIL = "rafacolucci@gmail.com"
WAIT = 5


def _reset():
    subprocess.run([
        "podman", "exec", "fityq-dev_backend_1", "python3",
        "/app/scripts/reset_user_data.py",
        "--email", EMAIL, "--confirm",
    ], capture_output=True, check=False)


def _login():
    return requests.post(f"{BASE}/user/e2e-login", json={
        "email": EMAIL, "display_name": "Rafael", "onboarding_completed": True,
    }, timeout=30).json()["token"]


def _send(token, msg):
    requests.post(f"{BASE}/message",
                  json={"user_message": msg},
                  headers={"Authorization": f"Bearer {token}"},
                  timeout=120)


def test_governance_blocks_activation_until_training_ready():
    """Partial anamnesis must not activate the plan; full anamnesis may activate it."""
    _reset()
    time.sleep(2)
    token = _login()

    for msg in [
        "oi",
        "quero criar um plano de treino",
        "quero ganhar massa, treino em casa com halteres, 6x por semana, 60 minutos",
    ]:
        _send(token, msg)
        time.sleep(WAIT)

    partial_resp = requests.get(
        f"{BASE}/plan",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    assert partial_resp.status_code == 404, (
        "plan must stay blocked while anamnesis is incomplete; "
        f"got status={partial_resp.status_code}, body={partial_resp.text[:300]}"
    )

    for msg in [
        "tenho 1 ano de experiencia, sem lesoes, gosto de supino e agachamento",
        "odeio stiff, durmo bem, estresse baixo",
    ]:
        _send(token, msg)
        time.sleep(WAIT)

    final_resp = requests.get(
        f"{BASE}/plan",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    assert final_resp.status_code == 200, (
        "plan should be creatable after complete anamnesis; "
        f"got status={final_resp.status_code}, body={final_resp.text[:300]}"
    )
    plan = final_resp.json()
    assert plan.get("title"), f"missing title: {json.dumps(plan, indent=2)[:500]}"
    assert plan["training_program"]["frequency_per_week"] == 6
    assert plan["training_program"]["session_duration_min"] == 60
