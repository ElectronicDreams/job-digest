from pathlib import Path

from jobdigest.config import Config, LLMConfig
from jobdigest.core.gates import (  # noqa: E501
    _passes_eligibility_gate,
    _passes_metro_gate,
    _passes_title_gate,
    apply_gates,
)
from jobdigest.models import Job, Profile

_PHRASES = ["uk only", "must be located in the uk", "no international applicants"]

_LLM = LLMConfig(
    provider="test",
    base_url="https://example.com",
    model="test-model",
    api_key_env="TEST_KEY",
)


def _config(exclusion_phrases: list | None = None) -> Config:
    return Config(
        recency_hours=72,
        min_score=50,
        output_dir=Path("./output"),
        enabled_sources=[],
        weights={},
        onboarding_llm=_LLM,
        daily_llm_scoring={"enabled": False, "model": None},
        log_level="INFO",
        exclusion_phrases=exclusion_phrases
        if exclusion_phrases is not None
        else _PHRASES,  # noqa: E501
    )


def _job(**kwargs) -> Job:
    defaults = dict(
        source="test",
        id="1",
        title="Senior Python Developer",
        company="Acme Corp",
        location="toronto, on",
        is_remote=False,
        url="https://example.com/jobs/1",
    )
    return Job(**{**defaults, **kwargs})


def _profile(**kwargs) -> Profile:
    defaults = dict(
        title_variants=["python developer", "backend engineer"],
        seniority_terms=["senior", "lead"],
        skills=["python", "django", "postgres"],
        location="toronto",
        acceptable_locations=["toronto", "remote"],
    )
    return Profile(**{**defaults, **kwargs})


# --- Metro gate ---


def test_metro_remote_job_always_passes():
    assert (
        _passes_metro_gate(_job(is_remote=True, location="anywhere"), _profile())
        is True
    )  # noqa: E501


def test_metro_onsite_in_same_city_passes():
    assert _passes_metro_gate(_job(location="toronto, on"), _profile()) is True


def test_metro_onsite_acceptable_location_passes():
    job = _job(is_remote=False, location="new york, ny")
    profile = _profile(acceptable_locations=["new york"])
    assert _passes_metro_gate(job, profile) is True


def test_metro_onsite_different_city_dropped():
    job = _job(is_remote=False, location="vancouver, bc")
    assert _passes_metro_gate(job, _profile()) is False


def test_metro_case_insensitive():
    job = _job(is_remote=False, location="TORONTO, ON")
    assert _passes_metro_gate(job, _profile()) is True


def test_metro_empty_profile_location_keeps_all_remote():
    job = _job(is_remote=True)
    assert (
        _passes_metro_gate(job, _profile(location="", acceptable_locations=[])) is True
    )  # noqa: E501


# --- Eligibility gate ---


def test_eligibility_no_description_keeps():
    assert _passes_eligibility_gate(_job(description=None), _PHRASES) is True


def test_eligibility_clean_description_keeps():
    assert (
        _passes_eligibility_gate(_job(description="Great Python role."), _PHRASES)
        is True
    )  # noqa: E501


def test_eligibility_phrase_match_drops():
    assert (
        _passes_eligibility_gate(_job(description="This role is UK only."), _PHRASES)
        is False  # noqa: E501
    )


def test_eligibility_second_phrase_drops():
    desc = "You must be located in the UK to apply."
    assert _passes_eligibility_gate(_job(description=desc), _PHRASES) is False


def test_eligibility_no_international_drops():
    assert (
        _passes_eligibility_gate(
            _job(description="No international applicants, sorry."), _PHRASES
        )
        is False
    )


def test_eligibility_ambiguous_keeps():
    assert (
        _passes_eligibility_gate(
            _job(description="We are an equal opportunity employer."), _PHRASES
        )
        is True
    )


def test_eligibility_case_insensitive():
    assert (
        _passes_eligibility_gate(_job(description="UK ONLY APPLICANTS"), _PHRASES)
        is False
    )  # noqa: E501


def test_eligibility_empty_phrases_always_keeps():
    assert _passes_eligibility_gate(_job(description="UK only."), []) is True


# --- Title/tech gate ---


def test_title_overlap_on_seniority_keeps():
    job = _job(title="Senior Data Engineer")
    assert _passes_title_gate(job, _profile()) is True


def test_title_overlap_on_skill_keeps():
    job = _job(title="Django Developer")
    assert _passes_title_gate(job, _profile()) is True


def test_title_overlap_on_title_variant_keeps():
    job = _job(title="Python Developer II")
    assert _passes_title_gate(job, _profile()) is True


def test_title_zero_overlap_drops():
    job = _job(title="Marketing Manager")
    assert _passes_title_gate(job, _profile()) is False


def test_title_empty_profile_terms_keeps():
    job = _job(title="Marketing Manager")
    profile = _profile(title_variants=[], seniority_terms=[], skills=[])
    assert _passes_title_gate(job, profile) is True


def test_title_case_insensitive():
    job = _job(title="SENIOR PYTHON DEVELOPER")
    assert _passes_title_gate(job, _profile()) is True


# --- apply_gates composition ---


def test_apply_gates_all_pass():
    jobs = [_job(is_remote=True, title="Senior Python Developer")]
    result = apply_gates(jobs, _profile(), _config())
    assert len(result) == 1


def test_apply_gates_drops_failed_metro():
    jobs = [
        _job(is_remote=False, location="vancouver, bc", title="Senior Python Developer")
    ]  # noqa: E501
    assert apply_gates(jobs, _profile(), _config()) == []


def test_apply_gates_drops_failed_eligibility():
    jobs = [_job(is_remote=True, description="UK only applicants.")]
    assert apply_gates(jobs, _profile(), _config()) == []


def test_apply_gates_empty_exclusion_phrases_keeps_all_eligible():
    jobs = [_job(is_remote=True, description="UK only applicants.")]
    assert len(apply_gates(jobs, _profile(), _config(exclusion_phrases=[]))) == 1


def test_apply_gates_drops_failed_title():
    jobs = [_job(is_remote=True, title="Marketing Manager")]
    assert apply_gates(jobs, _profile(), _config()) == []


def test_apply_gates_mixed_list():
    jobs = [
        _job(id="1", is_remote=True, title="Senior Python Developer"),
        _job(id="2", is_remote=False, location="vancouver, bc"),
        _job(id="3", is_remote=True, title="Sales Executive"),
    ]
    result = apply_gates(jobs, _profile(), _config())
    assert len(result) == 1
    assert result[0].id == "1"
