# Lead Personalization

B2B cold email personalization workspace. Researches leads from CSV, writes hyper-personalized 3-email sequences, and exports enriched files for any ESP.

The copy engine is deterministic: emails are assembled from versioned **offer packs** (variant pools + subject templates) selected by a stable per-lead hash, driven by research signals. There is **no LLM call per lead**.

## Setup (one-time)

```bash
# Python deps + install the library (editable)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .

# Node deps + headless Chromium for website research (render fallback)
npm install && npm run playwright:install

# API keys are OPTIONAL (Apify = LinkedIn posts, Reoon = email verification).
# The core pipeline needs none of them.
cp .env.example .env   # then fill in your keys
```

## Core library

`lead_personalization/` is an installable package (`pip install -e .`) you can call from scripts or an external orchestrator (e.g. n8n):

| Module | Purpose |
|--------|---------|
| `config.py` | Paths, feature flags, API keys (replaces hardcoded `ROOT`) |
| `offer_pack.py` + `offer_packs/*.json` | Versioned copy packs (pools + subject templates) |
| `research.py` / `renderers.py` | Fetch + tiered render + signal classification |
| `copywriter.py` | Deterministic 3-email sequence generation |
| `pipeline.py` | `normalize_rows`, `personalize_rows` (in-memory primitives) |
| `qa.py` / `sanitize.py` / `subjects.py` / `segments.py` / `linkedin.py` | Supporting logic |

Run the tests (includes a parity test proving the JSON offer pack reproduces the legacy engine's copy byte-for-byte):

```bash
.venv/bin/python -m pytest -q
```

## Quick start

1. **Add your lead list** — drop a CSV in `leads/` (e.g. `leads/my-list.csv`)
2. **Verify emails** (optional, max 500/day) — `python3 scripts/verify_emails_reoon.py leads/my-list.csv`
3. **Confirm sender context** — edit `OFFER.md` and `BRAND_IDENTITY.md` at project root
4. **Run in Cursor agent chat:**

   ```text
   Personalize leads/my-list.csv — pilot 50 leads first. Confirm your plan before running.
   ```

The agent follows the [lead-email-personalization](.cursor/skills/lead-email-personalization/SKILL.md) skill automatically.

## Project layout

```text
Lead-Personalization/
├── OFFER.md                 # What you sell (required for copy)
├── BRAND_IDENTITY.md        # Tone and positioning (required)
├── requirements.txt         # Python deps (install into .venv)
├── leads/                   # Input CSVs + normalized + enriched outputs (data, gitignored)
│   ├── pipeline/<slug>/     # Per-list Drive-pipeline working dirs
│   └── enriched/            # Per-batch enriched CSVs
├── campaigns/               # Manifest, research JSON, copy JSON (data, gitignored)
├── copy/                    # Markdown reviews + JSON exports (data, gitignored)
├── .pipeline/state.json     # Drive pipeline state (runtime, gitignored)
├── scripts/
│   ├── pipeline/            # Drive orchestrator: run_pipeline.py + report.py
│   ├── verify_emails_reoon.py       # Reoon email verification (500/day cap)
│   ├── split_leads_by_category.py   # Split mixed CSV into per-category files
│   ├── personalization/     # Core pipeline (normalize, batch, QA, merge)
│   └── archive/             # Legacy one-off scripts from past campaigns
├── .cursor/
│   ├── skills/              # Agent skills (lead-email-personalization, playwright-cli)
│   └── rules/               # Auto-apply workflow rule
├── .agents/skills/          # Skills installed via `npx skills add`
├── docs/reference/          # Research notes and reference material
└── archive/                 # Past campaign outputs (read-only)
```

## Drive pipeline (one command)

`scripts/pipeline/run_pipeline.py` is a resumable orchestrator that drives **every** lead list in Google Drive from raw export to personalized sequences, syncing each stage back to Drive. Run it once a day:

```bash
.venv/bin/python scripts/pipeline/run_pipeline.py                       # process all lists (oldest first)
.venv/bin/python scripts/pipeline/run_pipeline.py --status              # show tracked lists + stages
.venv/bin/python scripts/pipeline/run_pipeline.py --list "July 25,2026" # one list only
```

Or just say **"run the lead pipeline"** in agent chat (skill: `.cursor/skills/drive-lead-pipeline/`).

### Per-list flow

For each list (a file in `Raw Leads/`), the orchestrator runs:

1. **discover** — list `Raw Leads/` (CSV/XLSX, or a native Google Sheet exported to CSV) and track new lists in `.pipeline/state.json`.
2. **reconcile with Drive** — before doing any work, inspect the list's `Cleaned Leads/<title>/`, `Verified Leads/<title>/`, and `Personalized leads/<title>/` folders and adopt the authoritative CSV (the one with the **most data rows**, any filename) as the local baseline. If the personalized rows already cover the verified rows, the list is marked **`done` and skipped** — so manual or prior work is never redone. Otherwise the existing stages are adopted and the run resumes at the correct next step.
3. **download → clean** — pull the raw file, clean it (keep rows with a real email, trim columns, cap leads per business domain), and upload to `Cleaned Leads/<title>/`.
4. **verify** — Reoon email verification, **capped at 500/day** (free tier). Whatever exceeds the cap is deferred: the list stays in stage `verifying` and continues on the next run/day. Kept rows (`safe`, `role_account`) upload to `Verified Leads/<title>/`.
5. **personalize the delta** — only newly verified leads not already enriched are personalized (**10 parallel workers × 50-lead batches**, live website + LinkedIn research), merged into the cumulative per-list enriched CSV, and uploaded to `Personalized leads/<title>/` with a markdown review.

After all lists are processed it regenerates the report and imports it to Drive (below). One list failing never blocks the others; the next run resumes it automatically.

### State, working files, Drive layout

- **State:** `.pipeline/state.json` — per-list stage, Drive-title ↔ local-slug mapping, upload markers, in-flight delta. Every run is resumable and idempotent.
- **Contacted index:** `.pipeline/contacted.json` — every address that has been personalized, mapped to the list that got there first. Drive lists overlap, so each list's delta is checked against this index and an address already sequenced on another list is skipped (the run prints how many). Rebuild or inspect it with `run_pipeline.py --backfill-contacted`; the first run after an upgrade seeds it automatically from the existing enriched CSVs.
- **Working files:** `leads/pipeline/<slug>/` (slug = sanitized title, e.g. `July 25,2026` → `july-25-2026`) holds `raw.*`, `<slug>-cleaned.csv`, `<slug>-verified.csv`, `<slug>-enriched.csv` (cumulative), and archived batch artifacts.
- **Drive folders:** `Raw Leads`, `Cleaned Leads`, `Verified Leads`, `Personalized leads` — each downstream stage writes a `<title>/` subfolder named after the raw file.
- **Daily cadence:** because verification is capped at 500/day, large lists (thousands of leads) clear over several days — run the command daily and each list advances by up to 500 verified emails until `done`.

### Progress report → "Enrichment-Reports" Google Sheet

```bash
.venv/bin/python scripts/pipeline/report.py                      # write local Report.csv
.venv/bin/python scripts/pipeline/report.py --upload             # also sync the Drive Sheet
.venv/bin/python scripts/pipeline/report.py --upload --dry-run   # show the planned cell writes
```

`report.py` is **read-only** with respect to pipeline state: it reads `.pipeline/state.json` and the per-list stage CSVs and writes `Report.csv` at the project root (one row per list plus a TOTAL), safe to run anytime — even mid-run. With `--upload` (and automatically at the end of every `run_pipeline.py` run) it updates the **native Google Sheet named `Enrichment-Reports`** in the Drive root (stable file ID / shareable link, no duplicates).

**Your own columns are safe.** The sync edits individual cells through the Google Sheets API rather than re-importing a CSV over the sheet, and it only ever writes the pipeline's own columns (`A:J`). Anything you add to the right of them — a campaign-tracking checkbox, notes, formulas — is never written to. Rows are matched by `list_title` and **never moved**; a newly discovered list is *inserted* directly above `TOTAL`, so Sheets shifts your annotations down with the row they belong to. Lists you have in the sheet but that are no longer in pipeline state are left alone, never deleted.

Two safeguards: a report with no list rows (e.g. `.pipeline/state.json` missing) refuses to sync rather than blanking the sheet, and any API failure leaves the sheet untouched — there is deliberately no CSV-import fallback. Credentials are reused from the existing `gdrive` rclone remote, so there is no second OAuth setup.

### rclone (Google Drive) setup

The pipeline talks to Drive through an rclone remote named `gdrive`:

```bash
rclone config    # create a remote named "gdrive", storage type "drive"
```

Configure it with **your own Google OAuth client ID/secret** — rclone has retired its bundled shared client ID (it is heavily rate-limited and being phased out), so a personal client ID is required for reliable access. See rclone's ["Making your own client_id"](https://rclone.org/drive/#making-your-own-client-id) guide. Credentials live in `~/.config/rclone/rclone.conf` (outside this repo). The pipeline also needs `REOON_API_KEY` in `.env`.

## Pipeline (mixed lead lists)

```bash
# 0. Clean a raw Google Maps export (keeps rows with a real email, trims
#    columns, drops closed businesses, caps 2 leads per business domain)
python3 scripts/personalization/clean_gmb_leads.py leads/raw-export.xlsx

# 1. Normalize columns and derive segments
python3 scripts/personalization/normalize_leads.py leads/my-list.csv

# 2. Create batch manifest (50 leads/batch, stratified by segment)
python3 scripts/personalization/create_batch_manifest.py

# 3. Process batches
python3 scripts/personalization/run_batches.py --from 001 --to 010 --merge

# 4. Merge into single enriched CSV
python3 scripts/personalization/merge_enriched.py
```

For agent-driven runs, the skill handles research and copy; scripts handle normalization, batching, QA, and export.

## Outputs

| File | Purpose |
|------|---------|
| `leads/*-normalized.csv` | Cleaned input with derived fields |
| `leads/enriched/*-enriched.csv` | Per-batch enriched leads (incl. `signal_strength`, `copy_variant`) |
| `leads/*-enriched.csv` | Merged full-list export |
| `copy/*-review-*.md` | Human-readable copy review |
| `copy/*-emails-*.json` | Structured sequence for import |
| `campaigns/*-research.json` | Research signals per batch |

Copy rules (company tier / Google Maps lists): greeting is always `Hi,`; the company name never appears in the copy; each email is issue → solution → soft CTA, with openers/solutions/CTAs rotated from variant pools (`copy_variant` column tracks which combination each lead got, so reply rates can be compared per variant).

## Skills

| Skill | Location | Purpose |
|-------|----------|---------|
| lead-email-personalization | `.cursor/skills/lead-email-personalization/` | Lead research + cold email copy |
| playwright-cli | `.cursor/skills/playwright-cli/` | Headless browser for website research |

## LinkedIn recent-post enrichment (Apify)

For leads with a `Linkedin_URL`, the research step scrapes the latest 3 posts via
the Apify actor [`harvestapi/linkedin-profile-posts`](https://apify.com/harvestapi/linkedin-profile-posts)
(no cookies/account required) so copy can open with a genuinely observed signal
("saw your recent post on ..."). Website research still runs for every lead; if a
lead has no LinkedIn, it falls back to website + video-presence signals.

```bash
# Add your token to .env (see .env.example)
APIFY_API_TOKEN=...
```

| Behavior | Detail |
|----------|--------|
| Posts per lead | 3 latest (`LINKEDIN_MAX_POSTS`) |
| Cost | ~$2 / 1,000 posts (billed by Apify) |
| Cache | `.apify/linkedin_cache.json` — per-handle, never re-pays |
| Batched | One actor call per run warms all LinkedIn URLs before workers start |
| Disable | `--no-linkedin` on `process_batch.py` / `run_batches.py` |
| Output columns | `linkedin_topic`, `linkedin_posts_found`, `linkedin_last_post` |

## Playwright (headless browser)

Installed locally for lead website research and browser automation. The batch
pipeline uses it automatically: when a lead's site can't be read with a plain
HTTP fetch (JS-built sites, bot-blocking CDNs), `process_batch.py` falls back
to headless Chromium via `scripts/personalization/render_page.js` to extract
positioning text and video evidence. Disable with `--no-render` on
`process_batch.py` / `run_batches.py`.

```bash
# One-time browser install (already done)
npm run playwright:install

# Open a page headless (default via .playwright/cli.config.json)
npx playwright-cli open https://example.com
npx playwright-cli snapshot
npx playwright-cli close
```

Uses bundled Chromium (headless by default). Config: `.playwright/cli.config.json`.

## Email verification (Reoon)

Verifies lead emails before outreach. **Hard cap: 500/day** (free daily credits).

```bash
# API key in .env (copy from .env.example)
python3 scripts/verify_emails_reoon.py leads/your-list.csv
python3 scripts/verify_emails_reoon.py leads/your-list.csv --dry-run  # preview only
```

| Behavior | Detail |
|----------|--------|
| Daily limit | 500 emails/day (`REOON_DAILY_LIMIT` in `.env`) |
| Overflow | Extra emails deferred — run again tomorrow, or `--instant` for another 500 via instant credits, or `--full-list` for everything |
| Cache | `.reoon/verified_cache.json` skips already-verified addresses (full API detail lives here) |
| Output | One stable file: `leads/<campaign>-verified.csv` |
| Kept statuses | `safe` and `role_account` only (plus a `Status` column) |
| Daily runs | Each day's 500 verification rewrites the same file with all kept rows so far |

Docs: [Reoon API](https://www.reoon.com/articles/api-documentation-of-reoon-email-verifier/)

## Archive

Previous mix-leads campaign (June 2026) is in `archive/mix-leads-2026-06/` — batch research/copy JSON, handoff notes, and run logs from the prior run, kept for reference. Its one-off scripts live in `scripts/archive/`.
