import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from jobdigest.adapters.working_nomads import WorkingNomadsSource
from jobdigest.config import Config, LLMConfig

_FIXTURE = json.loads(
    (Path(__file__).parent.parent / "fixtures" / "working_nomads_jobs.json").read_text()
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
        enabled_sources=["working_nomads"],
        weights={},
        onboarding_llm=_LLM,
        daily_llm_scoring={"enabled": False, "model": None},
        log_level="INFO",
        exclusion_phrases=[],
    )


def test_fetch_happy_path_returns_jobs():
    with patch("jobdigest.adapters.working_nomads.get_json", return_value=_FIXTURE):
        result = WorkingNomadsSource(_config()).fetch()
    assert len(result) == 2
    assert result[0].source == "working_nomads"
    assert result[0].title == "Senior Python Developer"
    assert result[0].company == "Acme Corp"
    assert result[0].url == "https://www.workingnomads.com/job/go/1691057/"


def test_fetch_id_extracted_from_url():
    with patch("jobdigest.adapters.working_nomads.get_json", return_value=_FIXTURE):
        result = WorkingNomadsSource(_config()).fetch()
    assert result[0].id == "1691057"
    assert result[1].id == "1691058"


def test_fetch_salary_always_none():
    with patch("jobdigest.adapters.working_nomads.get_json", return_value=_FIXTURE):
        result = WorkingNomadsSource(_config()).fetch()
    assert all(j.salary is None for j in result)


def test_fetch_employment_type_inferred_from_tags():
    with patch("jobdigest.adapters.working_nomads.get_json", return_value=_FIXTURE):
        result = WorkingNomadsSource(_config()).fetch()
    assert result[0].employment_type is None
    assert result[1].employment_type == "contract"


def test_fetch_all_jobs_are_remote():
    with patch("jobdigest.adapters.working_nomads.get_json", return_value=_FIXTURE):
        result = WorkingNomadsSource(_config()).fetch()
    assert all(j.is_remote for j in result)


def test_fetch_location_normalized():
    with patch("jobdigest.adapters.working_nomads.get_json", return_value=_FIXTURE):
        result = WorkingNomadsSource(_config()).fetch()
    assert result[0].location == "north america"
    assert result[1].location == "worldwide, north america, europe"


def test_fetch_date_parsed_with_offset():
    with patch("jobdigest.adapters.working_nomads.get_json", return_value=_FIXTURE):
        result = WorkingNomadsSource(_config()).fetch()
    assert result[0].posted_date is not None
    assert result[0].posted_date.tzinfo is not None


def test_fetch_description_preserved():
    with patch("jobdigest.adapters.working_nomads.get_json", return_value=_FIXTURE):
        result = WorkingNomadsSource(_config()).fetch()
    assert result[0].description == "<p>Build scalable backend systems with Python.</p>"
    assert result[1].description is None


def test_fetch_empty_list():
    with patch("jobdigest.adapters.working_nomads.get_json", return_value=[]):
        result = WorkingNomadsSource(_config()).fetch()
    assert result == []


def test_fetch_non_list_response_returns_empty():
    bad_response = {"error": "bad"}
    with patch("jobdigest.adapters.working_nomads.get_json", return_value=bad_response):
        result = WorkingNomadsSource(_config()).fetch()
    assert result == []


def test_fetch_recency_filter_inside_window():
    now = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    recent = (now - timedelta(hours=1)).isoformat()
    payload = [
        {
            "url": "https://www.workingnomads.com/job/go/111/",
            "title": "Engineer",
            "description": None,
            "company_name": "Co",
            "category_name": "Development",
            "tags": "",
            "location": "Worldwide",
            "pub_date": recent,
        }
    ]
    with (
        patch("jobdigest.adapters.working_nomads.get_json", return_value=payload),
        patch("jobdigest.adapters.working_nomads._utcnow", return_value=now),
    ):
        result = WorkingNomadsSource(_config(recency_hours=72)).fetch()
    assert len(result) == 1


def test_fetch_recency_filter_outside_window():
    now = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    old = (now - timedelta(hours=100)).isoformat()
    payload = [
        {
            "url": "https://www.workingnomads.com/job/go/222/",
            "title": "Old Engineer",
            "description": None,
            "company_name": "OldCo",
            "category_name": "Development",
            "tags": "",
            "location": "Worldwide",
            "pub_date": old,
        }
    ]
    with (
        patch("jobdigest.adapters.working_nomads.get_json", return_value=payload),
        patch("jobdigest.adapters.working_nomads._utcnow", return_value=now),
    ):
        result = WorkingNomadsSource(_config(recency_hours=72)).fetch()
    assert result == []


def test_fetch_http_error_returns_empty():
    with patch(
        "jobdigest.adapters.working_nomads.get_json",
        side_effect=RuntimeError("network error"),
    ):
        result = WorkingNomadsSource(_config()).fetch()
    assert result == []
