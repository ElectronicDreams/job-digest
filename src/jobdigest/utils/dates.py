from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


def parse_date(raw: str | None) -> datetime | None:
    """Parse a date string into a timezone-aware datetime.

    Handles ISO 8601 (with or without Z / offset) and RFC 2822 (RSS).
    Returns None for missing or unparseable input.
    """
    if not raw:
        return None

    # Normalise Z suffix so fromisoformat works on Python 3.10
    normalized = raw.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        pass

    # RFC 2822 (e.g. "Mon, 01 Jan 2024 00:00:00 +0000" from RSS feeds)
    try:
        return parsedate_to_datetime(raw)
    except Exception:
        pass

    # Date-only fallback (YYYY-MM-DD)
    try:
        dt = datetime.strptime(raw[:10], "%Y-%m-%d")
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None
