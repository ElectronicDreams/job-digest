import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from jobdigest.adapters.himalayas import HimalayasSource
from jobdigest.config import Config, LLMConfig

_FIXTURE = json.loads(
    (Path(__file__).parent.parent / "fixtures" / "himalayas_jobs.json").read_text()
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
        enabled_sources=["himalayas"],
        weights={},
        onboarding_llm=_LLM,
        daily_llm_scoring={"enabled": False, "model": None},
        log_level="INFO",
        exclusion_phrases=[],
    )


def test_fetch_happy_path_returns_jobs():
    with patch("jobdigest.adapters.himalayas.get_json", return_value=_FIXTURE):
        result = HimalayasSource(_config()).fetch()
    assert len(result) == 2
    assert result[0].source == "himalayas"
    assert result[0].title == "Senior Python Developer"
    assert result[0].company == "Acme Corp"
    assert (
        result[0].url
        == "https://himalayas.app/companies/acme-corp/jobs/senior-python-developer"
    )


def test_fetch_id_uses_guid():
    with patch("jobdigest.adapters.himalayas.get_json", return_value=_FIXTURE):
        result = HimalayasSource(_config()).fetch()
    assert "himalayas.app" in result[0].id


def test_fetch_salary_parsed():
    with patch("jobdigest.adapters.himalayas.get_json", return_value=_FIXTURE):
        result = HimalayasSource(_config()).fetch()
    assert result[0].salary == {
        "min": 100000,
        "max": 150000,
        "currency": "USD",
        "period": "yearly",
    }


def test_fetch_missing_salary_is_none():
    with patch("jobdigest.adapters.himalayas.get_json", return_value=_FIXTURE):
        result = HimalayasSource(_config()).fetch()
    assert result[1].salary is None


def test_fetch_employment_type_mapped():
    with patch("jobdigest.adapters.himalayas.get_json", return_value=_FIXTURE):
        result = HimalayasSource(_config()).fetch()
    assert result[0].employment_type == "full-time"
    assert result[1].employment_type == "contract"


def test_fetch_all_jobs_are_remote():
    with patch("jobdigest.adapters.himalayas.get_json", return_value=_FIXTURE):
        result = HimalayasSource(_config()).fetch()
    assert all(j.is_remote for j in result)


def test_fetch_location_from_restrictions():
    with patch("jobdigest.adapters.himalayas.get_json", return_value=_FIXTURE):
        result = HimalayasSource(_config()).fetch()
    assert result[0].location == "remote"
    assert result[1].location == "united states"


def test_fetch_pubdate_parsed_from_timestamp():
    with patch("jobdigest.adapters.himalayas.get_json", return_value=_FIXTURE):
        result = HimalayasSource(_config()).fetch()
    assert result[0].posted_date is not None
    assert result[0].posted_date.tzinfo is not None


def test_fetch_empty_response():
    with patch("jobdigest.adapters.himalayas.get_json", return_value={"jobs": []}):
        result = HimalayasSource(_config()).fetch()
    assert result == []


def test_fetch_recency_filter_inside_window():
    now = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    recent_ts = int((now - timedelta(hours=1)).timestamp())
    payload = {
        "jobs": [
            {
                "title": "Job",
                "companyName": "Co",
                "employmentType": "Full-time",
                "minSalary": None,
                "maxSalary": None,
                "currency": None,
                "salaryPeriod": None,
                "locationRestrictions": [],
                "description": None,
                "pubDate": recent_ts,
                "applicationLink": "https://himalayas.app/jobs/1",
                "guid": "https://himalayas.app/jobs/1",
            }
        ]
    }
    with (
        patch("jobdigest.adapters.himalayas.get_json", return_value=payload),
        patch("jobdigest.adapters.himalayas._utcnow", return_value=now),
    ):
        result = HimalayasSource(_config(recency_hours=72)).fetch()
    assert len(result) == 1


def test_fetch_recency_filter_outside_window():
    now = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    old_ts = int((now - timedelta(hours=100)).timestamp())
    payload = {
        "jobs": [
            {
                "title": "Old Job",
                "companyName": "OldCo",
                "employmentType": "Full-time",
                "minSalary": None,
                "maxSalary": None,
                "currency": None,
                "salaryPeriod": None,
                "locationRestrictions": [],
                "description": None,
                "pubDate": old_ts,
                "applicationLink": "https://himalayas.app/jobs/2",
                "guid": "https://himalayas.app/jobs/2",
            }
        ]
    }
    with (
        patch("jobdigest.adapters.himalayas.get_json", return_value=payload),
        patch("jobdigest.adapters.himalayas._utcnow", return_value=now),
    ):
        result = HimalayasSource(_config(recency_hours=72)).fetch()
    assert result == []


def test_fetch_http_error_returns_empty():
    with patch(
        "jobdigest.adapters.himalayas.get_json",
        side_effect=RuntimeError("network error"),
    ):
        result = HimalayasSource(_config()).fetch()
    assert result == []
