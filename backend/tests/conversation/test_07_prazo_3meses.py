"""Test T07: Prazo curto - "3 meses"."""
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


def test_prazo_3meses():
    """3 mensagens, objetivo musculo, prazo relativo 3 meses."""
    _reset()
    time.sleep(2)
    token = _login()

    for msg in [
        "oi",
        "quero ganhar musculo, treino 4x na semana, 45 min cada sessao, sem restricoes",
        "prazo de 3 meses",
    ]:
        _send(token, msg)
        time.sleep(WAIT)

    time.sleep(5)
    plan = _get_plan(token)

    assert plan.get("title"), f"No title: {json.dumps(plan, indent=2)[:500]}"
    target = plan["timeline"]["target_date"]
    assert "2026-08" in target, f"Expected August 2026 target, got {target}"
    assert plan["training_program"]["frequency_per_week"] == 4
    assert plan["training_program"]["session_duration_min"] == 45
