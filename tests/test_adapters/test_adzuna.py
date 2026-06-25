import json
from pathlib import Path
from unittest.mock import patch

from jobdigest.adapters.adzuna import AdzunaSource
from jobdigest.config import Config, LLMConfig

_FIXTURE = json.loads(
    (Path(__file__).parent.parent / "fixtures" / "adzuna_jobs.json").read_text()
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
        enabled_sources=["adzuna"],
        weights={},
        onboarding_llm=_LLM,
        daily_llm_scoring={"enabled": False, "model": None},
        log_level="INFO",
        exclusion_phrases=[],
    )


def _source(recency_hours: int = 72) -> AdzunaSource:
    src = AdzunaSource(_config(recency_hours))
    src._app_id = "test_id"
    src._app_key = "test_key"
    return src


def test_fetch_happy_path_returns_jobs():
    with patch("jobdigest.adapters.adzuna.get_json", return_value=_FIXTURE):
        result = _source().fetch()
    assert len(result) == 2
    assert result[0].source == "adzuna"
    assert result[0].title == "Senior Python Developer"
    assert result[0].company == "Acme Corp"
    assert result[0].url == "https://www.adzuna.ca/jobs/details/4700116521"


def test_fetch_salary_parsed():
    with patch("jobdigest.adapters.adzuna.get_json", return_value=_FIXTURE):
        result = _source().fetch()
    assert result[0].salary == {
        "min": 100000.0,
        "max": 140000.0,
        "currency": "CAD",
        "period": "yearly",
    }


def test_fetch_missing_salary_is_none():
    with patch("jobdigest.adapters.adzuna.get_json", return_value=_FIXTURE):
        result = _source().fetch()
    assert result[1].salary is None


def test_fetch_employment_type_permanent_full_time():
    with patch("jobdigest.adapters.adzuna.get_json", return_value=_FIXTURE):
        result = _source().fetch()
    assert result[0].employment_type == "full-time"


def test_fetch_employment_type_contract():
    with patch("jobdigest.adapters.adzuna.get_json", return_value=_FIXTURE):
        result = _source().fetch()
    assert result[1].employment_type == "contract"


def test_fetch_remote_detected_from_title():
    with patch("jobdigest.adapters.adzuna.get_json", return_value=_FIXTURE):
        result = _source().fetch()
    assert result[1].is_remote is True


def test_fetch_onsite_not_flagged_remote():
    with patch("jobdigest.adapters.adzuna.get_json", return_value=_FIXTURE):
        result = _source().fetch()
    assert result[0].is_remote is False


def test_fetch_remote_detected_from_description():
    payload = {
        "results": [
            {
                **_FIXTURE["results"][0],
                "title": "Backend Developer",
                "description": "This is a work from home position.",
            }
        ]
    }
    with patch("jobdigest.adapters.adzuna.get_json", return_value=payload):
        result = _source().fetch()
    assert result[0].is_remote is True


def test_fetch_location_normalized():
    with patch("jobdigest.adapters.adzuna.get_json", return_value=_FIXTURE):
        result = _source().fetch()
    assert result[0].location == "toronto, ontario"


def test_fetch_date_parsed():
    with patch("jobdigest.adapters.adzuna.get_json", return_value=_FIXTURE):
        result = _source().fetch()
    assert result[0].posted_date is not None
    assert result[0].posted_date.tzinfo is not None


def test_fetch_missing_credentials_returns_empty():
    src = AdzunaSource(_config())
    src._app_id = ""
    src._app_key = ""
    result = src.fetch()
    assert result == []


def test_fetch_empty_results():
    with patch("jobdigest.adapters.adzuna.get_json", return_value={"results": []}):
        result = _source().fetch()
    assert result == []


def test_fetch_recency_uses_max_days_old():
    _patch = patch("jobdigest.adapters.adzuna.get_json", return_value={"results": []})
    with _patch as mock_get:
        _source(recency_hours=48).fetch()
    _, kwargs = mock_get.call_args
    assert kwargs["params"]["max_days_old"] == 2


def test_fetch_recency_hours_rounds_up():
    _patch = patch("jobdigest.adapters.adzuna.get_json", return_value={"results": []})
    with _patch as mock_get:
        _source(recency_hours=25).fetch()
    _, kwargs = mock_get.call_args
    assert kwargs["params"]["max_days_old"] == 2


def test_fetch_http_error_returns_empty():
    with patch(
        "jobdigest.adapters.adzuna.get_json",
        side_effect=RuntimeError("network error"),
    ):
        result = _source().fetch()
    assert result == []
