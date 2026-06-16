from unittest.mock import MagicMock, patch

from jobdigest.utils.rss import parse_feed

_FIXTURE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>Senior Python Developer</title>
      <link>https://example.com/jobs/1</link>
      <description>Remote Python role.</description>
    </item>
    <item>
      <title>Frontend Engineer</title>
      <link>https://example.com/jobs/2</link>
    </item>
  </channel>
</rss>"""


def _mock_feed(entries: list[dict]) -> MagicMock:
    feed = MagicMock()
    feed.entries = entries
    return feed


def test_parse_feed_returns_entries():
    with patch("jobdigest.utils.rss.feedparser.parse") as mock_parse:
        mock_parse.return_value = _mock_feed(
            [
                {
                    "title": "Senior Python Developer",
                    "link": "https://example.com/jobs/1",
                },
                {"title": "Frontend Engineer", "link": "https://example.com/jobs/2"},
            ]
        )
        result = parse_feed("https://example.com/feed.rss")
    assert len(result) == 2
    assert result[0]["title"] == "Senior Python Developer"
    assert result[1]["link"] == "https://example.com/jobs/2"


def test_parse_feed_returns_dicts():
    with patch("jobdigest.utils.rss.feedparser.parse") as mock_parse:
        mock_parse.return_value = _mock_feed([{"title": "Job"}])
        result = parse_feed("https://example.com/feed.rss")
    assert isinstance(result[0], dict)


def test_parse_feed_empty_feed():
    with patch("jobdigest.utils.rss.feedparser.parse") as mock_parse:
        mock_parse.return_value = _mock_feed([])
        result = parse_feed("https://example.com/feed.rss")
    assert result == []


def test_parse_feed_returns_empty_on_exception():
    with patch(  # noqa: E501
        "jobdigest.utils.rss.feedparser.parse", side_effect=Exception("network error")
    ):
        result = parse_feed("https://example.com/feed.rss")
    assert result == []
