from datetime import datetime, timedelta, timezone

from jobdigest.adapters.base import JobSource
from jobdigest.config import Config
from jobdigest.models import Job
from jobdigest.utils.http import get_json
from jobdigest.utils.location import normalize_location
from jobdigest.utils.logging import get_logger

_BASE_URL = "https://jobicy.com/api/v2/remote-jobs"
_LOGGER = get_logger(__name__)

_JOB_TYPE_MAP: dict[str, str] = {
    "full-time": "full-time",
    "part-time": "part-time",
    "contract": "contract",
    "freelance": "contract",
    "internship": "internship",
    "temporary": "contract",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_date(raw: object) -> datetime | None:
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


class JobicySource(JobSource):
    def __init__(self, config: Config) -> None:
        self._config = config

    def fetch(self) -> list[Job]:
        try:
            data = get_json(_BASE_URL, params={"count": 50})
        except Exception as exc:
            _LOGGER.warning("Jobicy fetch failed: %s", exc)
            return []

        jobs_raw = data.get("jobs", []) if isinstance(data, dict) else []
        cutoff = _utcnow() - timedelta(hours=self._config.recency_hours)
        results: list[Job] = []

        for raw in jobs_raw:
            posted = _parse_date(raw.get("pubDate"))
            if posted is not None and posted < cutoff:
                continue

            job_types: list = raw.get("jobType") or []
            first_type = job_types[0].strip().lower() if job_types else ""
            employment_type = _JOB_TYPE_MAP.get(first_type)

            salary_min = raw.get("salaryMin")
            salary_max = raw.get("salaryMax")
            salary = (
                {
                    "min": salary_min,
                    "max": salary_max,
                    "currency": raw.get("salaryCurrency"),
                    "period": raw.get("salaryPeriod"),
                }
                if (salary_min is not None or salary_max is not None)
                else None
            )

            results.append(
                Job(
                    source="jobicy",
                    id=str(raw.get("id", "")),
                    title=str(raw.get("jobTitle", "")),
                    company=str(raw.get("companyName", "")),
                    location=normalize_location(raw.get("jobGeo")),
                    is_remote=True,
                    url=str(raw.get("url", "")),
                    salary=salary,
                    employment_type=employment_type,
                    posted_date=posted,
                    description=raw.get("jobDescription") or raw.get("jobExcerpt"),
                )
            )

        return results
