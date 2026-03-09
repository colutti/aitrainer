from fastapi.testclient import TestClient
from src.api.main import app
from unittest.mock import patch, MagicMock

client = TestClient(app)

@patch("stripe.Webhook.construct_event")
def test_webhook_invalid_signature(mock_construct):
    import stripe
    mock_construct.side_effect = stripe.error.SignatureVerificationError("Invalid", "sig", "payload")
    response = client.post("/stripe/webhook", json={}, headers={"Stripe-Signature": "invalid"})
    assert response.status_code == 400
