import contextlib
from datetime import datetime, timezone
from pathlib import Path

from jobdigest import registry
from jobdigest.config import Config
from jobdigest.core.dedup import make_dedup_key
from jobdigest.core.gates import apply_gates
from jobdigest.core.ranking import rank_jobs
from jobdigest.core.store import SeenJobsStore
from jobdigest.models import Job, Profile
from jobdigest.render.html import render_digest
from jobdigest.utils.logging import get_logger

_LOGGER = get_logger(__name__)


def run(
    config: Config,
    profile: Profile,
    db_path: Path | None = None,
) -> Path:
    if db_path is None:
        db_path = Path("data") / "seen.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    all_jobs: list[Job] = []
    failed_sources: list[str] = []

    for source_class in registry.SOURCES:
        try:
            jobs = source_class(config).fetch()
            all_jobs.extend(jobs)
        except Exception as exc:
            name = source_class.__name__
            _LOGGER.warning("Source %s failed: %s", name, exc)
            failed_sources.append(name)

    with contextlib.closing(SeenJobsStore(db_path)) as store:
        new_jobs = [j for j in all_jobs if store.is_new(make_dedup_key(j))]
        gated = apply_gates(new_jobs, profile, config)
        ranked = rank_jobs(gated, profile, config)
        for job in ranked:
            store.mark_seen(make_dedup_key(job))

    html = render_digest(ranked, failed_sources, config)

    config.output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
    out_path = config.output_dir / f"digest-{ts}.html"
    out_path.write_text(html, encoding="utf-8")

    _LOGGER.info("Digest written to %s (%d jobs)", out_path, len(ranked))
    return out_path
