from pathlib import Path
from unittest.mock import patch

import pytest

from jobdigest.config import Config, LLMConfig
from jobdigest.models import Job, Profile
from jobdigest.runner import run

_LLM = LLMConfig(
    provider="test",
    base_url="https://example.com",
    model="test-model",
    api_key_env="TEST_KEY",
)


def _config(tmp_path: Path, min_score: int = 0) -> Config:
    return Config(
        recency_hours=72,
        min_score=min_score,
        output_dir=tmp_path / "output",
        enabled_sources=[],
        weights={"freshness": 100},
        onboarding_llm=_LLM,
        daily_llm_scoring={"enabled": False, "model": None},
        log_level="INFO",
        exclusion_phrases=[],
    )


def _job(id: str = "1", source: str = "test") -> Job:
    return Job(
        source=source,
        id=id,
        title="Senior Python Developer",
        company="Acme Corp",
        location="remote",
        is_remote=True,
        url=f"https://example.com/jobs/{id}",
    )


def _profile() -> Profile:
    return Profile(
        title_variants=["python developer"],
        seniority_terms=["senior"],
        skills=["python"],
    )


class _GoodSource:
    def __init__(self, config):
        pass

    def fetch(self):
        return [_job("good-1")]


class _BadSource:
    def __init__(self, config):
        pass

    def fetch(self):
        raise RuntimeError("network down")


class _EmptySource:
    def __init__(self, config):
        pass

    def fetch(self):
        return []


def test_runner_produces_html_file(tmp_path):
    config = _config(tmp_path)
    with patch("jobdigest.runner.registry.SOURCES", [_GoodSource]):
        out = run(config, _profile(), db_path=tmp_path / "seen.db")
    assert out.exists()
    assert out.suffix == ".html"
    assert "digest-" in out.name


def test_runner_html_contains_job_title(tmp_path):
    config = _config(tmp_path)
    with patch("jobdigest.runner.registry.SOURCES", [_GoodSource]):
        out = run(config, _profile(), db_path=tmp_path / "seen.db")
    assert "Senior Python Developer" in out.read_text()


def test_runner_failure_isolation(tmp_path):
    config = _config(tmp_path)
    with patch("jobdigest.runner.registry.SOURCES", [_GoodSource, _BadSource]):
        out = run(config, _profile(), db_path=tmp_path / "seen.db")
    html = out.read_text()
    assert "Senior Python Developer" in html
    assert "_BadSource" in html


def test_runner_empty_result_produces_file(tmp_path):
    config = _config(tmp_path)
    with patch("jobdigest.runner.registry.SOURCES", [_EmptySource]):
        out = run(config, _profile(), db_path=tmp_path / "seen.db")
    assert out.exists()
    assert "No new jobs" in out.read_text()


def test_runner_creates_output_dir(tmp_path):
    config = _config(tmp_path)
    assert not config.output_dir.exists()
    with patch("jobdigest.runner.registry.SOURCES", [_EmptySource]):
        run(config, _profile(), db_path=tmp_path / "seen.db")
    assert config.output_dir.exists()


def test_runner_dedup_prevents_second_run_repeat(tmp_path):
    config = _config(tmp_path)
    db = tmp_path / "seen.db"
    with patch("jobdigest.runner.registry.SOURCES", [_GoodSource]):
        run(config, _profile(), db_path=db)
        out2 = run(config, _profile(), db_path=db)
    assert "No new jobs" in out2.read_text()


# --- First-run guard (cli) ---


def test_first_run_guard_exits_1_with_message(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)  # no profile.json here
    from jobdigest.cli import _run

    with pytest.raises(SystemExit) as exc:
        _run()
    assert exc.value.code == 1
    assert "No profile found" in capsys.readouterr().out
