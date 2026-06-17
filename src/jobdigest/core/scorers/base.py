from abc import ABC, abstractmethod

from jobdigest.config import Config
from jobdigest.models import Job, Profile


class Scorer(ABC):
    key: str

    @abstractmethod
    def score(self, job: Job, profile: Profile, config: Config) -> float:
        """Return a score in the range 0–100. Never raise."""
        ...
