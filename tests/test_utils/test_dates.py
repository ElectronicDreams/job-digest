from datetime import datetime, timezone

from jobdigest.utils.dates import parse_date


def test_iso8601_with_z_suffix():
    dt = parse_date("2024-03-15T12:30:00Z")
    assert dt == datetime(2024, 3, 15, 12, 30, 0, tzinfo=timezone.utc)


def test_iso8601_with_offset():
    dt = parse_date("2024-03-15T12:30:00+05:00")
    assert dt is not None
    assert dt.utcoffset() is not None


def test_iso8601_no_timezone_assumes_utc():
    dt = parse_date("2024-03-15T12:30:00")
    assert dt is not None
    assert dt.tzinfo == timezone.utc


def test_date_only():
    dt = parse_date("2024-03-15")
    assert dt == datetime(2024, 3, 15, 0, 0, 0, tzinfo=timezone.utc)


def test_rfc2822():
    dt = parse_date("Mon, 15 Jan 2024 10:00:00 +0000")
    assert dt is not None
    assert dt.year == 2024
    assert dt.month == 1
    assert dt.day == 15


def test_none_returns_none():
    assert parse_date(None) is None


def test_empty_string_returns_none():
    assert parse_date("") is None


def test_invalid_string_returns_none():
    assert parse_date("not a date at all") is None


def test_result_is_always_timezone_aware():
    for raw in (
        "2024-01-01T00:00:00Z",
        "2024-01-01",
        "Mon, 01 Jan 2024 00:00:00 +0000",
    ):  # noqa: E501
        dt = parse_date(raw)
        assert dt is not None
        assert dt.tzinfo is not None, f"Expected tz-aware for {raw!r}"
