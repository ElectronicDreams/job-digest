# CLAUDE.md

Guidance for Claude Code working in this repository. Read this file at the
start of every session before touching any code.

---

## Project overview

A Python tool that generates a daily ranked job digest as a local HTML page,
matched against a user's résumé profile. See `REQUIREMENTS.md` for the full
spec — that document is the source of truth for all product decisions. This
file covers *how to work in this repo*: conventions, architecture shorthand,
and the git workflow.

---

## Architecture quick-reference

- **`Job` dataclass** (`src/jobdigest/models.py`) is the universal contract.
  Every adapter normalizes its source payload into `Job`. Downstream code
  (gates, scorers, render) only ever consumes `Job` — never raw source data.

- **Adapters** (`src/jobdigest/adapters/`) — one file per source, each
  implementing the `JobSource` ABC (`adapters/base.py`). An adapter owns its
  endpoint, auth, quirks, and the translation into `Job`. Adding or fixing a
  source means touching one file only.

- **Scorers** (`src/jobdigest/core/scorers/`) — one file per ranking signal,
  each implementing the `Scorer` interface (`scorers/base.py`). A scorer must
  degrade gracefully: if its required data is absent, return 0 — never raise,
  never drop the job.

- **Shared mechanics** (HTTP retry, RSS parsing, date/location normalization,
  dedup keys, logging) live in `src/jobdigest/utils/`. Do not duplicate these
  across adapters. Do not push stateless helpers into base-class inheritance
  — keep the inheritance hierarchy shallow and purposeful.

- **Full repo layout** is in `REQUIREMENTS.md §11`. Follow it exactly when
  creating new files or directories. Do not invent new top-level modules.

---

## MVP scorer set

The following scorers are in scope for the MVP. Do not implement anything
outside this list — `applicant_count` and `close_date` are explicitly deferred
to v2+.

| Scorer | Weight | Notes |
|---|---|---|
| `closeness` | 30 | Title / seniority / tech proximity to profile |
| `skills_match` | 25 | Required skills overlap with profile skills |
| `experience_level` | 10 | Stated years / level vs profile seniority |
| `salary` | 10 | Salary vs profile floor; 0 if missing (flagged) |
| `freshness` | 15 | How recently the job was posted |
| `languages` | 5 | Required spoken languages vs profile |
| `employment_type` | 5 | Nudge toward preferred employment types |

Weights sum to 100. Configurable in `config.json`.

---

## Git workflow
- At the start of every session, sync with main before branching:
  git checkout main && git pull
  
- **Never commit directly to `main`.** It is branch-protected and requires a
  passing PR.

- For each issue, create a branch:

  git checkout -b feature/issue-<N>-<short-slug>

  e.g. `feature/issue-7-himalayas-adapter`

- When starting work on an issue, mark it in progress:

  gh issue edit <N> --add-label "status:in-progress"

- Implement the full acceptance criteria, including tests.

- Before pushing, run locally and confirm all three pass:

  ruff check . && ruff format --check . && pytest

- Commit using Conventional Commits format (see below).

- Push the branch and open a PR:

  gh pr create --fill

- Fill in the PR template fully — do not leave checklist items unchecked
  unless explicitly noted with a reason.

- Reference the issue with `Closes #<N>` in the PR body.

- **Do not merge the PR.** Wait for human review and approval.

---

## Commit message format — Conventional Commits

Format:

  <type>(<scope>): <short summary>

  - bullet describing what changed
  - another change
  - another change

**Types:** `feat`, `fix`, `test`, `refactor`, `chore`, `docs`, `ci`

**Scope:** the module or area affected, e.g. `himalayas`, `scoring`, `cli`,
`models`, `ci`

**Examples:**

  feat(himalayas): add Himalayas job source adapter

  - implement HimalayasSource extending JobSource ABC
  - normalize API response fields into Job dataclass
  - handle missing salary and location gracefully


  test(himalayas): add unit tests for Himalayas adapter

  - mock HTTP responses via pytest fixtures
  - cover happy path, missing fields, and HTTP error cases


  chore(ci): add ruff linting and format check to CI workflow

  - add ruff check and ruff format --check steps
  - runs on all PRs targeting main

---

## Testing conventions

- Tests live in `tests/`, mirroring `src/jobdigest/` structure.
  e.g. `tests/test_adapters/test_himalayas.py`

- Adapter tests use **mocked or fixture HTTP responses** — never make live API
  calls in tests.

- Every new adapter, scorer, or gate ships with tests in the same PR.

- Run the full suite (`pytest`), not just the new tests, before pushing.

---

## Code style

- Python >= 3.10; **type hints throughout**.

- `ruff` is the linter and formatter. All code must pass `ruff check .` and
  `ruff format --check .` before a PR is opened. CI enforces this on every PR.

- Prefer **dataclasses** for data structures (`Job`, `Profile`, etc.).

- Keep adapters and scorers **small and single-purpose**.

- Favor composition over deep inheritance hierarchies.

---

## Issue conventions

- One adapter + its tests = one issue.
- One scorer + its tests = one issue (trivially related scorers may be
  grouped if they share logic).
- Issues must be self-contained: acceptance criteria + links to relevant
  `REQUIREMENTS.md` sections, so a session can start cold without re-deriving
  context.

---

## Config & secrets

- `config.json` and `profile.json` are git-ignored. Only `*.example.json`
  versions are committed.

- **Never commit API keys, tokens, `.env` files, or any credentials.**

- When adding a new config option, update the corresponding `*.example.json`
  with a sensible placeholder or default value.

---

## GitHub CLI auth

Claude's GitHub identity uses a PAT stored in `.env` as `GITHUB_TOKEN`.
Source it at session start if `gh auth status` shows unauthenticated:

  export GITHUB_TOKEN=$(grep GITHUB_TOKEN .env | cut -d= -f2)
  gh auth login --with-token <<< "$GITHUB_TOKEN"

Confirm with:

  gh auth status

---

## Labels

All issues must have exactly one `type:` label and one `phase:` label applied
when the issue is created.

| Label | Meaning |
|---|---|
| `type:feature` | New functionality |
| `type:bug` | Something broken |
| `type:chore` | Infra, config, tooling, docs |
| `type:test` | Test-only work |
| `phase:0` | Scaffolding |
| `phase:1` | First adapter (Himalayas) |
| `phase:2` | Core pipeline |
| `phase:3` | Remaining adapters |
| `phase:4` | Scorers |
| `phase:5` | Onboarding |
| `phase:6` | Polish and README |
| `status:in-progress` | Added when work begins |
| `status:blocked` | Waiting on a dependency |

---

## Project board

The GitHub Project board uses built-in automation for status transitions.
Claude Code is only responsible for one manual transition — marking an issue
in progress when work begins (see Git workflow above). All other transitions
(Done, closed, merged) are handled automatically by GitHub.

Board columns: Backlog -> Ready -> In Progress -> In Review -> Done

---

## Roadmap — strictly out of MVP scope

Do not implement anything from this list. If a question arises about whether
something belongs in the MVP, default to no and flag it for human review.

**Deferred to v1.1:**
- TheirStack adapter
- Daily LLM scoring toggle

**Deferred to v2+:**
- `applicant_count` scorer
- `close_date` scorer
- Email delivery
- Web hosting / public URL
- Application tracking
- Dashboard
- Retention pruning
- Transit-time commute calculation
- Autonomous source discovery
- Adaptive learning
- Per-profile source selection
- Additional sources (Arbeitnow, Remotive, Arc.dev, HN, social signals)
