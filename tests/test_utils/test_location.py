from jobdigest.utils.location import normalize_location


def test_lowercases():
    assert normalize_location("Toronto, ON") == "toronto, on"


def test_strips_whitespace():
    assert normalize_location("  Remote  ") == "remote"


def test_none_returns_empty_string():
    assert normalize_location(None) == ""


def test_empty_string_returns_empty_string():
    assert normalize_location("") == ""


def test_already_lowercase_unchanged():
    assert normalize_location("new york") == "new york"


def test_mixed_case_and_whitespace():
    assert normalize_location("  New York, NY  ") == "new york, ny"
