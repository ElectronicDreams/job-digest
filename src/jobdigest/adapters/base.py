from abc import ABC, abstractmethod

from jobdigest.models import Job


class JobSource(ABC):
    @abstractmethod
    def fetch(self) -> list[Job]:
        """Fetch jobs from this source and return them normalized as Job objects."""
        ...
