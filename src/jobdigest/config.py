import json
from dataclasses import dataclass
from dataclasses import fields as dataclass_fields
from pathlib import Path

from jobdigest.models import Profile

_DEFAULTS: dict = {
    "recency_hours": 72,
    "min_score": 50,
    "output_dir": "./output",
    "enabled_sources": ["adzuna", "himalayas", "remoteok", "jobicy", "working_nomads"],
    "weights": {
        "closeness": 30,
        "skills_match": 25,
        "experience_level": 10,
        "salary": 10,
        "freshness": 15,
        "languages": 5,
        "employment_type": 5,
    },
    "onboarding_llm": {
        "provider": "gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-2.5-flash",
        "api_key_env": "GEMINI_API_KEY",
    },
    "daily_llm_scoring": {"enabled": False, "model": None},
    "log_level": "INFO",
}


@dataclass
class LLMConfig:
    provider: str
    base_url: str
    model: str
    api_key_env: str


@dataclass
class Config:
    recency_hours: int
    min_score: int
    output_dir: Path
    enabled_sources: list
    weights: dict
    onboarding_llm: LLMConfig
    daily_llm_scoring: dict
    log_level: str


def load_config(path: Path = Path("config.json")) -> Config:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    merged = {**_DEFAULTS, **data}
    llm_raw = {**_DEFAULTS["onboarding_llm"], **merged.get("onboarding_llm", {})}

    return Config(
        recency_hours=int(merged["recency_hours"]),
        min_score=int(merged["min_score"]),
        output_dir=Path(merged["output_dir"]),
        enabled_sources=list(merged["enabled_sources"]),
        weights=dict(merged["weights"]),
        onboarding_llm=LLMConfig(**llm_raw),
        daily_llm_scoring=dict(merged["daily_llm_scoring"]),
        log_level=str(merged["log_level"]),
    )


def load_profile(path: Path = Path("profile.json")) -> Profile | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    known = {f.name for f in dataclass_fields(Profile)}
    return Profile(**{k: v for k, v in data.items() if k in known})
