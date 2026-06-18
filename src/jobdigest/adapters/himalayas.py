from datetime import datetime, timedelta, timezone

from jobdigest.adapters.base import JobSource
from jobdigest.config import Config
from jobdigest.models import Job
from jobdigest.utils.http import get_json
from jobdigest.utils.location import normalize_location
from jobdigest.utils.logging import get_logger

_BASE_URL = "https://himalayas.app/jobs/api"
_LOGGER = get_logger(__name__)

_EMPLOYMENT_TYPE_MAP: dict[str, str] = {
    "full-time": "full-time",
    "fulltime": "full-time",
    "part-time": "part-time",
    "parttime": "part-time",
    "contractor": "contract",
    "contract": "contract",
    "freelance": "contract",
    "internship": "internship",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_pubdate(raw_value: object) -> datetime | None:
    if isinstance(raw_value, (int, float)):
        return datetime.fromtimestamp(raw_value, tz=timezone.utc)
    return None


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
            posted = _parse_pubdate(raw.get("pubDate"))
            if posted is not None and posted < cutoff:
                continue

            min_sal = raw.get("minSalary")
            max_sal = raw.get("maxSalary")
            salary = (
                {
                    "min": min_sal,
                    "max": max_sal,
                    "currency": raw.get("currency"),
                    "period": raw.get("salaryPeriod"),
                }
                if (min_sal is not None or max_sal is not None)
                else None
            )

            restrictions: list = raw.get("locationRestrictions") or []
            first_loc = restrictions[0] if restrictions else "Remote"
            location_str = normalize_location(first_loc)

            job_type_raw = (raw.get("employmentType") or "").strip().lower()
            employment_type = _EMPLOYMENT_TYPE_MAP.get(job_type_raw)

            results.append(
                Job(
                    source="himalayas",
                    id=str(raw.get("guid", raw.get("applicationLink", ""))),
                    title=str(raw.get("title", "")),
                    company=str(raw.get("companyName", "")),
                    location=location_str,
                    is_remote=True,
                    url=str(raw.get("applicationLink", raw.get("guid", ""))),
                    salary=salary,
                    employment_type=employment_type,
                    posted_date=posted,
                    description=raw.get("description") or raw.get("excerpt"),
                )
            )

        return results
