from datetime import datetime, timezone

from jobdigest.models import Job

_BUCKET_SECONDS = 7 * 86400


def make_dedup_key(job: Job) -> str:
    if job.posted_date is not None:
        bucket = int(job.posted_date.timestamp()) // _BUCKET_SECONDS
    else:
        bucket = int(datetime.now(timezone.utc).timestamp()) // _BUCKET_SECONDS

    company = (job.company or "").strip().lower()
    title = (job.title or "").strip().lower()
    return f"{company}|{title}|{bucket}"
