# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

B2B cold email personalization engine. Researches leads from CSV (website + LinkedIn), writes deterministic 3-email sequences from versioned offer packs (no LLM calls per lead), and exports enriched CSVs for ESP import. A Drive-resumable orchestrator (`scripts/pipeline/run_pipeline.py`) handles the daily cadence end-to-end.

## Commands

```bash
# Run all tests
.venv/bin/python -m pytest -q

# Run a single test
.venv/bin/python -m pytest tests/test_subjects.py -q

# Drive pipeline (daily run, all lists)
.venv/bin/python scripts/pipeline/run_pipeline.py

# Drive pipeline (one list, or status check)
.venv/bin/python scripts/pipeline/run_pipeline.py --list "July 25,2026"
.venv/bin/python scripts/pipeline/run_pipeline.py --status

# Manual batch pipeline (for ad-hoc lists outside Drive)
python3 scripts/personalization/normalize_leads.py leads/my-list.csv
python3 scripts/personalization/create_batch_manifest.py leads/my-list-normalized.csv campaigns/my-list-batch-manifest.json
python3 scripts/personalization/run_batches.py --manifest campaigns/my-list-batch-manifest.json --from 001 --to 010 --merge

# Email verification (500/day cap)
python3 scripts/verify_emails_reoon.py leads/my-list.csv

# Progress report
.venv/bin/python scripts/pipeline/report.py                # local CSV
.venv/bin/python scripts/pipeline/report.py --upload       # sync to Google Sheet
```

## Architecture

### Two packages, one direction

- **`lead_personalization/`** — installable library (`pip install -e .`). Pure in-memory primitives: rows in, structured results out. No file I/O assumptions. Drives research, copy generation, normalization, LinkedIn scraping.
- **`scripts/`** — CLI and file orchestration on top of the library. Batch manifests, artifact paths, Drive sync, progress output.

The library must not depend on scripts. `tests/test_one_engine.py` fails if a second copy of any library module reappears in `scripts/`.

### The copy engine is deterministic

Emails are assembled from **offer packs** (`lead_personalization/offer_packs/*.json`) — versioned variant pools + subject templates — selected by a stable per-lead hash driven by research signals. There is no LLM in the loop. `copywriter.py` generates the 3-email sequence; `subjects.py` generates subjects; `qa.py` and `sanitize.py` enforce copy rules.

### The one rule: a mailable address is never dropped

No fit score, no tiering, no "good prospect" filter. A lead is only removed when the email itself is worthless (no address, placeholder domain, duplicate, >2 per company domain, Reoon-rejected). `aevora_segment` picks which copy angle — including `low_fit` for unmapped categories — never whether to write at all. `tests/test_no_lead_is_dropped.py` enforces this invariant.

### Research pipeline

`research.py` fetches a lead's website, classifies evidence, and falls back to headless Chromium (`render_page.js` via `renderers.py`) when HTTP can't read JS-built sites. `linkedin.py` scrapes recent posts via Apify with a file-locked, atomically-written cache at `.apify/linkedin_cache.json`.

### Drive orchestrator

`scripts/pipeline/run_pipeline.py` is resumable and idempotent. State lives in `.pipeline/state.json`. It discovers lists in Drive's `Raw Leads/`, reconciles against existing `Cleaned/Verified/Personalized` folders (adopting the CSV with the most rows), and advances each list by one stage per run. Verification is capped at 500/day (Reoon free tier), so large lists clear over multiple daily runs. The contacted index (`.pipeline/contacted.json`) deduplicates across overlapping Drive lists.

### Artifact namespacing

Every artifact a personalization run writes into shared directories (`campaigns/`, `copy/`, `leads/enriched/`) is prefixed with the list's slug — defined in `scripts/personalization/artifacts.py`. Merges glob only their own prefix so two lists can run side by side.

### Copy rules

Greeting is always `Hi,`; company name never appears in copy; each email follows issue → solution → soft CTA. Openers/solutions/CTAs rotate from variant pools. The `copy_variant` column tracks which combination each lead got for reply-rate comparison.

## Lead personalization workflow

When working on lead lists, cold email, outbound, CSV enrichment, or files under `leads/` or `copy/`:

1. **Propose a plan** (pilot size, columns, outputs) and wait for user approval before bulk work. Goal is cold → warm intent, not cold → close.
2. **Load sender context** from project root: `OFFER.md` and `BRAND_IDENTITY.md` before writing any email copy. If missing, ask once; do not invent offers or stats.
3. **Mixed lists:** run `scripts/personalization/normalize_leads.py` before research.
4. **Default workflow**: confirm plan → normalize → pilot batch (50 unless specified) → research signals → 3-email sequence → QA → export enriched CSV + `copy/pilot-review-*.md`.
5. **Tool-agnostic**: deliver CSV/JSON/markdown only; do not call Instantly or other ESP APIs unless explicitly requested.
6. Do not invent offers, stats, or signals. Map value to: save time / save money / make money.

**Before any pipeline work:** sync and check remote state first — run `scripts/pipeline/report.py --upload` (or the full pipeline, which reconciles against Drive) before starting work. Never trust local `.pipeline/state.json`, local CSVs, or a stale local `Report.csv` as the source of truth; Drive folders and the Google Sheet are authoritative.

**Drive pipeline:** when asked to "run the lead pipeline" or "process the Drive leads", run `.venv/bin/python scripts/pipeline/run_pipeline.py` end to end. Do not pass `--no-verify` on real runs. Report the final `PIPELINE SUMMARY` block. If rclone auth fails (`rclone lsjson "gdrive:Raw Leads"`), tell the user and stop — do not retry in a loop. Never edit `.pipeline/state.json` by hand unless asked; never delete `leads/pipeline/` working directories for lists that are not `done`.

## Dual-tier outreach

| Tier | When | Greeting |
|------|------|----------|
| `person` | Named contact + non-generic email | `Hi {first_name},` |
| `company` | GMB / generic inbox / business-only name | `Hi,` — **no company name anywhere in copy** (use "your site", "your team") |

## Research signal priority

Evidence priority for the opener: `linkedin_posts` → `site_video` → `social_video` → `positioning` → `weak`. `signal_strength` (strong/weak) per lead; weak-signal leads get the honest generic variant, never a fabricated observation. Signal must be verifiable.

## QA checks (enforced by `scripts/personalization/qa.py`)

- Word count: ≤100 words
- First line: specific signal; no small talk
- Subject: ≤60 chars; lowercase; signal/city-specific; no spam words (`subjects.py`)
- AI tells: no em dashes
- Company name: never in body or greeting (company tier)
- Truncation: no `...` artifacts in subject or body
- Sequence: no duplicate paragraphs or subjects across the 3 steps
- CTA: soft, low-friction (sample offer, example, or short call)

## Export columns

`research_signal`, `research_notes`, `signal_strength`, `copy_variant`, `email_1_subject`, `email_1_body` … `email_3_subject`, `email_3_body`. Use `copy_variant` to compare reply rates per variant and prune weak angles.

## Checkpoint / resume

Batch manifest (`campaigns/*-batch-manifest.json`) tracks status: `pending` → `copy_done` → `exported`. Re-run `run_batches.py --all-pending` to continue interrupted runs.

## Key files

| File | Role |
|------|------|
| `OFFER.md` / `BRAND_IDENTITY.md` | Sender context — what you sell, tone and positioning |
| `lead_personalization/pipeline.py` | Row normalization + in-memory research→copy path |
| `lead_personalization/config.py` | Paths, feature flags, API keys |
| `lead_personalization/offer_pack.py` | Loads and selects from versioned copy packs |
| `scripts/personalization/artifacts.py` | Single source of truth for per-list artifact filenames |
| `scripts/pipeline/run_pipeline.py` | Drive orchestrator (daily command) |
| `scripts/pipeline/report.py` | Progress report → CSV + Google Sheet sync |

## Environment

- Python 3.11+, deps in `requirements.txt`, install editable with `pip install -e .`
- Node.js for Playwright (headless Chromium fallback in research): `npm install && npm run playwright:install`
- API keys (optional, in `.env`): `APIFY_API_TOKEN` / `APIFY_FALLBACK_TOKENS` (LinkedIn posts, supports multi-token fallback), `REOON_API_KEY` (email verification)
- Drive access via rclone remote named `gdrive` (requires personal OAuth client ID)

