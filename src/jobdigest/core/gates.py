import re

from jobdigest.models import Job, Profile

_EXCLUSION_PHRASES = (
    "us only",
    "usa only",
    "united states only",
    "must be located in the united states",
    "must reside in the united states",
    "us residents only",
    "united states residents only",
    "no canada",
    "canada not eligible",
)


def _passes_metro_gate(job: Job, profile: Profile) -> bool:
    if job.is_remote:
        return True
    job_loc = job.location.lower()
    targets = [profile.location] + list(profile.acceptable_locations)
    return any(t.strip().lower() in job_loc for t in targets if t.strip())


def _passes_eligibility_gate(job: Job) -> bool:
    if not job.description:
        return True
    desc = job.description.lower()
    return not any(phrase in desc for phrase in _EXCLUSION_PHRASES)


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9+#]+", text.lower()))


def _passes_title_gate(job: Job, profile: Profile) -> bool:
    job_tokens = _tokenize(job.title)
    profile_terms = profile.title_variants + profile.seniority_terms + profile.skills
    profile_tokens: set[str] = set()
    for term in profile_terms:
        profile_tokens |= _tokenize(str(term))
    if not profile_tokens:
        return True
    return bool(job_tokens & profile_tokens)


def apply_gates(jobs: list[Job], profile: Profile) -> list[Job]:
    return [
        job
        for job in jobs
        if _passes_metro_gate(job, profile)
        and _passes_eligibility_gate(job)
        and _passes_title_gate(job, profile)
    ]
