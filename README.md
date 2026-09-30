# Lead Personalization

B2B cold email personalization workspace. Researches leads from CSV, writes hyper-personalized 3-email sequences, and exports enriched files for any ESP.

The copy engine is deterministic: emails are assembled from versioned **offer packs** (variant pools + subject templates) selected by a stable per-lead hash, driven by research signals. There is **no LLM call per lead**.

## The one rule: a mailable address is never dropped

The pipeline makes **no judgement about lead quality**. There is no fit score, no
tiering, no "good prospect" filter. If an address can receive mail, it gets a
sequence.

A lead is only ever removed for a reason that makes the email itself worthless:

| Removed | Why |
|---|---|
| No email on the row | nothing to send to |
| Placeholder domain (`example.com`, `*.example`) | not a real inbox |
| Duplicate address | the same person, already on another row |
| Beyond 2 per company domain | five people at one firm reads as a blast, not outreach (free providers exempt) |
| Rejected by Reoon | the provider says it will bounce |

Nothing else. Permanently-closed listings, unusual industries, competitors,
thin websites — all kept. `aevora_segment` picks *which* angle a lead's copy
takes, including the `general` fallback for unmapped categories; it never
decides whether a lead is worth writing to. Every industry needs finished
video, so there is no "bad" category — `general` is a full copy pool, not a
demotion. `tests/test_no_lead_is_dropped.py` counts rows out of a batch so
that stays true, and `tests/test_copy_quality.py` pins the segment name.

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

## How the two packages relate

`lead_personalization/` is the engine — normalization, research, copy. It is an installable package (`pip install -e .`) you can drive from an external orchestrator (e.g. n8n). `scripts/` is the CLI and file orchestration around it: batch manifests, artifact paths, `.env` lookups, progress output.

| Module | Purpose |
|--------|---------|
| `pipeline.py` | Row normalization + the in-memory research→copy path |
| `research.py` / `renderers.py` | Page fetch, tier-2 Chromium render, evidence classification |
| `linkedin.py` | Apify profile scrape with a file-locked, atomically-written cache |
| `copywriter.py` | Deterministic 3-email sequence generation |
| `offer_pack.py` + `offer_packs/*.json` | Versioned copy packs (pools + subject templates) |
| `qa.py` / `sanitize.py` / `subjects.py` / `segments.py` | Supporting copy logic |
| `render_page.js` | Headless-Chromium render used by the research step |
| `config.py` | Paths, feature flags, API keys (replaces hardcoded `ROOT`) |

All of it used to exist twice. `scripts/personalization/` carried its own `qa.py`, `sanitize.py`, `segments.py`, `subjects.py`, ~370 lines of inline variant pools, a second research stack, a second Apify scraper, and a second normalizer. A parity test held the copy half together; nothing at all held the rest. The duplicates are gone — `process_batch.py` went 573 → 233 lines, `linkedin_apify.py` 230 → 76, `normalize_leads.py` 276 → 137, 1,079 lines down to 446 — and `tests/test_one_engine.py` fails if a second copy reappears.

Collapsing them fixed a real bug the duplication had been hiding: the library's LinkedIn cache locks and writes atomically where the script's did not (with `--workers 8`, 7 of 8 concurrent results were being lost).

It also surfaced a claim that was never true. This section used to say `process_batch` skipped competitors by reading a `fit_score` column, worth 740 of 3,045 rows. It did not — the selection was always `[all_rows[i] for i in batch["rows"]]`, unfiltered, in every commit. The 740 was the count of rows *labelled* skip, not rows removed; the real output shows July 6 personalizing 2,381 of 2,381 verified, July 7 2,142 of 2,142. `fit_score` has been deleted, and `tests/test_no_lead_is_dropped.py` now counts rows out of a batch so a gate cannot reappear undetected.

Run the tests:

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
│   ├── pipeline/            # Drive orchestrator: run_pipeline.py + report.py + sheets_sync.py
│   ├── verify_emails_reoon.py       # Reoon email verification (500/day cap)
│   ├── split_leads_by_category.py   # Split mixed CSV into per-category files
│   └── personalization/     # Core pipeline (normalize, clean, batch, QA, merge, LinkedIn shim)
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

- **State:** `.pipeline/state.json` — per-list stage, Drive-title ↔ local-slug mapping, upload markers (row count **and content hash** of what was last pushed, so an in-place rewrite like `regen_subjects.py` re-uploads instead of being skipped as "unchanged"), in-flight delta. Every run is resumable and idempotent.
- **Contacted index:** `.pipeline/contacted.json` — every address that has been personalized, mapped to the list that got there first. Drive lists overlap, so each list's delta is checked against this index and an address already sequenced on another list is skipped (the run prints how many). Rebuild or inspect it with `run_pipeline.py --backfill-contacted`; the first run after an upgrade seeds it automatically from the existing enriched CSVs.
- **Rejected tombstones:** `.reoon/rejected.json` — addresses known to have been checked but with no cached result, so a reset cannot re-spend credits on them. Reoon results (rejections included) live in the cache; this file only covers runs whose cache was later lost, where a reseed could restore the passing addresses but not the rejects. Entries are marked `inferred_rejected` so an inference is never confused with a real answer. Recover them with `run_pipeline.py --backfill-rejected` (previews by default; add `--apply`), and spend credits on them anyway with `verify_emails_reoon.py --recheck-rejected`.
- **Working files:** `leads/pipeline/<slug>/` (slug = sanitized title, e.g. `July 25,2026` → `july-25-2026`) holds `raw.*`, `<slug>-cleaned.csv`, `<slug>-verified.csv`, `<slug>-enriched.csv` (cumulative), and archived batch artifacts.
- **Artifact names are per list:** every file a personalization run writes into the shared `campaigns/`, `copy/`, and `leads/enriched/` directories is prefixed with the list's slug — `campaigns/july-25-2026-batch-manifest.json`, `leads/enriched/july-25-2026-batch-001-enriched.csv`, and so on (all spelled in one place, `scripts/personalization/artifacts.py`). The merge globs only its own prefix. These names used to be a fixed `mix-leads-*` for every list, which meant another list's leftover batches could be folded into this list's merged output, and only one list could personalize at a time. The run still archives its artifacts into the list's workdir afterwards — not to avoid collisions between lists, but because the *next delta on the same list* renumbers from batch 001 and would otherwise overwrite this run's review and copy JSON.
- **Drive folders:** `Raw Leads`, `Cleaned Leads`, `Verified Leads`, `Personalized leads` — each downstream stage writes a `<title>/` subfolder named after the raw file.
- **Daily cadence:** because verification is capped at 500/day, large lists (thousands of leads) clear over several days — run the command daily and each list advances by up to 500 verified emails until `done`.

### Progress report → "Enrichment-Reports" Google Sheet

```bash
.venv/bin/python scripts/pipeline/report.py                      # write local Report.csv
.venv/bin/python scripts/pipeline/report.py --upload             # also sync the Drive Sheet
.venv/bin/python scripts/pipeline/report.py --upload --dry-run   # show the planned cell writes
```

`report.py` is **read-only** with respect to pipeline state: it reads `.pipeline/state.json` and the per-list stage CSVs and writes `Report.csv` at the project root (one row per list plus a TOTAL), safe to run anytime — even mid-run. With `--upload` (and automatically at the end of every `run_pipeline.py` run) it updates the **native Google Sheet named `Enrichment-Reports`** in the Drive root (stable file ID / shareable link, no duplicates).

**Reading the numbers.** Per-list columns count that list's own rows — what you see when you open its CSV. The **TOTAL row counts distinct addresses**, because the Drive lists overlap and summing the columns invents work that does not exist (17,243 pending against 15,634 real addresses — three days of budget that was never there). `unique_pending` is each list's own share of the pending total, with a shared address attributed to the older list, so that column *does* sum to TOTAL and the size of the overlap is visible rather than hidden. Pending is recomputed live from the cleaned CSVs against the Reoon cache and tombstones, so a list marked `done` reads 0 only when every one of its addresses is genuinely accounted for.

**Your own columns are safe.** The sync edits individual cells through the Google Sheets API rather than re-importing a CSV over the sheet, and it only ever writes the pipeline's own columns (`A:J`). Anything you add to the right of them — a campaign-tracking checkbox, notes, formulas — is never written to. That range is `len(report.COLUMNS)` wide: **adding an eleventh column would claim `K` and overwrite whatever is there**, so a new column has to replace one of the ten (`unique_pending` took the slot of `verify_complete`, which only ever restated `pending_verification == 0`). Rows are matched by `list_title` and **never moved**; a newly discovered list is *inserted* directly above `TOTAL`, so Sheets shifts your annotations down with the row they belong to. Lists you have in the sheet but that are no longer in pipeline state are left alone, never deleted.

Two safeguards: a report with no list rows (e.g. `.pipeline/state.json` missing) refuses to sync rather than blanking the sheet, and any API failure leaves the sheet untouched — there is deliberately no CSV-import fallback. Credentials are reused from the existing `gdrive` rclone remote, so there is no second OAuth setup.

### rclone (Google Drive) setup

The pipeline talks to Drive through an rclone remote named `gdrive`:

```bash
rclone config    # create a remote named "gdrive", storage type "drive"
```

Configure it with **your own Google OAuth client ID/secret** — rclone has retired its bundled shared client ID (it is heavily rate-limited and being phased out), so a personal client ID is required for reliable access. See rclone's ["Making your own client_id"](https://rclone.org/drive/#making-your-own-client-id) guide. Credentials live in `~/.config/rclone/rclone.conf` (outside this repo). The pipeline also needs `REOON_API_KEY` in `.env`.

## Pipeline (mixed lead lists)

```bash
# 0. Clean a raw Google Maps export (keeps every row with a real email, trims
#    columns, caps 2 leads per business domain)
python3 scripts/personalization/clean_gmb_leads.py leads/raw-export.xlsx

# 1. Normalize columns and derive segments
python3 scripts/personalization/normalize_leads.py leads/my-list.csv

# 2. Create batch manifest (50 leads/batch, stratified by segment)
#    Second argument is optional; its filename prefixes every artifact below.
python3 scripts/personalization/create_batch_manifest.py leads/my-list-normalized.csv \
    campaigns/my-list-batch-manifest.json

# 3. Process batches
python3 scripts/personalization/run_batches.py --manifest campaigns/my-list-batch-manifest.json \
    --from 001 --to 010 --merge

# 4. Merge into single enriched CSV
python3 scripts/personalization/merge_enriched.py
```

The manifest names every artifact the run writes, so two lists can be processed
side by side by giving each its own: their research JSON, copy JSON, reviews,
enriched batches, and merged CSVs stay disjoint, and each merge globs only its
own batches. Omit `--manifest` and everything falls back to the shared
historical `mix-leads-*` names.

Batch status advances `pending → copy_done → exported`. Re-running with
`--all-pending` resumes an interrupted run through both unfinished states: a
`copy_done` batch (crashed after research/copy were written but before the
export) rebuilds from the JSON already on disk instead of re-paying for
research.

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

Copy rules (dual-tier): greeting is `Hi {first_name},` for person-tier leads, `Hi,` for company-tier; the company name never appears in the copy; emails 1-2 are issue → solution → soft CTA and email 3 is the breakup (closer + support + question, no new observation), with openers/solutions/CTAs rotated from variant pools (`copy_variant` column tracks which combination each lead got, so reply rates can be compared per variant).

## Skills

| Skill | Location | Purpose |
|-------|----------|---------|
| lead-email-personalization | `.cursor/skills/lead-email-personalization/` | Lead research + cold email copy |
| playwright-cli | `.cursor/skills/playwright-cli/` | Headless browser for website research |

## LinkedIn recent-post enrichment (Apify)

For leads with a `Linkedin_URL`, the research step scrapes the latest 2 posts via
the Apify actor [`harvestapi/linkedin-profile-posts`](https://apify.com/harvestapi/linkedin-profile-posts)
(no cookies/account required) so copy can open with a genuinely observed signal
("saw your recent post on ..."). Website research still runs for every lead; if a
lead has no LinkedIn, it falls back to website + video-presence signals.

```bash
# Add your token to .env (see .env.example)
APIFY_API_TOKEN=...

# Optional: Multiple tokens with automatic fallback (comma-separated or via APIFY_FALLBACK_TOKENS)
# APIFY_API_TOKEN=token1,token2
# or
# APIFY_FALLBACK_TOKENS=fallback_token_1,fallback_token_2
```

| Behavior | Detail |
|----------|--------|
| Posts per lead | 2 latest (`LINKEDIN_MAX_POSTS`) |
| Cost | ~$2 / 1,000 posts (billed by Apify) |
| Fallback APIs | Automatic failover to next token on rate limits, quota exhaustion, or API errors |
| Cache | `.apify/linkedin_cache.json` — per-handle, never re-pays |
| Batched | One actor call per run warms all LinkedIn URLs before workers start |
| Disable | `--no-linkedin` on `process_batch.py` / `run_batches.py` |
| Output columns | `linkedin_topic`, `linkedin_posts_found`, `linkedin_last_post` |

## Playwright (headless browser)

Installed locally for lead website research and browser automation. The batch
pipeline uses it automatically: when a lead's site can't be read with a plain
HTTP fetch (JS-built sites, bot-blocking CDNs), `process_batch.py` falls back
to headless Chromium via `lead_personalization/render_page.js` to extract
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

Previous mix-leads campaign (June 2026) is in `archive/mix-leads-2026-06/` — batch research/copy JSON, handoff notes, and run logs from the prior run, kept for reference.

The one-off scripts that produced it used to sit in `scripts/archive/`. They were removed in the Step 9 cleanup: 9,409 lines across 13 files, all hardcoded to a `leads/Real-Estate-USA-500.csv` that no longer exists and all computing `ROOT` as if they still lived in `scripts/`, so none of them could run from where they sat. Recover any of them with `git show a676e35:scripts/archive/<name>.py`.
