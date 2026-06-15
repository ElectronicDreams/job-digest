before a PR is opened. CI enforces this on every PR.

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

```bash
export GITHUB_TOKEN=$(grep GITHUB_TOKEN .env | cut -d= -f2)
gh auth login --with-token <<< "$GITHUB_TOKEN"
```

Confirm with:

```bash
gh auth status
```

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

Board columns: `Backlog` → `Ready` → `In Progress` → `In Review` → `Done`