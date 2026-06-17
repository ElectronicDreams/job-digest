from pathlib import Path
from unittest.mock import patch

from jobdigest.config import Config, LLMConfig
from jobdigest.core.ranking import SCORERS, rank_jobs
from jobdigest.core.scorers.base import Scorer
from jobdigest.models import Job, Profile

_LLM = LLMConfig(
    provider="test",
    base_url="https://example.com",
    model="test-model",
    api_key_env="TEST_KEY",
)


def _config(min_score: int = 0, weights: dict | None = None) -> Config:
    return Config(
        recency_hours=72,
        min_score=min_score,
        output_dir=Path("./output"),
        enabled_sources=[],
        weights=weights if weights is not None else {"freshness": 100},
        onboarding_llm=_LLM,
        daily_llm_scoring={"enabled": False, "model": None},
        log_level="INFO",
        exclusion_phrases=[],
    )


def _job(id: str = "1", **kwargs) -> Job:
    defaults = dict(
        source="test",
        title="Python Developer",
        company="Acme",
        location="remote",
        is_remote=True,
        url="https://example.com/jobs/1",
    )
    return Job(id=id, **{**defaults, **kwargs})


def _profile() -> Profile:
    return Profile()


# --- Scorer ABC ---


def test_scorer_subclass_requires_score_method():
    class NoScore(Scorer):
        key = "x"

    import pytest

    with pytest.raises(TypeError):
        NoScore()  # type: ignore[abstract]


def test_scorer_key_attribute():
    assert SCORERS[0].key == "freshness"


# --- FreshnessStub ---


def test_freshness_stub_returns_50():
    stub = SCORERS[0]
    assert stub.score(_job(), _profile(), _config()) == 50.0


# --- rank_jobs ---


def test_rank_jobs_empty_list():
    assert rank_jobs([], _profile(), _config()) == []


def test_rank_jobs_single_job_passes_min_score_zero():
    result = rank_jobs([_job()], _profile(), _config(min_score=0))
    assert len(result) == 1


def test_rank_jobs_stub_score_50_passes_min_score_50():
    result = rank_jobs([_job()], _profile(), _config(min_score=50))
    assert len(result) == 1


def test_rank_jobs_min_score_above_stub_drops_job():
    result = rank_jobs([_job()], _profile(), _config(min_score=51))
    assert result == []


def test_rank_jobs_returns_descending_order():
    class HighScorer(Scorer):
        key = "freshness"

        def score(self, job, profile, config):
            return 90.0 if job.id == "high" else 10.0

    with patch("jobdigest.core.ranking.SCORERS", [HighScorer()]):
        jobs = [_job(id="low"), _job(id="high")]
        result = rank_jobs(jobs, _profile(), _config(min_score=0))
    assert result[0].id == "high"
    assert result[1].id == "low"


def test_rank_jobs_scorer_exception_does_not_propagate():
    class BrokenScorer(Scorer):
        key = "freshness"

        def score(self, job, profile, config):
            raise RuntimeError("boom")

    with patch("jobdigest.core.ranking.SCORERS", [BrokenScorer()]):
        # exception → score 0.0 → drops below min_score=1, no exception raised
        result = rank_jobs([_job()], _profile(), _config(min_score=1))
    assert result == []


def test_rank_jobs_missing_weight_key_uses_zero():
    # no weights → weight_sum=0 → score 0.0 → drops below min_score=1
    result = rank_jobs([_job()], _profile(), _config(min_score=1, weights={}))
    assert result == []


def test_rank_jobs_scorer_exception_contributes_zero_not_crash():
    class BrokenScorer(Scorer):
        key = "freshness"

        def score(self, job, profile, config):
            raise ValueError("bad data")

    with patch("jobdigest.core.ranking.SCORERS", [BrokenScorer()]):
        jobs = [_job()]
        result = rank_jobs(jobs, _profile(), _config(min_score=0))
    assert isinstance(result, list)
