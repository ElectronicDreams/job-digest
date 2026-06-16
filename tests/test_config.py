import json
from pathlib import Path

import pytest

from jobdigest.config import load_config, load_profile


def _write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------


def test_load_config_valid(tmp_path: Path):
    _write(tmp_path / "config.json", {"recency_hours": 48, "min_score": 60})
    config = load_config(tmp_path / "config.json")
    assert config.recency_hours == 48
    assert config.min_score == 60


def test_load_config_applies_defaults(tmp_path: Path):
    _write(tmp_path / "config.json", {})
    config = load_config(tmp_path / "config.json")
    assert config.recency_hours == 72
    assert config.min_score == 50
    assert config.log_level == "INFO"
    assert "closeness" in config.weights


def test_load_config_output_dir_is_path(tmp_path: Path):
    _write(tmp_path / "config.json", {"output_dir": "./output"})
    config = load_config(tmp_path / "config.json")
    assert isinstance(config.output_dir, Path)


def test_load_config_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nonexistent.json")


def test_load_config_invalid_json(tmp_path: Path):
    (tmp_path / "config.json").write_text("{ not valid json }", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_config(tmp_path / "config.json")


def test_load_config_llm_defaults_merged(tmp_path: Path):
    _write(tmp_path / "config.json", {"onboarding_llm": {"model": "gemini-2.0-flash"}})
    config = load_config(tmp_path / "config.json")
    assert config.onboarding_llm.model == "gemini-2.0-flash"
    assert config.onboarding_llm.provider == "gemini"


# ---------------------------------------------------------------------------
# load_profile
# ---------------------------------------------------------------------------


def test_load_profile_valid(tmp_path: Path):
    _write(
        tmp_path / "profile.json",
        {
            "title_variants": ["Senior Developer"],
            "skills": ["Python"],
            "seniority_terms": ["senior"],
            "experience_terms": ["5+ years"],
            "location": "Toronto",
            "acceptable_locations": ["Toronto", "Remote"],
            "work_types": ["remote"],
            "work_authorization": "Authorized to work in Canada",
            "salary_floor": {"amount": 100_000, "currency": "CAD"},
            "employment_types": ["permanent"],
        },
    )
    profile = load_profile(tmp_path / "profile.json")
    assert profile is not None
    assert profile.location == "Toronto"
    assert profile.skills == ["Python"]


def test_load_profile_missing_returns_none(tmp_path: Path):
    assert load_profile(tmp_path / "profile.json") is None


def test_load_profile_invalid_json(tmp_path: Path):
    (tmp_path / "profile.json").write_text("{ bad json }", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_profile(tmp_path / "profile.json")


def test_load_profile_ignores_unknown_fields(tmp_path: Path):
    _write(
        tmp_path / "profile.json", {"location": "Montreal", "unknown_key": "ignored"}
    )
    profile = load_profile(tmp_path / "profile.json")
    assert profile is not None
    assert profile.location == "Montreal"


def test_load_profile_partial_fields(tmp_path: Path):
    """Missing optional fields should fall back to dataclass defaults."""
    _write(tmp_path / "profile.json", {"location": "Toronto"})
    profile = load_profile(tmp_path / "profile.json")
    assert profile is not None
    assert profile.skills == []
    assert profile.salary_floor is None
