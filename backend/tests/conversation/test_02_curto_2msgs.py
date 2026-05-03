"""Test T02: Curto - 2 mensagens com confirmação explícita."""
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
    ], capture_output=True)


def _login():
    return requests.post(f"{BASE}/user/e2e-login", json={
        "email": EMAIL, "display_name": "Rafael", "onboarding_completed": True,
    }, timeout=30).json()["token"]


def _send(token, msg):
    requests.post(f"{BASE}/message",
                  json={"user_message": msg},
                  headers={"Authorization": f"Bearer {token}"},
                  timeout=120)


def _get_plan(token):
    return requests.get(f"{BASE}/plan",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=30).json()


def test_curto_2msgs():
    """2 mensagens: info + "pode criar"."""
    _reset()
    time.sleep(2)
    token = _login()

    for msg in [
        "ola, quero ganhar massa e treino seg, qua, sex, 60 min cada, sem restricoes",
        "quero resultado em 4 meses, pode criar o plano",
    ]:
        _send(token, msg)
        time.sleep(WAIT)

    time.sleep(5)
    plan = _get_plan(token)

    assert plan.get("title"), f"No title: {json.dumps(plan, indent=2)[:500]}"
    freq = plan["training_program"]["frequency_per_week"]
    assert freq == 3, f"Expected 3x/week, got {freq}"
    assert plan["training_program"]["session_duration_min"] == 60
