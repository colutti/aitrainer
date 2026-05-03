"""Test T03: Perder peso - "ate o fim do ano"."""
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


def test_perder_peso():
    """3 mensagens, meta emagrecimento, prazo fim do ano."""
    _reset()
    time.sleep(2)
    token = _login()

    for msg in [
        "bom dia",
        "quero emagrecer, posso treinar seg, qua, sex, 50 min cada",
        "ate o fim do ano, sem lesoes, academia normal",
    ]:
        _send(token, msg)
        time.sleep(WAIT)

    time.sleep(5)
    plan = _get_plan(token)

    assert plan.get("title"), f"No title: {json.dumps(plan, indent=2)[:500]}"
    target = plan["timeline"]["target_date"]
    assert "2026-12" in target, f"Expected December 2026 target, got {target}"
    goal = plan["goal"]["primary"]
    assert goal in ("lose_fat",), f"Expected lose_fat goal, got {goal}"
    assert plan["training_program"]["frequency_per_week"] == 3
    assert plan["training_program"]["session_duration_min"] == 50
