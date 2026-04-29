"""Tests for Firebase Admin initialization helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.core.firebase import _load_service_account_json, init_firebase


def test_load_service_account_json_normalizes_literal_newlines_in_private_key() -> None:
    """Firebase env JSON with literal private_key newlines should still parse."""
    raw = (
        '{"type":"service_account","project_id":"demo","private_key_id":"abc",'
        '"private_key":"-----BEGIN PRIVATE KEY-----\n'
        'line1\nline2\n-----END PRIVATE KEY-----\n",'
        '"client_email":"demo@example.com"}'
    )

    parsed = _load_service_account_json(raw)

    assert parsed["project_id"] == "demo"
    assert parsed["private_key"].count("\n") == 4


def test_init_firebase_uses_normalized_json_credentials() -> None:
    """The Firebase initializer must pass normalized credentials to Certificate."""
    raw = (
        '{"type":"service_account","project_id":"demo","private_key_id":"abc",'
        '"private_key":"-----BEGIN PRIVATE KEY-----\nline1\n-----END PRIVATE KEY-----\n",'
        '"client_email":"demo@example.com"}'
    )

    with patch("src.core.firebase.settings") as mock_settings, patch(
        "src.core.firebase.get_app", side_effect=ValueError("missing app")
    ), patch("src.core.firebase.initialize_app") as mock_initialize_app, patch(
        "src.core.firebase.credentials.Certificate"
    ) as mock_certificate:
        mock_settings.FIREBASE_CREDENTIALS = raw
        mock_certificate.return_value = MagicMock()

        init_firebase()

    mock_certificate.assert_called_once()
    mock_initialize_app.assert_called_once()
