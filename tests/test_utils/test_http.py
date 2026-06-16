from unittest.mock import MagicMock, patch

import pytest
import requests

from jobdigest.utils.http import get_json


def _resp(status: int, data: dict | list | None = None) -> MagicMock:
    r = MagicMock()
    r.status_code = status
    r.json.return_value = data if data is not None else {}
    if status >= 400:
        r.raise_for_status.side_effect = requests.HTTPError(response=r)
    else:
        r.raise_for_status.return_value = None
    return r


def test_success_first_try():
    with patch("jobdigest.utils.http.requests.Session") as MockSession:
        MockSession.return_value.get.return_value = _resp(200, {"jobs": []})
        result = get_json("https://example.com/api")
    assert result == {"jobs": []}
    assert MockSession.return_value.get.call_count == 1


def test_retries_on_5xx_then_succeeds():
    with (
        patch("jobdigest.utils.http.requests.Session") as MockSession,
        patch("jobdigest.utils.http.time.sleep"),
    ):
        MockSession.return_value.get.side_effect = [
            _resp(500),
            _resp(503),
            _resp(200, {"ok": True}),
        ]
        result = get_json("https://example.com/api", retries=3)
    assert result == {"ok": True}
    assert MockSession.return_value.get.call_count == 3


def test_raises_after_all_retries_exhausted():
    with (
        patch("jobdigest.utils.http.requests.Session") as MockSession,
        patch("jobdigest.utils.http.time.sleep"),
    ):
        MockSession.return_value.get.return_value = _resp(503)
        with pytest.raises(RuntimeError, match="retries exhausted"):
            get_json("https://example.com/api", retries=3)
    assert MockSession.return_value.get.call_count == 3


def test_retries_on_timeout_then_succeeds():
    with (
        patch("jobdigest.utils.http.requests.Session") as MockSession,
        patch("jobdigest.utils.http.time.sleep"),
    ):
        MockSession.return_value.get.side_effect = [
            requests.Timeout(),
            _resp(200, {"data": "ok"}),
        ]
        result = get_json("https://example.com/api", retries=3)
    assert result == {"data": "ok"}


def test_retries_on_connection_error():
    with (
        patch("jobdigest.utils.http.requests.Session") as MockSession,
        patch("jobdigest.utils.http.time.sleep"),
    ):
        MockSession.return_value.get.side_effect = [
            requests.ConnectionError(),
            _resp(200, [{"id": 1}]),
        ]
        result = get_json("https://example.com/api")
    assert result == [{"id": 1}]


def test_4xx_raises_immediately_no_retry():
    with patch("jobdigest.utils.http.requests.Session") as MockSession:
        MockSession.return_value.get.return_value = _resp(404)
        with pytest.raises(requests.HTTPError):
            get_json("https://example.com/api")
    assert MockSession.return_value.get.call_count == 1


def test_passes_params_and_headers():
    with patch("jobdigest.utils.http.requests.Session") as MockSession:
        MockSession.return_value.get.return_value = _resp(200, {})
        get_json(  # noqa: E501
            "https://example.com/api", params={"q": "python"}, headers={"X-Key": "val"}
        )
    MockSession.return_value.get.assert_called_once_with(
        "https://example.com/api",
        params={"q": "python"},
        headers={"X-Key": "val"},
        timeout=10,
    )
