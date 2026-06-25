import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from jobdigest.adapters.jobicy import JobicySource
from jobdigest.config import Config, LLMConfig

_FIXTURE = json.loads(
    (Path(__file__).parent.parent / "fixtures" / "jobicy_jobs.json").read_text()
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
        enabled_sources=["jobicy"],
        weights={},
        onboarding_llm=_LLM,
        daily_llm_scoring={"enabled": False, "model": None},
        log_level="INFO",
        exclusion_phrases=[],
    )


def test_fetch_happy_path_returns_jobs():
    with patch("jobdigest.adapters.jobicy.get_json", return_value=_FIXTURE):
        result = JobicySource(_config()).fetch()
    assert len(result) == 2
    assert result[0].source == "jobicy"
    assert result[0].title == "Senior Backend Engineer"
    assert result[0].company == "Acme Corp"
    assert result[0].url == "https://jobicy.com/jobs/142662-senior-backend-engineer"


def test_fetch_id_is_stringified():
    with patch("jobdigest.adapters.jobicy.get_json", return_value=_FIXTURE):
        result = JobicySource(_config()).fetch()
    assert result[0].id == "142662"


def test_fetch_salary_parsed():
    with patch("jobdigest.adapters.jobicy.get_json", return_value=_FIXTURE):
        result = JobicySource(_config()).fetch()
    assert result[0].salary == {
        "min": 120000,
        "max": 180000,
        "currency": "USD",
        "period": "yearly",
    }


def test_fetch_missing_salary_is_none():
    with patch("jobdigest.adapters.jobicy.get_json", return_value=_FIXTURE):
        result = JobicySource(_config()).fetch()
    assert result[1].salary is None


def test_fetch_employment_type_mapped():
    with patch("jobdigest.adapters.jobicy.get_json", return_value=_FIXTURE):
        result = JobicySource(_config()).fetch()
    assert result[0].employment_type == "full-time"
    assert result[1].employment_type == "contract"


def test_fetch_all_jobs_are_remote():
    with patch("jobdigest.adapters.jobicy.get_json", return_value=_FIXTURE):
        result = JobicySource(_config()).fetch()
    assert all(j.is_remote for j in result)


def test_fetch_location_normalized():
    with patch("jobdigest.adapters.jobicy.get_json", return_value=_FIXTURE):
        result = JobicySource(_config()).fetch()
    assert result[0].location == "usa"
    assert result[1].location == "belgium,  spain,  uk"


def test_fetch_date_parsed():
    with patch("jobdigest.adapters.jobicy.get_json", return_value=_FIXTURE):
        result = JobicySource(_config()).fetch()
    assert result[0].posted_date is not None
    assert result[0].posted_date.tzinfo is not None


def test_fetch_description_prefers_full_over_excerpt():
    with patch("jobdigest.adapters.jobicy.get_json", return_value=_FIXTURE):
        result = JobicySource(_config()).fetch()
    expected = "<p>Build scalable backend systems with Python and AWS.</p>"
    assert result[0].description == expected


def test_fetch_description_falls_back_to_excerpt():
    fixture = {
        "jobs": [
            {
                **_FIXTURE["jobs"][1],
                "jobDescription": None,
                "jobExcerpt": "Build React UIs.",
            }
        ]
    }
    with patch("jobdigest.adapters.jobicy.get_json", return_value=fixture):
        result = JobicySource(_config()).fetch()
    assert result[0].description == "Build React UIs."


def test_fetch_empty_jobs():
    with patch("jobdigest.adapters.jobicy.get_json", return_value={"jobs": []}):
        result = JobicySource(_config()).fetch()
    assert result == []


def test_fetch_recency_filter_inside_window():
    now = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    recent = (now - timedelta(hours=1)).isoformat()
    payload = {
        "jobs": [
            {
                "id": 1,
                "url": "https://jobicy.com/jobs/1",
                "jobTitle": "Engineer",
                "companyName": "Co",
                "jobType": ["Full-Time"],
                "jobGeo": "USA",
                "jobDescription": None,
                "jobExcerpt": None,
                "pubDate": recent,
                "salaryMin": None,
                "salaryMax": None,
                "salaryCurrency": None,
                "salaryPeriod": None,
            }
        ]
    }
    with (
        patch("jobdigest.adapters.jobicy.get_json", return_value=payload),
        patch("jobdigest.adapters.jobicy._utcnow", return_value=now),
    ):
        result = JobicySource(_config(recency_hours=72)).fetch()
    assert len(result) == 1


def test_fetch_recency_filter_outside_window():
    now = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    old = (now - timedelta(hours=100)).isoformat()
    payload = {
        "jobs": [
            {
                "id": 2,
                "url": "https://jobicy.com/jobs/2",
                "jobTitle": "Old Engineer",
                "companyName": "OldCo",
                "jobType": ["Full-Time"],
                "jobGeo": "USA",
                "jobDescription": None,
                "jobExcerpt": None,
                "pubDate": old,
                "salaryMin": None,
                "salaryMax": None,
                "salaryCurrency": None,
                "salaryPeriod": None,
            }
        ]
    }
    with (
        patch("jobdigest.adapters.jobicy.get_json", return_value=payload),
        patch("jobdigest.adapters.jobicy._utcnow", return_value=now),
    ):
        result = JobicySource(_config(recency_hours=72)).fetch()
    assert result == []


def test_fetch_http_error_returns_empty():
    with patch(
        "jobdigest.adapters.jobicy.get_json",
        side_effect=RuntimeError("network error"),
    ):
        result = JobicySource(_config()).fetch()
    assert result == []
