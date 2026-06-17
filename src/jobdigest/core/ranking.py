from jobdigest.config import Config
from jobdigest.core.scorers.base import Scorer
from jobdigest.core.scorers.freshness import FreshnessStub
from jobdigest.models import Job, Profile
from jobdigest.utils.logging import get_logger

_LOGGER = get_logger(__name__)


# Phase 4 scorers append to this list.
SCORERS: list[Scorer] = [FreshnessStub()]


def _weighted_score(job: Job, profile: Profile, config: Config) -> float:
    total = 0.0
    weight_sum = sum(config.weights.get(s.key, 0) for s in SCORERS)
    if weight_sum == 0:
        return 0.0
    for scorer in SCORERS:
        weight = config.weights.get(scorer.key, 0)
        if weight == 0:
            continue
        try:
            raw = scorer.score(job, profile, config)
        except Exception as exc:
            _LOGGER.warning("Scorer %s raised for job %s: %s", scorer.key, job.id, exc)
            raw = 0.0
        total += raw * (weight / weight_sum)
    return total


def rank_jobs(jobs: list[Job], profile: Profile, config: Config) -> list[Job]:
    if not jobs:
        return []
    scored = [(job, _weighted_score(job, profile, config)) for job in jobs]
    passing = [(job, s) for job, s in scored if s >= config.min_score]
    passing.sort(key=lambda x: x[1], reverse=True)
    return [job for job, _ in passing]
