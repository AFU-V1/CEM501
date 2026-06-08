"""Project-wide time helpers.

All user-facing times are normalized to Turkey time (Europe/Istanbul).
"""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo


TR_TZ = ZoneInfo("Europe/Istanbul")
DISPLAY_FORMAT = "%Y-%m-%d %H:%M:%S"


def tr_now() -> datetime:
    """Return the current time in Turkey time."""
    return datetime.now(TR_TZ)


def tr_now_string() -> str:
    """Return a display/storage timestamp in Turkey time."""
    return tr_now().strftime(DISPLAY_FORMAT)


def parse_to_tr_datetime(value: str | None) -> datetime | None:
    """Parse common email/app timestamps and normalize them to Turkey time."""
    if not value:
        return None

    text = str(value).strip()
    parsers = [
        lambda candidate: parsedate_to_datetime(candidate),
        lambda candidate: datetime.fromisoformat(candidate),
        lambda candidate: datetime.strptime(candidate, DISPLAY_FORMAT),
        lambda candidate: datetime.strptime(candidate, "%Y-%m-%d"),
    ]

    for parser in parsers:
        try:
            parsed = parser(text)
        except (TypeError, ValueError, IndexError, OverflowError):
            continue

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=TR_TZ)
        return parsed.astimezone(TR_TZ)

    return None


def format_tr_datetime(value: str | None) -> str:
    """Format a timestamp-like value for display in Turkey time."""
    parsed = parse_to_tr_datetime(value)
    if not parsed:
        return str(value or "")
    return parsed.strftime(DISPLAY_FORMAT)


def sqlite_utc_to_tr_string(value: str | None) -> str:
    """Convert SQLite CURRENT_TIMESTAMP strings from UTC to Turkey time."""
    if not value:
        return tr_now_string()

    text = str(value).strip()
    try:
        parsed = datetime.strptime(text, DISPLAY_FORMAT).replace(tzinfo=timezone.utc)
    except ValueError:
        return format_tr_datetime(text)

    return parsed.astimezone(TR_TZ).strftime(DISPLAY_FORMAT)
