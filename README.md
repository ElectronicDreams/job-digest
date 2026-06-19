# Job Digest

A Python tool that generates a daily ranked job digest as a local HTML page, matched against your résumé profile. It pulls job postings from free APIs, scores them against your skills and preferences, deduplicates across runs, and writes a self-contained HTML file you can open in any browser.

> **Current state:** Only the [Himalayas](https://himalayas.app) source adapter is implemented. Additional sources (RemoteOK, Jobicy, Working Nomads, Adzuna) are coming in a later phase.

---

## Requirements

- Python 3.10 or later
- pip (bundled with Python 3.10+)

---

## Environment setup

### Linux

Python 3.10+ is available in most distribution package managers.

```bash
# Debian / Ubuntu
sudo apt update && sudo apt install python3 python3-pip python3-venv

# Fedora
sudo dnf install python3 python3-pip
```

### macOS

Install Python via [Homebrew](https://brew.sh):

```bash
brew install python
```

Verify:

```bash
python3 --version   # should be 3.10+
```

### Windows 11 with WSL2 (recommended)

Open your WSL2 terminal (Ubuntu is the most common distribution) and follow the Linux instructions above. All subsequent commands in this guide should be run inside the WSL2 shell.

### Windows 11 without WSL2

1. Download Python 3.10+ from [python.org](https://www.python.org/downloads/).
2. During installation, check **"Add Python to PATH"**.
3. Open **Command Prompt** or **PowerShell** for all commands below.
4. Replace `python3` with `python` and forward slashes with backslashes where noted.

---

## First-time setup

### 1. Clone the repository

```bash
git clone https://github.com/ElectronicDreams/job-digest.git
cd job-digest
git checkout pre-release-test-himalayas-only
```

> This branch contains the Himalayas adapter and the core pipeline in a tested, working state. The `main` branch is under active development and may be ahead of what is documented here.

### 2. Create and activate a virtual environment

**Linux / macOS / WSL2:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (Command Prompt):**

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Python dependencies

```bash
pip install -e .
```

This reads `pyproject.toml` and installs all required packages (`requests`, `feedparser`, `nh3`) into the virtual environment.

### 4. Create your config file

Copy the example and edit it to suit your situation:

```bash
cp config.example.json config.json
```

Open `config.json`. For a first run, the most important fields are:

| Field | What to set |
|---|---|
| `recency_hours` | How far back to fetch jobs (e.g. `72` for 3 days) |
| `min_score` | Minimum score (0–100) a job must reach to appear in the digest. Start with `0` to see all results, raise it later. |
| `output_dir` | Where the HTML digest is written (default: `./output`) |
| `exclusion_phrases` | See the [Gates](#gates-and-no-results) section below — leave as `[]` on a first run |

For now, leave `enabled_sources` containing only `"himalayas"` — the other sources are not yet implemented.

### 5. Create your profile file

Copy the example and edit it to match your background:

```bash
cp profile.example.json profile.json
```

Fill in your real job titles, skills, location, and salary floor. See `profile.example.json` for the expected shape of each field.

> **Tip for a first run:** If you are not sure your profile is configured correctly, temporarily clear `title_variants`, `skills`, and `seniority_terms` (set them to `[]`). This disables the title gate so all fetched jobs pass through, letting you verify that the source is returning results before tuning your profile.

---

## Running the digest

Make sure your virtual environment is activated, then:

```bash
python -m jobdigest run
```

The tool will:
1. Fetch jobs from Himalayas (up to 100 postings, filtered to `recency_hours`)
2. Deduplicate against jobs seen in previous runs (`data/seen.db`)
3. Apply hard gates (see below)
4. Score and rank the passing jobs
5. Write the digest to `output/digest-<timestamp>.html`

The path to the generated file is printed at the end.

### Deduplication and the second run

Jobs that appear in the digest are recorded in `data/seen.db` so they are not shown again on the next run. This means:

- **First run:** up to 100 recent jobs may appear.
- **Second run:** only jobs posted since the last run (that haven't been seen before) will appear, so the digest may be empty or much shorter.

If you want to re-see all jobs from the first run (for example, after changing your profile), delete the database and run again:

```bash
rm data/seen.db
python -m jobdigest run
```

---

## Viewing the digest

Open the generated HTML file in your browser:

**Linux / WSL2:**

```bash
xdg-open output/digest-*.html
```

Or navigate to the `output/` folder in your file manager and double-click the file.

**macOS:**

```bash
open output/digest-*.html
```

**Windows (from WSL2):**

```bash
explorer.exe "$(wslpath -w output/digest-*.html)"
```

**Windows (native):**

Navigate to the `output\` folder in File Explorer and double-click the `.html` file.

---

## Gates and no results

Three hard gates filter jobs before scoring. If your digest is empty, one of these is likely the cause:

| Gate | What it checks | How to relax it |
|---|---|---|
| **Title gate** | Job title shares at least one token with your `title_variants`, `skills`, or `seniority_terms` | Add more variants, or temporarily set all three to `[]` |
| **Metro gate** | Job location matches your `location` or `acceptable_locations` — remote jobs always pass | Add more locations, or ensure `is_remote` jobs are coming through (Himalayas is remote-only, so all jobs pass this gate automatically) |
| **Eligibility gate** | Job description does not contain any phrase from `exclusion_phrases` | Set `exclusion_phrases` to `[]` in `config.json` to disable this gate entirely |

**Recommended debugging steps if no results appear:**

1. Set `exclusion_phrases` to `[]` in `config.json`.
2. Set `title_variants`, `skills`, and `seniority_terms` to `[]` in `profile.json`.
3. Set `min_score` to `0` in `config.json`.
4. Delete `data/seen.db` and run again.

If jobs now appear, re-enable each filter one at a time to find which one is too restrictive.
