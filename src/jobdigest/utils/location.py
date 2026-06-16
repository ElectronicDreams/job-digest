def normalize_location(raw: str | None) -> str:
    """Return a lowercased, stripped location string. None → empty string."""
    if not raw:
        return ""
    return raw.strip().lower()
