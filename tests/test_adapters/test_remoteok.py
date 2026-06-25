import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from jobdigest.adapters.remoteok import RemoteOkSource
from jobdigest.config import Config, LLMConfig

_FIXTURE = json.loads(
    (Path(__file__).parent.parent / "fixtures" / "remoteok_jobs.json").read_text()
)

_LLM = LLMConfig(
    provider="test",
    base_url="https://example.com",
    model="test-model",
    api_key_env="TEST_KEY",
)


def _config(recency_hours: int = 72) -> Config:
    return Config(
        recency_hours=recency_hours,
        min_score=50,
        output_dir=Path("./output"),
        enabled_sources=["remoteok"],
        weights={},
        onboarding_llm=_LLM,
        daily_llm_scoring={"enabled": False, "model": None},
        log_level="INFO",
        exclusion_phrases=[],
    )


def test_fetch_happy_path_returns_jobs():
    with patch("jobdigest.adapters.remoteok.get_json", return_value=_FIXTURE):
        result = RemoteOkSource(_config()).fetch()
    assert len(result) == 2
    assert result[0].source == "remoteok"
    assert result[0].title == "Senior Backend Engineer"
    assert result[0].company == "Acme Corp"
    assert result[0].url == "https://acme.com/jobs/backend"


def test_fetch_skips_legal_notice():
    with patch("jobdigest.adapters.remoteok.get_json", return_value=_FIXTURE):
        result = RemoteOkSource(_config()).fetch()
    assert all(j.title != "" for j in result)
    assert len(result) == 2


def test_fetch_salary_parsed():
    with patch("jobdigest.adapters.remoteok.get_json", return_value=_FIXTURE):
        result = RemoteOkSource(_config()).fetch()
    assert result[0].salary == {
        "min": 120000,
        "max": 180000,
        "currency": "USD",
        "period": "yearly",
    }


def test_fetch_missing_salary_is_none():
    with patch("jobdigest.adapters.remoteok.get_json", return_value=_FIXTURE):
        result = RemoteOkSource(_config()).fetch()
    assert result[1].salary is None


def test_fetch_employment_type_inferred_from_tags():
    with patch("jobdigest.adapters.remoteok.get_json", return_value=_FIXTURE):
        result = RemoteOkSource(_config()).fetch()
    assert result[0].employment_type == "full-time"
    assert result[1].employment_type == "contract"


def test_fetch_all_jobs_are_remote():
    with patch("jobdigest.adapters.remoteok.get_json", return_value=_FIXTURE):
        result = RemoteOkSource(_config()).fetch()
    assert all(j.is_remote for j in result)


def test_fetch_location_normalized():
    with patch("jobdigest.adapters.remoteok.get_json", return_value=_FIXTURE):
        result = RemoteOkSource(_config()).fetch()
    assert result[0].location == "worldwide"
    assert result[1].location == "usa only"


def test_fetch_date_parsed():
    with patch("jobdigest.adapters.remoteok.get_json", return_value=_FIXTURE):
        result = RemoteOkSource(_config()).fetch()
    assert result[0].posted_date is not None
    assert result[0].posted_date.tzinfo is not None


def test_fetch_empty_list():
    with patch("jobdigest.adapters.remoteok.get_json", return_value=[]):
        result = RemoteOkSource(_config()).fetch()
    assert result == []


def test_fetch_non_list_response_returns_empty():
    with patch("jobdigest.adapters.remoteok.get_json", return_value={"error": "bad"}):
        result = RemoteOkSource(_config()).fetch()
    assert result == []


def test_fetch_recency_filter_inside_window():
    now = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    recent_date = (now - timedelta(hours=1)).isoformat()
    payload = [
        {
            "id": "1",
            "slug": "new-job",
            "url": "https://remoteok.com/1",
            "apply_url": "https://example.com/apply",
            "position": "Engineer",
            "company": "Co",
            "description": None,
            "date": recent_date,
            "tags": [],
            "location": "Worldwide",
            "salary_min": 0,
            "salary_max": 0,
        }
    ]
    with (
        patch("jobdigest.adapters.remoteok.get_json", return_value=payload),
        patch("jobdigest.adapters.remoteok._utcnow", return_value=now),
    ):
        result = RemoteOkSource(_config(recency_hours=72)).fetch()
    assert len(result) == 1


def test_fetch_recency_filter_outside_window():
    now = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    old_date = (now - timedelta(hours=100)).isoformat()
    payload = [
        {
            "id": "2",
            "slug": "old-job",
            "url": "https://remoteok.com/2",
            "apply_url": "https://example.com/apply",
            "position": "Old Engineer",
            "company": "OldCo",
            "description": None,
            "date": old_date,
            "tags": [],
            "location": "Worldwide",
            "salary_min": 0,
            "salary_max": 0,
        }
    ]
    with (
        patch("jobdigest.adapters.remoteok.get_json", return_value=payload),
        patch("jobdigest.adapters.remoteok._utcnow", return_value=now),
    ):
        result = RemoteOkSource(_config(recency_hours=72)).fetch()
    assert result == []


def test_fetch_http_error_returns_empty():
    with patch(
        "jobdigest.adapters.remoteok.get_json",
        side_effect=RuntimeError("network error"),
    ):
        result = RemoteOkSource(_config()).fetch()
    assert result == []


def test_fetch_url_falls_back_to_remoteok_url():
    payload = [
        {
            "id": "99",
            "slug": "fallback-job",
            "url": "https://remoteok.com/99",
            "position": "Dev",
            "company": "Co",
            "description": None,
            "date": "2099-01-01T00:00:00+00:00",
            "tags": [],
            "location": "Worldwide",
            "salary_min": 0,
            "salary_max": 0,
        }
    ]
    with patch("jobdigest.adapters.remoteok.get_json", return_value=payload):
        result = RemoteOkSource(_config()).fetch()
    assert result[0].url == "https://remoteok.com/99"
