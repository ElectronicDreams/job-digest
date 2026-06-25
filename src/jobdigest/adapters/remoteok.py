from datetime import datetime, timedelta, timezone

from jobdigest.adapters.base import JobSource
from jobdigest.config import Config
from jobdigest.models import Job
from jobdigest.utils.dates import parse_date
from jobdigest.utils.http import get_json
from jobdigest.utils.location import normalize_location
from jobdigest.utils.logging import get_logger

_BASE_URL = "https://remoteok.com/api"
_LOGGER = get_logger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _infer_employment_type(tags: list) -> str | None:
    tag_set = {t.lower() for t in tags}
    if "contract" in tag_set or "contractor" in tag_set or "freelance" in tag_set:
        return "contract"
    if "part-time" in tag_set or "part time" in tag_set:
        return "part-time"
    if "internship" in tag_set or "intern" in tag_set:
        return "internship"
    return "full-time"


class RemoteOkSource(JobSource):
    def __init__(self, config: Config) -> None:
        self._config = config

    def fetch(self) -> list[Job]:
        try:
            data = get_json(_BASE_URL)
        except Exception as exc:
            _LOGGER.warning("RemoteOK fetch failed: %s", exc)
            return []

        if not isinstance(data, list):
            _LOGGER.warning("RemoteOK unexpected response type: %s", type(data))
            return []

        cutoff = _utcnow() - timedelta(hours=self._config.recency_hours)
        results: list[Job] = []

        for raw in data:
            if not isinstance(raw, dict) or "slug" not in raw:
                continue

            posted = parse_date(raw.get("date"))
            if posted is not None and posted < cutoff:
                continue

            tags: list = raw.get("tags") or []

            salary_min = raw.get("salary_min")
            salary_max = raw.get("salary_max")
            salary = (
                {
                    "min": salary_min,
                    "max": salary_max,
                    "currency": "USD",
                    "period": "yearly",
                }
                if (salary_min or salary_max)
                else None
            )

            location_raw = raw.get("location") or "Worldwide"
            is_remote = True

            url = raw.get("apply_url") or raw.get("url") or ""

            results.append(
                Job(
                    source="remoteok",
                    id=str(raw.get("id", raw.get("slug", ""))),
                    title=str(raw.get("position", "")),
                    company=str(raw.get("company", "")),
                    location=normalize_location(location_raw),
                    is_remote=is_remote,
                    url=url,
                    salary=salary,
                    employment_type=_infer_employment_type(tags),
                    posted_date=posted,
                    description=raw.get("description"),
                )
            )

        return results
