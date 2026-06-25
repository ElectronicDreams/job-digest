import math
import os
from datetime import datetime, timezone

from jobdigest.adapters.base import JobSource
from jobdigest.config import Config
from jobdigest.models import Job
from jobdigest.utils.dates import parse_date
from jobdigest.utils.http import get_json
from jobdigest.utils.location import normalize_location
from jobdigest.utils.logging import get_logger

_BASE_URL = "https://api.adzuna.com/v1/api/jobs/ca/search/1"
_LOGGER = get_logger(__name__)

_REMOTE_KEYWORDS = frozenset(
    ["remote", "work from home", "wfh", "fully remote", "télétravail"]
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _detect_remote(title: str, description: str) -> bool:
    combined = f"{title} {description}".lower()
    return any(kw in combined for kw in _REMOTE_KEYWORDS)


def _employment_type(contract_type: str, contract_time: str) -> str | None:
    if contract_type == "contract":
        return "contract"
    if contract_time == "full_time":
        return "full-time"
    if contract_time == "part_time":
        return "part-time"
    return None


class AdzunaSource(JobSource):
    def __init__(self, config: Config) -> None:
        self._config = config
        self._app_id = os.environ.get("ADZUNA_APP_ID", "")
        self._app_key = os.environ.get("ADZUNA_APP_KEY", "")

    def fetch(self) -> list[Job]:
        if not self._app_id or not self._app_key:
            _LOGGER.warning(
                "Adzuna credentials not set (ADZUNA_APP_ID / ADZUNA_APP_KEY); skipping"
            )
            return []

        params = {
            "app_id": self._app_id,
            "app_key": self._app_key,
            "results_per_page": 50,
            "category": "it-jobs",
            "max_days_old": math.ceil(self._config.recency_hours / 24),
        }

        try:
            data = get_json(_BASE_URL, params=params)
        except Exception as exc:
            _LOGGER.warning("Adzuna fetch failed: %s", exc)
            return []

        results_raw = data.get("results", []) if isinstance(data, dict) else []
        results: list[Job] = []

        for raw in results_raw:
            title = str(raw.get("title", ""))
            description = str(raw.get("description") or "")
            company = (raw.get("company") or {}).get("display_name", "")
            location_display = (raw.get("location") or {}).get("display_name", "")

            salary_min = raw.get("salary_min")
            salary_max = raw.get("salary_max")
            salary = (
                {
                    "min": salary_min,
                    "max": salary_max,
                    "currency": "CAD",
                    "period": "yearly",
                }
                if (salary_min is not None or salary_max is not None)
                else None
            )

            employment_type = _employment_type(
                raw.get("contract_type") or "",
                raw.get("contract_time") or "",
            )

            results.append(
                Job(
                    source="adzuna",
                    id=str(raw.get("id", "")),
                    title=title,
                    company=str(company),
                    location=normalize_location(location_display),
                    is_remote=_detect_remote(title, description),
                    url=str(raw.get("redirect_url", "")),
                    salary=salary,
                    employment_type=employment_type,
                    posted_date=parse_date(raw.get("created")),
                    description=description or None,
                )
            )

        return results
