"""
This module contains the models for user profiles and preferences.
"""

from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field, model_validator, computed_field
from src.core.subscription import SUBSCRIPTION_PLANS, SubscriptionPlan
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
    hevy_webhook_token: str | None = Field(
        default=None, description="Unique token for webhook URL path"
    )
    hevy_webhook_secret: str | None = Field(
        default=None, description="Secret for Authorization header validation"
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
        description="Custom limit override (daily for Free, monthly for paid)",
    )
    custom_trial_days: int | None = Field(
        default=None, description="Custom validity days override"
    )
    messages_sent_this_month: int = Field(
        default=0, description="Messages sent in current billing cycle"
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

    @computed_field
    @property
    def trial_remaining_days(self) -> int | None:
        """Calculates remaining days in the trial period."""
        try:
            plan_name = SubscriptionPlan(self.subscription_plan)
        except (ValueError, AttributeError):
            plan_name = SubscriptionPlan.FREE
        plan = SUBSCRIPTION_PLANS[plan_name]
        # Admin Override for validity
        v_days = (
            self.custom_trial_days
            if self.custom_trial_days is not None
            else plan.validity_days
        )
        if v_days is None:
            return None
        if not self.current_billing_cycle_start:
            return v_days

        now = datetime.now(timezone.utc)
        cycle_start = parse_cycle_start(self.current_billing_cycle_start, now)

        elapsed = (now - cycle_start).days
        remaining = v_days - elapsed
        return max(0, remaining)

    @computed_field
    @property
    def current_daily_limit(self) -> int | None:
        """Returns the daily message limit for the current plan."""
        try:
            plan_name = SubscriptionPlan(self.subscription_plan)
        except (ValueError, AttributeError):
            plan_name = SubscriptionPlan.FREE
        plan = SUBSCRIPTION_PLANS[plan_name]
        # If it's a daily plan (Free), the custom limit overrides the daily limit
        if plan.daily_limit is not None:
            c_lim = self.custom_message_limit
            return c_lim if c_lim is not None else plan.daily_limit
        return None

    @computed_field
    @property
    def current_plan_limit(self) -> int | None:
        """Returns the message limit for the plan (daily for Free, monthly for others)."""
        try:
            plan_name = SubscriptionPlan(self.subscription_plan)
        except (ValueError, AttributeError):
            plan_name = SubscriptionPlan.FREE
        plan = SUBSCRIPTION_PLANS[plan_name]

        # Priority: Custom limit > Plan limit (Daily or Monthly)
        if self.custom_message_limit is not None:
            return self.custom_message_limit

        if plan.daily_limit is not None:
            return plan.daily_limit

        if plan.monthly_limit is not None:
            return plan.monthly_limit

        return None

    @computed_field
    @property
    def effective_remaining_messages(self) -> int | None:
        """Calculates how many messages the user can still send."""
        try:
            plan_name = SubscriptionPlan(self.subscription_plan)
        except (ValueError, AttributeError):
            plan_name = SubscriptionPlan.FREE
        plan = SUBSCRIPTION_PLANS[plan_name]

        # Check for billing cycle reset (30 days)
        now = datetime.now(timezone.utc)
        is_cycle_reset = False
        if self.current_billing_cycle_start:
            cycle_start = parse_cycle_start(self.current_billing_cycle_start, now)

            if now - cycle_start >= timedelta(days=30):
                is_cycle_reset = True

        # Check Validity / Trial Expiration
        v_days = (
            self.custom_trial_days
            if self.custom_trial_days is not None
            else plan.validity_days
        )
        if v_days is not None:
            if self.trial_remaining_days is not None and self.trial_remaining_days <= 0:
                return 0

        # Daily Limit Logic (Overrides for Free)
        if plan.daily_limit is not None:
            d_lim = (
                self.custom_message_limit
                if self.custom_message_limit is not None
                else plan.daily_limit
            )
            # Check for daily reset
            today_str = now.strftime("%Y-%m-%d")
            sent_today = (
                self.messages_sent_today if self.last_message_date == today_str else 0
            )
            return max(0, d_lim - sent_today)

        # Monthly Limit Logic (Overrides for Paid)
        if plan.monthly_limit is not None:
            m_lim = (
                self.custom_message_limit
                if self.custom_message_limit is not None
                else plan.monthly_limit
            )
            sent_this_month = 0 if is_cycle_reset else self.messages_sent_this_month
            return max(0, m_lim - sent_this_month)
        return None

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
