"""
This module contains the models for user profiles and preferences.
"""

from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field, model_validator, computed_field
from src.core.subscription import (
    SubscriptionPlan,
    default_trial_ends_at,
    get_effective_plan_details,
    is_trial_active,
)
from src.utils.date_utils import parse_cycle_start


class UserProfileInput(BaseModel):
    """
    Data class to hold user configuration and profile data for input.
    """

    gender: str = Field(
        ...,
        description="User's gender",
        pattern="^([Mm]asculino|[Ff]eminino|[Mm]ale|[Ff]emale|[Ff]emenino|[Oo]tro|[Oo]ther)$",
    )
    age: int = Field(..., ge=18, le=100, description="Age between 18 and 100 years")
    weight: float | None = Field(
        default=None, ge=30.0, le=500.0, description="Weight in kg between 30 and 500"
    )
    height: int = Field(
        ..., ge=100, le=250, description="Height in cm between 100 and 250"
    )
    goal: str | None = Field(default=None, description="User's goal (legacy)")
    goal_type: str = Field(
        ...,
        pattern="^(lose|gain|maintain)$",
        description="Type of goal: lose, gain, or maintain",
    )
    target_weight: float | None = Field(
        default=None,
        gt=0,
        le=500.0,
        description="Target weight in kg (optional, must be > 0 if set)",
    )
    weekly_rate: float = Field(
        default=0.5,
        ge=0.0,
        le=2.0,
        description="Desired weekly weight change rate in kg",
    )
    notes: str | None = Field(
        default=None, max_length=1000, description="User observations/notes"
    )

    # New V3 Field: Stores compacted history context
    long_term_summary: str | None = Field(
        default=None, description="Stores compacted history context"
    )

    # New V3 Field: Tracks the timestamp of the last message included in the summary
    last_compaction_timestamp: str | None = Field(
        default=None, description="ISO timestamp of the last summarized message"
    )
    # Onboarding status
    onboarding_completed: bool | None = Field(
        default=None, description="Whether the user has completed the onboarding flow"
    )

    @model_validator(mode="after")
    def validate_weekly_rate(self) -> "UserProfileInput":
        """Validates that weekly rate is set if goal is to lose or gain weight."""
        if self.goal_type in ("lose", "gain") and (
            self.weekly_rate is None or self.weekly_rate <= 0
        ):
            raise ValueError(
                "Weekly rate must be greater than 0 for lose or gain goals"
            )
        return self


class UserProfile(UserProfileInput):
    """
    Data class to hold user configuration and profile data.
    """

    email: str = Field(..., description="User's email")
    password_hash: str | None = Field(
        default=None, description="Hashed password for authentication"
    )
    role: str = Field(default="user", description="User role: user or admin")
    is_demo: bool = Field(
        default=False, description="Whether this account is a protected read-only demo"
    )

    # Hevy Integration
    hevy_api_key: str | None = Field(
        default=None, description="Hevy API key, encrypted"
    )
    hevy_enabled: bool = Field(
        default=False, description="Integration enabled/disabled toggle"
    )
    hevy_last_sync: datetime | None = Field(
        default=None, description="Last successful sync timestamp"
    )

    # Telegram Notifications
    telegram_notify_on_workout: bool = Field(
        default=True, description="Send Telegram notification when workout is saved"
    )
    telegram_notify_on_nutrition: bool = Field(
        default=False,
        description="Send Telegram notification when nutrition is logged (future)",
    )
    telegram_notify_on_weight: bool = Field(
        default=False,
        description="Send Telegram notification when weight is logged (future)",
    )

    # User Identity
    display_name: str | None = Field(
        default=None, max_length=50, description="User display name for UI and prompts"
    )
    photo_base64: str | None = Field(
        default=None,
        max_length=700_000,
        description="Profile photo as base64 data URI (max ~500KB)",
    )

    # Subscription and Limits
    subscription_plan: str = Field(
        default="Free", description="Current subscription plan"
    )
    stripe_customer_id: str | None = Field(
        default=None, description="Stripe Customer ID"
    )
    stripe_subscription_id: str | None = Field(
        default=None, description="Active subscription ID"
    )
    stripe_subscription_status: str | None = Field(
        default=None, description="Subscription status from Stripe"
    )
    custom_message_limit: int | None = Field(
        default=None,
        description="Custom monthly message limit override for effective paid capabilities",
    )
    custom_trial_days: int | None = Field(default=None, description="Deprecated field")
    trial_ends_at: datetime | None = Field(
        default_factory=default_trial_ends_at,
        description="Trial end timestamp for Free users",
    )
    messages_sent_this_month: int = Field(
        default=0, description="Messages sent in current billing cycle"
    )
    photos_sent_this_month: int = Field(
        default=0, description="Images sent in current billing cycle"
    )
    total_messages_sent: int = Field(
        default=0, description="Total messages sent by user ever"
    )
    current_billing_cycle_start: datetime | None = Field(
        default=None, description="ISO timestamp of cycle start"
    )
    onboarding_completed: bool | None = Field(
        default=True, description="Whether the user has completed the onboarding flow"
    )

    # Message Tracking
    messages_sent_today: int = Field(default=0, description="Messages sent today")
    last_message_date: str | None = Field(
        default=None, description="ISO Date of last message sent"
    )

    # Coaching Check-in (TDEE)
    tdee_last_target: int | None = Field(
        default=None, description="Last recommended daily calorie target"
    )
    tdee_last_check_in: str | None = Field(
        default=None, description="ISO date of last coaching check-in"
    )
    tdee_activity_factor: float | None = Field(
        default=None,
        ge=1.2,
        le=1.9,
        description="Activity factor for TDEE prior (AI-adjustable). "
        "None = use system default (1.45). "
        "Range: 1.2 (sedentary) to 1.9 (extremely active).",
    )
    timezone: str | None = Field(
        default=None, max_length=50, description="IANA timezone e.g. Europe/Madrid"
    )
    tdee_start_date: str | None = Field(
        default=None,
        description="ISO Date string to start TDEE EMA calculation from (format: YYYY-MM-DD)",
    )

    @model_validator(mode="after")
    def normalize_trial_for_pro(self) -> "UserProfile":
        """Paid users do not need a trial end timestamp."""
        if self.subscription_plan == SubscriptionPlan.PRO:
            self.trial_ends_at = None
        return self

    @computed_field
    @property
    def trial_remaining_days(self) -> int | None:
        """Calculates remaining days in the trial period."""
        if self.subscription_plan == SubscriptionPlan.PRO:
            return None
        if not self.trial_ends_at:
            return 0
        now = datetime.now(timezone.utc)
        trial_end = (
            self.trial_ends_at.replace(tzinfo=timezone.utc)
            if self.trial_ends_at.tzinfo is None
            else self.trial_ends_at
        )
        remaining = (trial_end - now).days
        return max(0, remaining)

    @computed_field
    @property
    def is_trial_active(self) -> bool:
        """Whether the user still has active trial capabilities."""
        return is_trial_active(self.trial_ends_at)

    @computed_field
    @property
    def effective_plan_name(self) -> str:
        """Effective plan label after applying trial override."""
        return get_effective_plan_details(
            self.subscription_plan, self.trial_ends_at
        ).name

    @computed_field
    @property
    def effective_chat_enabled(self) -> bool:
        """Whether chat is effectively enabled for the current user state."""
        return get_effective_plan_details(
            self.subscription_plan, self.trial_ends_at
        ).chat_enabled

    @computed_field
    @property
    def current_daily_limit(self) -> int | None:
        """Deprecated field maintained for API compatibility."""
        return None

    @computed_field
    @property
    def current_plan_limit(self) -> int | None:
        """Current effective monthly message limit."""
        details = get_effective_plan_details(self.subscription_plan, self.trial_ends_at)
        if details.monthly_message_limit is None:
            return None
        if self.custom_message_limit is not None:
            return self.custom_message_limit
        return details.monthly_message_limit

    @computed_field
    @property
    def effective_remaining_messages(self) -> int | None:
        """Calculates how many messages the user can still send."""
        details = get_effective_plan_details(self.subscription_plan, self.trial_ends_at)
        if not details.chat_enabled:
            return 0

        now = datetime.now(timezone.utc)
        is_cycle_reset = False
        if self.current_billing_cycle_start:
            cycle_start = parse_cycle_start(self.current_billing_cycle_start, now)
            if now - cycle_start >= timedelta(days=30):
                is_cycle_reset = True

        message_limit = self.current_plan_limit
        if message_limit is None:
            return None
        sent_this_month = 0 if is_cycle_reset else self.messages_sent_this_month
        return max(0, message_limit - sent_this_month)

    @computed_field
    @property
    def effective_remaining_photos(self) -> int | None:
        """Calculates how many images can still be sent in this cycle."""
        details = get_effective_plan_details(self.subscription_plan, self.trial_ends_at)
        if not details.image_input_enabled:
            return 0

        now = datetime.now(timezone.utc)
        is_cycle_reset = False
        if self.current_billing_cycle_start:
            cycle_start = parse_cycle_start(self.current_billing_cycle_start, now)
            if now - cycle_start >= timedelta(days=30):
                is_cycle_reset = True

        limit = details.monthly_photo_limit
        if limit is None:
            return None
        sent_this_month = 0 if is_cycle_reset else self.photos_sent_this_month
        return max(0, limit - sent_this_month)

    def _goal_type_label(self) -> str:
        labels = {
            "lose": "Perder peso",
            "gain": "Ganhar massa",
            "maintain": "Manter peso",
        }
        return labels.get(self.goal_type, self.goal_type)

    def get_profile_summary(self) -> str:
        """
        Generates a summary of the user's profile for use in prompts.

        Returns:
            str: Formatted summary of the user's profile as key-value pairs.
        """
        name_line = f"**Nome:** {self.display_name}\n" if self.display_name else ""
        weight_line = f"**Peso Inicial:** {self.weight}kg\n" if self.weight else ""
        return (
            f"{name_line}"
            f"**Gênero:** {self.gender}\n"
            f"**Idade:** {self.age} anos\n"
            f"{weight_line}"
            f"**Altura:** {self.height}cm\n"
            f"**Tipo de Objetivo:** {self._goal_type_label()}\n"
            f"**Taxa Semanal:** {self.weekly_rate}kg/semana\n"
            f"**Observações:** {self.notes or 'Nenhuma'}"
        )
