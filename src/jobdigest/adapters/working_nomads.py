from datetime import datetime, timedelta, timezone

from jobdigest.adapters.base import JobSource
from jobdigest.config import Config
from jobdigest.models import Job
from jobdigest.utils.dates import parse_date
from jobdigest.utils.http import get_json
from jobdigest.utils.location import normalize_location
from jobdigest.utils.logging import get_logger

_BASE_URL = "https://www.workingnomads.com/api/exposed_jobs/"
_LOGGER = get_logger(__name__)

_TAG_TYPE_MAP: dict[str, str] = {
    "contract": "contract",
    "freelance": "contract",
    "part-time": "part-time",
    "part time": "part-time",
    "internship": "internship",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _id_from_url(url: str) -> str:
    """Extract the numeric job ID from the Working Nomads job URL."""
    parts = [p for p in url.rstrip("/").split("/") if p]
    return parts[-1] if parts else url


def _employment_type(tags_str: str) -> str | None:
    tags = {t.strip().lower() for t in tags_str.split(",")}
    for tag, etype in _TAG_TYPE_MAP.items():
        if tag in tags:
            return etype
    return None


class WorkingNomadsSource(JobSource):
    def __init__(self, config: Config) -> None:
        self._config = config

    def fetch(self) -> list[Job]:
        try:
            data = get_json(_BASE_URL, params={"category": "development"})
        except Exception as exc:
            _LOGGER.warning("Working Nomads fetch failed: %s", exc)
            return []

        if not isinstance(data, list):
            _LOGGER.warning("Working Nomads unexpected response type: %s", type(data))
            return []

        cutoff = _utcnow() - timedelta(hours=self._config.recency_hours)
        results: list[Job] = []

        for raw in data:
            posted = parse_date(raw.get("pub_date"))
            if posted is not None and posted < cutoff:
                continue

            url = str(raw.get("url", ""))
            tags_str = raw.get("tags") or ""

            results.append(
                Job(
                    source="working_nomads",
                    id=_id_from_url(url),
                    title=str(raw.get("title", "")),
                    company=str(raw.get("company_name", "")),
                    location=normalize_location(raw.get("location")),
                    is_remote=True,
                    url=url,
                    salary=None,
                    employment_type=_employment_type(tags_str),
                    posted_date=posted,
                    description=raw.get("description"),
                )
            )

        return results
