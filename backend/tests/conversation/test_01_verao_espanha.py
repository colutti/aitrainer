"""Test T01: Verão da Espanha - info espalhada em 4 mensagens."""
import json
import subprocess
import time

import requests

BASE = "http://localhost:8000"
EMAIL = "rafacolucci@gmail.com"
WAIT = 5  # segundos entre turnos


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


def test_verao_espanha_4msg():
    """4 mensagens, dados espalhados entre turnos."""
    _reset()
    time.sleep(2)
    token = _login()

    for msg in [
        "ola bom dia",
        "eu quero ganhar massa e posso treinar seg, terca, quarta, sexta e sabado",
        "ate o verao da espanha, nao tenho nenhuma restricao a nada, treino em academia normal",
        "60 minutos",
    ]:
        _send(token, msg)
        time.sleep(WAIT)

    time.sleep(5)
    plan = _get_plan(token)

    assert plan.get("title"), f"No title: {json.dumps(plan, indent=2)[:500]}"
    target = plan["timeline"]["target_date"]
    assert "2026-06" in target, f"Expected June 2026 target, got {target}"
    assert plan["training_program"]["frequency_per_week"] == 5
    assert plan["training_program"]["session_duration_min"] == 60
