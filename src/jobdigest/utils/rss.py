import feedparser


def parse_feed(url: str) -> list[dict]:
    """Fetch and parse an RSS/Atom feed, returning entries as plain dicts.

    Returns an empty list on any error — a broken feed never crashes the pipeline.
    """
    try:
        feed = feedparser.parse(url)
        return [dict(entry) for entry in feed.entries]
    except Exception:
        return []
