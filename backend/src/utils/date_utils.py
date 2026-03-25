"""Date and time utilities."""

from datetime import datetime, timezone


def parse_cycle_start(cycle_start: str | datetime | None, now: datetime) -> datetime:
    """Parses a cycle start date from string or datetime, ensuring it's aware and valid."""
    if cycle_start is None:
        return now

    if isinstance(cycle_start, str):
        try:
            cycle_start = datetime.fromisoformat(cycle_start)
        except ValueError:
            cycle_start = now

    # Ensure cycle_start is aware
    if cycle_start.tzinfo is None:
        cycle_start = cycle_start.replace(tzinfo=timezone.utc)

    return cycle_start
