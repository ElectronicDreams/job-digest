# Daily Job Digest — Requirements (MVP)

> Working title — rename freely. A public, AI-first GitHub pet project.
> Target: a working MVP in one to two weeks.

This document is the merge of two planning passes. Where they conflicted, the **more recent** refined scope is the source of truth (concrete 5-source MVP, TheirStack at v1.1, 72h recency, `profile.json`, SQLite seen-jobs store); the earlier pass contributed the deeper **architecture** direction, re-normalized onto the `Job` model below.

---

## 1. Product & scope

A Python tool that **writes a daily ranked job digest** for any tech worker, at any level, matched to their own résumé and criteria — as a local, timestamped HTML page they open in a browser. Public, AI-first GitHub pet project; collaborators clone the repo, onboard with their own résumé, and get their own tailored digest. Also doubles as a Python-learning project and a portfolio artifact.

- **North-star goal:** surface **≥ 5 unique, recently-posted, well-targeted roles** each weekday morning — a target the source set is sized for, **not a quota**.
- **Quality over quantity:** never pad. An honest "nothing great today" is a valid, correct result.
- **Fully autonomous daily run** via cron / OS scheduler; non-interactive auth throughout.
- **No browser automation, no scraping.** RSS is *not* a scraper — it is structured, publisher-sanctioned data, and is allowed.

---

## 2. Onboarding & matching profile (`profile.json`)

- Interactive, run **once per person**, plus on-demand **refine / rebuild**.
- **Guided CLI command** (`onboard`) walks the user through it: résumé in → **one LLM call** parses a draft profile → **user confirms / edits** (parse-then-confirm) → written to `profile.json`. The LLM is required only here.
- Accepts résumés as **PDF, .docx, .txt, or pasted text**.
- The **onboarding LLM is configurable** (provider + model in `config.json`; see §3). It ships defaulting to a **hosted free tier** for a low-friction first run, with **local Ollama** documented as a private, self-hosted alternative (résumé text never leaves the machine).
- Text is **extracted locally** and sent to the LLM as plain text, so any provider works. Reliability ranks **paste / .txt / .docx (clean) > PDF (best-effort)** — multi-column or scanned PDFs may parse imperfectly; the parse-then-confirm step is the safety net. No OCR in the MVP (a no-text-layer PDF prompts the user to paste instead).
- `profile.json` is **human-readable, hand-editable, git-ignored**, and kept **separate from the SQLite store** and from operational config.
- **`rebuild`** = discard + regenerate. **`refine`** = additive union + dedup (never silently drops; the user hand-prunes the file).

**`profile.json` schema (MVP):**

| Field | Purpose |
|---|---|
| `title_variants[]` | Title synonyms; applied across **all** sources |
| `skills[]` | Skill / tech list for the skills-match signal |
| `seniority_terms[]`, `experience_terms[]` | Seniority / experience matching |
| `location` | Home metro (drives the same-metro gate) |
| `acceptable_locations[]` | Explicit allow-list of locations / remote scopes |
| `work_types[]` | `onsite` / `hybrid` / `remote` accepted |
| `work_authorization` | e.g. "Authorized to work in Canada" (drives the remote-eligibility gate) |
| `salary_floor` | `{ amount, currency }` minimum |
| `employment_types[]` | e.g. `permanent`, `contract` (no solo freelance) |

---

## 3. Configuration (`config.json`) & CLI

Operational settings live in **`config.json`** — separate from the personal `profile.json`. (We standardize on JSON since the profile already uses it.)

```jsonc
{
  "recency_hours": 72,                // configurable freshness window
  "min_score": 50,                    // 0–100 cutoff; jobs below are omitted
  "output_dir": "./output",
  "enabled_sources": ["adzuna", "himalayas", "remoteok", "jobicy", "working_nomads"],
  "weights": {                        // pluggable scorer weights (sum to 100)
    "closeness": 25, "skills_match": 20, "experience_level": 10,
    "salary": 10, "freshness": 15, "languages": 5,
    "applicant_count": 5, "close_date": 5, "employment_type": 5
  },
  "onboarding_llm": {                 // OpenAI-compatible; swap provider in config, no code change
    "provider": "gemini",             // DEFAULT: a hosted free tier (no credit card)
    "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "model": "gemini-2.5-flash",      // verify exact name/price at build; any cheap small model is plenty
    "api_key_env": "GEMINI_API_KEY"   // e.g. local Ollama → base_url http://localhost:11434/v1, key unused
  },
  "daily_llm_scoring": { "enabled": false, "model": null },  // off by default (effectively v1.1)
  "log_level": "INFO"
}
```

**CLI commands (entry point, e.g. `python -m jobdigest …`):**

- **`onboard`** — guided, interactive; builds / refines / rebuilds `profile.json`. Guides the user at every step.
- **`run`** — the daily pipeline (this is what the scheduler triggers).
- **First-run guard:** if `profile.json` does **not** exist, `run` does **not** execute the pipeline. Instead it detects the missing profile and **guides the user to run `onboard` first**, then exits.

Both `config.json` and `profile.json` ship as committed **`*.example.json`** files; the live copies are git-ignored (same pattern as `.env` / `.env.example`).

---

## 4. Sources & adapters

- **Programmatic access only — APIs + RSS. No scrapers in the MVP.**
- Mixed adapter mechanisms are fine — easiest viable mechanism per source.
- ~90% remote roles accepted; **no** local-Indeed-scraper exception.

### MVP core — 5 sources, all queried every run (no per-profile selection)

| Source | Access | Notes |
|---|---|---|
| **Adzuna Canada** | static-key REST | the only local-Toronto source |
| **Himalayas** | no-auth JSON | contractor filter + CAD salary · attribution link-back required \* |
| **RemoteOK** | no-auth JSON | tag-based |
| **Jobicy** | no-auth JSON | full JD in payload |
| **Working Nomads** | RSS | North-America filter + contract coverage |

\* If Himalayas listings are displayed, include a visible link back to **himalayas.app** crediting it as the source (their public-data terms).

- **Excluded (scraper-dependent):** Indeed, Glassdoor, Google Jobs, Dice, Wellfound.
- **Never-list:** Contra, Twine, SkipTheDrive, VirtualVocations, JustRemote.
- **Vetting gate** (any source, now or future): working API/RSS (not a 403 / login wall) · NA tech coverage incl. global-remote-into-NA · range of roles & seniority levels · clean, free access terms.

---

## 5. Data model — the common `Job`

Each adapter normalizes its raw payload into one `Job`:

`source` · `id` · `title` · `company` · `location` · `is_remote` · `salary` *(nullable + flagged)* · `employment_type` · `url` · `posted_date` · `description`

- Missing fields → `null` and **flagged in the HTML** (missing ≠ zero).
- `employment_type` is a **ranking signal, not a gate.**
- Downstream (gates → ranking → render) consumes only `Job`, never raw source data.

---

## 6. Architecture (cross-cutting)

**Source layer — Adapter pattern.** A `JobSource` abstract base class (`abc.ABC`) defines the interface — essentially `fetch() -> list[Job]`. One concrete adapter per source (`AdzunaSource`, `HimalayasSource`, `RemoteOkSource`, `JobicySource`, `WorkingNomadsRssSource`; `TheirStackSource` arrives at v1.1). Each adapter owns only its endpoint, auth, quirks, and the translation into `Job`, so adding / debugging / fixing a source is isolated to a single file. **The normalization contract — every adapter returns `Job` — is what protects the whole pipeline from each source's mess.**

**DRY via shared infrastructure.** Repeated mechanics (HTTP-with-retry, RSS parsing, date / location normalization, dedup-key generation, logging) are centralized in base-class helpers and a `utils` module. Inheritance is reserved for the genuine *is-a* contract to keep the hierarchy shallow; stateless helpers live in `utils`, not the class tree (no inheritance overreach). A **source registry** declares the active adapters; the daily **runner** iterates the registry.

**Ranking mirrors the source layer.** A weighted, **pluggable scoring system**: each signal is an independent scorer contributing **only when its data exists** (missing = zero, never a crash, never a drop). Weights are tunable now (in `config.json`) and learnable later — the seam where v2 adaptive learning plugs in. Both layers extend by adding one isolated unit: a new source is a new adapter in the registry; a new signal is a new scorer with a weight.

**LLM access — provider unit.** The onboarding parse goes through a thin, **OpenAI-compatible `LLMProvider`** (one small unit, same spirit as the adapters). `provider` / `base_url` / `model` / `api_key_env` come from `config.json`, so switching between a hosted free tier, a cheap paid model, or **local Ollama** (any OpenAI-compatible endpoint) is configuration, not code. Most providers speak this format directly; Gemini and Anthropic expose compatible endpoints.

---

## 7. Daily-run pipeline

1. **First-run guard** — no `profile.json` → guide user to `onboard`, exit.
2. **Fetch** — runner iterates the registry; each adapter returns `list[Job]`. **Recency**: configurable, **default 72h** (server-side where supported, else client-side on `posted_date`).
3. **Resilience** — a per-source failure → **skip + log + banner** in the result HTML. One flaky source never zeroes the morning.
4. **Dedup** — key = `(company, title, rolling-7-day bucket of posted_date)`.
5. **Cross-run state — SQLite seen-jobs store** — makes runs **idempotent**; only genuinely-new postings surface each morning. Also the debug / data store. *Dedup ledger only — not the v2 application tracker.*
6. **Gate** — drop failing jobs (§8).
7. **Score & select** — score each survivor **0–100** via the weighted scorers; **omit anything below `min_score` (default 50, configurable)**; show all remaining, **ranked descending**.
8. **Render** — write the timestamped HTML digest (§9).

---

## 8. Gates & ranking

**Hard gates (drop the job):**

- **Same-metro** for on-site / hybrid — the cheap "is it in the region" check, no maps / transit API.
- **Best-effort remote eligibility** from posting text — unknown = keep + flag **"work authorization unclear."**
- **Loose** seniority / title / tech match — in the neighborhood, not exact.

**Ranking — heuristic at run time (no LLM in MVP), normalized 0–100:**
tech / title / seniority closeness · required-skills match *(Tier A — in)* · per-tech experience level when stated · salary *(flag if missing)* · freshness · required languages · applicant count · close date · `employment_type` nudge.

**Selection rule:** gates drop; all gate-survivors are scored and shown **ranked**, with a **minimum-score cutoff (`min_score`, default 50/100, configurable)** removing weak matches — this is what keeps "never padded" real. An optional **daily-LLM scoring toggle** exists but is **off by default** (effectively v1.1).

---

## 9. Output

- Local **static HTML**, **timestamped & non-overwriting:** `digest-YYYY-MM-DD_HHMM.html` (sorts chronologically, Windows-safe). All runs preserved; an **"open latest"** shortcut is the view button.
- **One card per posting:** title · company · location · work type · matched tech · salary-or-flag · freshness · applicant / close info · apply link.
- **No email in the MVP.**

---

## 10. Stack, cost & repo hygiene

- **Python + OS scheduler**; cross-platform — Windows 11 (native / WSL2), Linux, macOS, or a cheap VM. Low cost throughout, favoring free tiers.
- **LLM default & cost:** ships pointed at a **hosted free tier** (no credit card) so onboarding works after the user grabs one free key. Because the onboarding call is a tiny, once-per-person résumé→JSON task, **model quality is not the constraint — cost / privacy / availability are**, and any small modern model handles it for a fraction of a cent (or free).
- **Repo hygiene from commit one:** clean layout · `requirements.txt` / `pyproject.toml` · `.env.example` committed, `.env` git-ignored · config separated from code.
- **README (an explicit deliverable)** must contain:
  - **Manual run / schedule / view steps** for all three environments (Windows 11 native & WSL2, Linux, macOS), including the browser **"open latest"** shortcut, plus a short **troubleshooting** section.
  - **A "pick your model" section** capturing the LLM cost-and-options landscape (verify exact names/prices at build, since they shift):
    - *Hosted free tiers* — Google **Gemini Flash** (the most generous; no card; daily quota far exceeds a once-per-person call) is the shipped default; **Groq** (fast small models, no card) and **OpenRouter** (free DeepSeek / Llama / Gemma models) as alternatives. All are rate-limited dev tiers, ample for onboarding.
    - *Cheap paid* — the smallest "nano / mini / flash / small"-class models sit around ~$0.10 / 1M input tokens; a résumé parse is a few thousand tokens, so effectively pennies-or-less.
    - *How to switch* — the `onboarding_llm` block in `config.json` (`provider` / `base_url` / `model` / `api_key_env`); no code change.
  - **A comprehensive self-hosted (Ollama) guide** for the privacy route — résumé text never leaves the machine: installing Ollama per OS, pulling a small model (e.g. a compact Qwen / Llama / Mistral), pointing `base_url` to `http://localhost:11434/v1` with the local model name, RAM/hardware notes, and a link to the official Ollama docs.
  - **Model-access caveat:** **Claude Pro ≠ API access** — a hosted model needs its own pay-as-you-go (or free-tier) key, separate from any Claude subscription.

---

## 11. Repository / package layout

`src`-layout, idiomatic and installable; per-source isolation and shared utils made physical.

```
job-digest/
├── README.md
├── REQUIREMENTS.md
├── pyproject.toml                 # (or requirements.txt)
├── .gitignore                     # .env, profile.json, config.json, data/, output/, __pycache__
├── .env.example                   # Adzuna app_id/app_key; LLM key (default GEMINI_API_KEY, free tier)
├── config.example.json            # operational defaults → copy to config.json (git-ignored)
├── profile.example.json           # sample profile → produced/edited via `onboard` (git-ignored)
├── scripts/
│   ├── open_latest.bat            # Windows view shortcut
│   └── open_latest.sh             # Linux/macOS view shortcut
├── data/                          # git-ignored runtime state
│   └── seen_jobs.sqlite
├── output/                        # git-ignored; timestamped digests land here
│   └── digest-YYYY-MM-DD_HHMM.html
├── src/
│   └── jobdigest/
│       ├── __init__.py
│       ├── __main__.py            # CLI entry: dispatch onboard / run
│       ├── cli.py                 # arg parsing, first-run guard
│       ├── config.py              # load + validate config.json / profile.json
│       ├── models.py              # Job dataclass, Profile schema
│       ├── registry.py            # active adapter registry
│       ├── runner.py              # daily pipeline orchestration
│       ├── adapters/
│       │   ├── __init__.py
│       │   ├── base.py            # JobSource ABC + shared base-class helpers
│       │   ├── adzuna.py
│       │   ├── himalayas.py
│       │   ├── remoteok.py
│       │   ├── jobicy.py
│       │   ├── working_nomads.py  # RSS
│       │   └── theirstack.py      # v1.1 — present but not registered by default
│       ├── core/
│       │   ├── __init__.py
│       │   ├── gates.py           # hard gates
│       │   ├── dedup.py           # dedup key
│       │   ├── store.py           # SQLite seen-jobs store
│       │   ├── ranking.py         # orchestrates scorers → 0–100, applies min_score
│       │   └── scorers/           # one pluggable scorer per signal
│       │       ├── __init__.py
│       │       ├── base.py        # Scorer interface
│       │       ├── closeness.py
│       │       ├── skills.py
│       │       ├── experience.py
│       │       ├── salary.py
│       │       ├── freshness.py
│       │       ├── languages.py
│       │       └── employment_type.py
│       ├── onboarding/
│       │   ├── __init__.py
│       │   ├── resume.py          # PDF / .docx / .txt / paste extraction
│       │   ├── llm.py             # LLM call → draft profile (model from config)
│       │   └── interactive.py     # guided confirm/edit flow
│       ├── render/
│       │   ├── __init__.py
│       │   ├── html.py            # digest builder + failure banner
│       │   └── templates/         # card + page templates
│       └── utils/
│           ├── __init__.py
│           ├── http.py            # HTTP with retry
│           ├── rss.py             # RSS parsing
│           ├── dates.py           # date normalization
│           ├── location.py        # location normalization
│           └── logging.py
└── tests/
    ├── __init__.py
    ├── test_adapters/
    ├── test_gates.py
    ├── test_ranking.py
    └── test_dedup_store.py
```

---

## 12. Roadmap — explicitly out of the MVP

**v1.1**
- **TheirStack** adapter — Bearer key, credit-metered; unique ATS-direct coverage (Lever / Greenhouse / Ashby / Workday).
- Optional **daily-LLM scoring** (+ its configurable model).

**v2+**
- **More sources:** Arbeitnow · Remotive · Arc.dev · HN "Who's Hiring" · Mastodon / Bluesky social signals.
- **Delivery:** email (Gmail App Password / SMTP) · hosted / public URL.
- **Housekeeping & UI:** retention pruning (keep last *X* digests, auto-prune) · dashboard · application tracking · transit-time commute calc.
- **Intelligence:** autonomous source discovery · adaptive source-learning · per-profile source selection.
- **Enrichment signals:** company size · industry · company tech stack · ratings / funding · LinkedIn / Indeed.

---

## 13. Definition of done (week two)

A collaborator of any tech role or level:

1. clones the repo,
2. drops in their résumé + config,
3. runs `onboard` to a confirmed profile, and
4. a scheduled `run` pulls the 5 vetted sources → **gates → scores (0–100, ≥ `min_score`) → writes** a clean, timestamped HTML digest with apply links —

…showing only genuine matches, and honest when there are few.
