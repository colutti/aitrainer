from unittest.mock import patch, MagicMock
from src.services.stripe import create_checkout_session
from src.api.models.user_profile import UserProfile

@patch("stripe.checkout.Session.create")
def test_create_checkout_session(mock_create):
    mock_create.return_value = MagicMock(url="https://checkout.stripe.com/pay")
    user = UserProfile(
        email="test@example.com", gender="Masculino", age=30, height=170, goal_type="maintain",
        stripe_customer_id="cus_123"
    )
    url = create_checkout_session(user, "price_123", "http://localhost:3000/success", "http://localhost:3000/cancel")
    
    assert url == "https://checkout.stripe.com/pay"
    mock_create.assert_called_once()
    args, kwargs = mock_create.call_args
    assert kwargs["customer"] == "cus_123"
