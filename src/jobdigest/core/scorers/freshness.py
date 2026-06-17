from jobdigest.config import Config
from jobdigest.core.scorers.base import Scorer
from jobdigest.models import Job, Profile


# TODO(phase-4): replace with real freshness logic
class FreshnessStub(Scorer):
    key = "freshness"

    def score(self, job: Job, profile: Profile, config: Config) -> float:
        return 50.0
