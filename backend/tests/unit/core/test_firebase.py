from unittest.mock import patch

from src.core.firebase import init_firebase


@patch("src.core.firebase.initialize_app")
@patch("src.core.firebase.credentials.Certificate")
@patch("src.core.firebase.settings")
def test_init_firebase_accepts_json_credentials(
    mock_settings,
    mock_certificate,
    mock_initialize,
):
    mock_settings.FIREBASE_CREDENTIALS = '{"type":"service_account","project_id":"demo"}'

    init_firebase()

    mock_certificate.assert_called_once_with(
        {"type": "service_account", "project_id": "demo"}
    )
    mock_initialize.assert_called_once()


@patch("src.core.firebase.logger")
@patch("src.core.firebase.settings")
def test_init_firebase_logs_warning_when_credentials_are_missing(
    mock_settings,
    mock_logger,
):
    mock_settings.FIREBASE_CREDENTIALS = ""

    init_firebase()

    mock_logger.warning.assert_called_once()
