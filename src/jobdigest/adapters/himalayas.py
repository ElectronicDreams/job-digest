from datetime import datetime, timedelta, timezone

from jobdigest.adapters.base import JobSource
from jobdigest.config import Config
from jobdigest.models import Job
from jobdigest.utils.dates import parse_date
from jobdigest.utils.http import get_json
from jobdigest.utils.location import normalize_location
from jobdigest.utils.logging import get_logger

_BASE_URL = "https://himalayas.app/jobs/api"
_LOGGER = get_logger(__name__)

_EMPLOYMENT_TYPE_MAP: dict[str, str] = {
    "fulltime": "full-time",
    "parttime": "part-time",
    "contract": "contract",
    "internship": "internship",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class HimalayasSource(JobSource):
    def __init__(self, config: Config) -> None:
        self._config = config

    def fetch(self) -> list[Job]:
        try:
            data = get_json(_BASE_URL, params={"limit": 100})
        except Exception as exc:
            _LOGGER.warning("Himalayas fetch failed: %s", exc)
            return []

        jobs_raw = data.get("jobs", []) if isinstance(data, dict) else []
        cutoff = _utcnow() - timedelta(hours=self._config.recency_hours)
        results: list[Job] = []

        for raw in jobs_raw:
            posted = parse_date(raw.get("postedAt"))
            if posted is not None and posted < cutoff:
                continue

            salary_raw = raw.get("salary")
            salary = (
                {
                    "min": salary_raw.get("min"),
                    "max": salary_raw.get("max"),
                    "currency": salary_raw.get("currency"),
                }
                if isinstance(salary_raw, dict)
                else None
            )

            locations: list = raw.get("locations") or []
            location_str = normalize_location(locations[0] if locations else None)
            is_remote = bool(raw.get("remote", False)) or "remote" in location_str

            job_type_raw = (raw.get("jobType") or "").lower()
            employment_type = _EMPLOYMENT_TYPE_MAP.get(job_type_raw)

            results.append(
                Job(
                    source="himalayas",
                    id=str(raw.get("id", "")),
                    title=str(raw.get("title", "")),
                    company=str(raw.get("companyName", "")),
                    location=location_str,
                    is_remote=is_remote,
                    url=str(raw.get("url", "")),
                    salary=salary,
                    employment_type=employment_type,
                    posted_date=posted,
                    description=raw.get("description"),
                )
            )

        return results
