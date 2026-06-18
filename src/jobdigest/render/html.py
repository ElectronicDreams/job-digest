from datetime import datetime, timezone

from jobdigest.config import Config
from jobdigest.models import Job

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: system-ui, sans-serif; background: #f5f5f5; color: #222;
       padding: 1.5rem; }
h1 { font-size: 1.4rem; margin-bottom: 1rem; }
.banner { background: #fff3cd; border: 1px solid #ffc107; border-radius: 6px;
          padding: 0.75rem 1rem; margin-bottom: 1rem; }
.empty  { color: #666; margin-top: 1rem; }
.count  { color: #555; font-size: 0.9rem; margin-bottom: 1rem; }
.cards  { display: flex; flex-direction: column; gap: 0.75rem; }
.card   { background: #fff; border: 1px solid #ddd; border-radius: 8px;
          padding: 1rem 1.25rem; }
.card h2 { font-size: 1.05rem; margin-bottom: 0.35rem; }
.card h2 a { text-decoration: none; color: #1a0dab; }
.card h2 a:hover { text-decoration: underline; }
.meta   { font-size: 0.85rem; color: #555; margin-bottom: 0.4rem; }
.meta span + span::before { content: " · "; }
.salary { font-size: 0.9rem; margin-bottom: 0.3rem; }
.salary.missing { color: #b45309; }
.desc   { font-size: 0.82rem; color: #444; margin-top: 0.4rem;
          display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;
          overflow: hidden; }
.attribution { font-size: 0.78rem; color: #888; margin-top: 0.4rem; display: block; }
.attribution a { color: #888; }
"""


def _freshness(posted_date: datetime | None) -> str:
    if posted_date is None:
        return "Unknown age"
    delta = datetime.now(timezone.utc) - posted_date
    hours = int(delta.total_seconds() / 3600)
    if hours < 1:
        return "just now"
    if hours < 24:
        return f"{hours}h ago"
    return f"{hours // 24}d ago"


def _salary_html(salary: dict | None) -> str:
    if salary is None:
        return '<span class="salary missing">&#x26A0; Salary not listed</span>'
    lo = salary.get("min")
    hi = salary.get("max")
    cur = salary.get("currency", "")
    if lo and hi:
        return f'<span class="salary">{cur} {lo:,} – {hi:,}</span>'
    if lo:
        return f'<span class="salary">{cur} {lo:,}+</span>'
    return '<span class="salary missing">&#x26A0; Salary not listed</span>'


def _card_html(job: Job) -> str:
    work_type = job.employment_type or "—"
    location = job.location or "—"
    remote_tag = (
        " (remote)" if job.is_remote and "remote" not in location.lower() else ""
    )
    desc_html = ""
    if job.description:
        desc_html = f'<div class="desc">{job.description}</div>'
    attribution = ""
    if job.source == "himalayas":
        attribution = (
            '<span class="attribution">'
            'via <a href="https://himalayas.app">himalayas.app</a>'
            "</span>"
        )
    return f"""<div class="card">
  <h2><a href="{job.url}">{job.title}</a></h2>
  <div class="meta">
    <span>{job.company}</span>
    <span>{location}{remote_tag}</span>
    <span>{work_type}</span>
    <span>{_freshness(job.posted_date)}</span>
  </div>
  {_salary_html(job.salary)}
  {desc_html}
  {attribution}
</div>"""


def render_digest(jobs: list[Job], failed_sources: list[str], config: Config) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    date_str = ts[:10]

    banner = ""
    if failed_sources:
        names = ", ".join(failed_sources)
        banner = f'<div class="banner">&#x26A0; Sources with errors: {names}</div>\n  '

    count_label = f"{len(jobs)} new job{'s' if len(jobs) != 1 else ''} found"
    count_html = f'<p class="count">{count_label}</p>'

    if jobs:
        cards_html = "\n  ".join(_card_html(j) for j in jobs)
    else:
        cards_html = '<p class="empty">No new jobs matched your profile today.</p>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Job Digest – {date_str}</title>
  <style>{_CSS}</style>
</head>
<body>
  <h1>Job Digest – {ts}</h1>
  {banner}{count_html}
  <div class="cards">
  {cards_html}
  </div>
</body>
</html>"""
