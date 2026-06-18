from pathlib import Path

from jobdigest.config import Config, LLMConfig
from jobdigest.models import Job
from jobdigest.render.html import render_digest

_LLM = LLMConfig(
    provider="test",
    base_url="https://example.com",
    model="test-model",
    api_key_env="TEST_KEY",
)

_CONFIG = Config(
    recency_hours=72,
    min_score=0,
    output_dir=Path("./output"),
    enabled_sources=[],
    weights={},
    onboarding_llm=_LLM,
    daily_llm_scoring={"enabled": False, "model": None},
    log_level="INFO",
    exclusion_phrases=[],
)


def _job(description: str | None = None) -> Job:
    return Job(
        source="himalayas",
        id="test-id",
        title="Python Dev",
        company="Acme",
        location="remote",
        is_remote=True,
        url="https://example.com/job/1",
        description=description,
    )


def test_description_safe_html_is_rendered():
    html = render_digest([_job("<p>Good job description</p>")], [], _CONFIG)
    assert "<p>Good job description</p>" in html


def test_description_script_tag_is_stripped():
    html = render_digest(
        [_job('<p>Legit content</p><script>alert("xss")</script>')], [], _CONFIG
    )
    assert "<script>" not in html
    assert "alert" not in html


def test_description_inline_event_handler_is_stripped():
    html = render_digest([_job('<p onmouseover="evil()">Hover me</p>')], [], _CONFIG)
    assert "onmouseover" not in html
    assert "evil()" not in html


def test_description_iframe_is_stripped():
    html = render_digest(
        [_job('<iframe src="https://evil.example.com"></iframe><p>text</p>')],
        [],
        _CONFIG,
    )
    assert "<iframe" not in html


def test_description_none_renders_no_desc_block():
    html = render_digest([_job(None)], [], _CONFIG)
    assert 'class="desc"' not in html


def test_no_jobs_renders_empty_state():
    html = render_digest([], [], _CONFIG)
    assert "No new jobs" in html


def test_failed_sources_banner_shown():
    html = render_digest([], ["himalayas"], _CONFIG)
    assert "himalayas" in html
    assert "banner" in html
