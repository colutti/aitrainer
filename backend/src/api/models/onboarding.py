"""
Models for onboarding flow.
"""

from pydantic import BaseModel, EmailStr, Field, model_validator


class OnboardingCompleteRequest(BaseModel):
    """
    Request model for completing onboarding.
    """

    token: str = Field(..., description="Invite token")
    password: str = Field(..., min_length=8, description="User password")
    gender: str = Field(..., pattern="^(Masculino|Feminino)$")
    age: int = Field(..., ge=18, le=100)
    weight: float = Field(..., ge=30.0, le=500.0, description="Weight in kg")
    height: int = Field(..., ge=100, le=250, description="Height in cm")
    goal_type: str = Field(..., pattern="^(lose|gain|maintain)$")
    weekly_rate: float = Field(
        0.5, ge=0.0, le=2.0, description="Weekly change rate in kg"
    )
    trainer_type: str = Field(
        default="atlas",
        pattern="^(atlas|luna|sargento|sofia)$",
        description="Selected trainer type",
    )

    @model_validator(mode="after")
    def validate_password_strength(self) -> "OnboardingCompleteRequest":
        """
        Validates password meets security requirements:
        - Min 8 characters
        - At least 1 uppercase
        - At least 1 lowercase
        - At least 1 digit
        """
        password = self.password

        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one digit")

        return self


class OnboardingValidateResponse(BaseModel):
    """
    Response model for token validation.
    """

    valid: bool = Field(..., description="Whether token is valid")
    email: EmailStr | None = Field(None, description="Email if valid")
    reason: str | None = Field(None, description="Reason if invalid")


class OnboardingCompleteResponse(BaseModel):
    """
    Response model for completing onboarding.
    """

    token: str = Field(..., description="JWT authentication token")
    message: str = Field(..., description="Success message")
