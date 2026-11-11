# AGENTS.md

This file provides universal guidance for AI agents working with code in this repository.

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

No fit score, no tiering, no "good prospect" filter. A lead is only removed when the email itself is worthless (no address, placeholder domain, duplicate, >2 per company domain, Reoon-rejected). `aevora_segment` picks which copy angle — including `general` for unmapped categories — never whether to write at all. Every industry needs finished video, so there is no "bad" segment; `general` is a full copy pool. `tests/test_no_lead_is_dropped.py` enforces this invariant.

### Research pipeline

`research.py` fetches a lead's website, classifies evidence, and falls back to headless Chromium (`render_page.js` via `renderers.py`) when HTTP can't read JS-built sites. `linkedin.py` scrapes recent posts via Apify with a file-locked, atomically-written cache at `.apify/linkedin_cache.json`.

### Drive orchestrator

`scripts/pipeline/run_pipeline.py` is resumable and idempotent. State lives in `.pipeline/state.json`. It discovers lists in Drive's `Raw Leads/`, reconciles against existing `Cleaned/Verified/Personalized` folders (adopting the CSV with the most rows), and advances each list by one stage per run. Verification is capped at 500/day (Reoon free tier), so large lists clear over multiple daily runs. The contacted index (`.pipeline/contacted.json`) deduplicates across overlapping Drive lists.

### Artifact namespacing

Every artifact a personalization run writes into shared directories (`campaigns/`, `copy/`, `leads/enriched/`) is prefixed with the list's slug — defined in `scripts/personalization/artifacts.py`. Merges glob only their own prefix so two lists can run side by side.

### Copy rules (dual-tier outreach & icebreaker standards)

- **Greeting rotation**:
  - `person` tier: Rotate greeting text (`Hi {first_name},`, `Hey {first_name},`, `Hello {first_name},`, `{first_name},`).
  - `company` tier (GMB / Google Maps / generic inbox / no contact name): Rotate greeting text (`Hi,`, `Hey,`, `Hello,`).
  - **STRICT RULE FOR NO-NAME LEADS**: If a lead does not have a confirmed person's name, **NEVER** use `Hello [Company Name]` or `Hello Team` or `[Company] Team`. Output only the simple greeting and go straight into the icebreaker on line 2.
- **Client-centric first line**:
  - The first line after the greeting (opener, second angle, closer) is about the client: their business, market, or observable assets. It never starts with *I / We / My / Our*, and no line uses stock sender-centric phrases (*"caught my eye"*, *"I noticed"*, *"I came across"*, *"I am reaching out"*, *"My name is"*, *"We help"*). Enforced by `qa.opener_is_client_centric` and at pack load.
  - The solution line may say what "we" do ("We finish the footage you already shoot..."). That is plain, honest cold-email copy, not sender-centric filler.
  - The first line must be a specific, **verifiable** observation, asset gap, local market reality, or operational point. Never claim more than research checked: a linked Instagram is "set up on Instagram", not "consistent weekly work".
- **Never quote junk back**: prospect text (site title/H1/meta, LinkedIn posts) is only quoted when it passes `qa.snippet_reject_reasons`: no error pages, addresses, nav/CTA labels, questions, person names, filler starts, markup, non-English text, or mid-sentence cuts. Subject hooks are used whole or cut at the first sentence break, never mid-phrase.
- **Studios are not told they lack video**: video producers, photographers, and recording studios map to `production_studios`, which pitches white-label edit capacity. `segment_openers` in the pack override the generic openers per segment.
- **Structure**: Email 1 = observation → solution → soft CTA. Email 2 = new angle → one concrete proof point from `OFFER.md` (`proof_lines`) → soft CTA. Email 3 = breakup: closer + support line + a real question, no new observation. Pools rotate deterministically per lead; `copy_variant` (`{evidence}.o#s#a#p#cl#su#c###`) records the combination for reply-rate comparison.

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

## Dual-tier outreach & greeting rules

| Tier | When | Greeting Rotation |
|------|------|-------------------|
| `person` | Named contact + non-generic email | `{Hi|Hey|Hello} {first_name},` or `{first_name},` |
| `company` | GMB / Google Maps / generic inbox / business-only name | `{Hi,|Hey,|Hello,}` — **no company name or "team" anywhere in greeting or copy**; straight to icebreaker |

## High-performing B2B icebreakers reference

### Best-performing styles for named contacts (`person` tier)
1. **Verifiable LinkedIn post / Discussion hook**:
   - *"Your recent LinkedIn post, \"{snippet}\", is the kind of point that usually reaches more people as a short captioned clip than as text alone."*
   - `{snippet}` must be a complete sentence or clause from the post, never cut mid-sentence.
2. **On-site asset & finishing observation**:
   - *"Your current project gallery shows substantial portfolio depth, but the walkthrough clips on the landing page still rely on static title cards..."*
   - *"Your site already runs video, putting you ahead of most {peer} in {loc}. The gap is usually the finish: pacing, hooks, and captions built for each platform."*
3. **Positioning contrast hook**:
   - *"Your site leads with \"{snippet}\", which is clear positioning that most {peer} in {loc} never back up with finished video."*

### Best-performing styles for company-only / Google Maps leads (`company` tier)
1. **Google Maps review volume & reputation hook**:
   - *"Over {review_count} verified reviews in {loc} with a {rating} average is a rare track record for {category}."* (only with real review data on the row; never describe review content research did not read)
2. **On-site media gap (still photos vs. video)**:
   - *"The portfolio on your site highlights extensive project work, yet the landing pages rely almost entirely on still photography. For commercial inquiries, short site-walk reels tend to answer client questions before the initial consultation."*
3. **Social channel vs. website disconnect**:
   - *"Your {channel} is linked from your listing, but the website itself carries no video. Visitors who arrive from Google never see the work your followers do."*
4. **Category peer baseline (weak-signal honest fallback)**:
   - *"Most {peer} in {loc} sit on usable walkthrough footage and phone clips from active projects that never become finished client-facing video."*

## Research signal priority

Evidence priority for the opener: `linkedin_posts` → `site_video` → `social_video` → `positioning` → `weak`. `signal_strength` (strong/weak) per lead; weak-signal leads get the honest generic variant, never a fabricated observation. Signal must be verifiable.

## QA checks (enforced by `lead_personalization/qa.py`)

- Word count: ≤100 words
- First line: specific signal; client-focused; no small talk; never starts with I/We/My/Our; no "caught my eye" style phrases (`sender_centric_opener`)
- Greeting: one of the rotated forms only (`bad_greeting`)
- Subject junk: no error pages, phone/address/URL/price, rankings ("#1 rated"), self-reference ("we are..."), person names, or trailing punctuation (`subject_junk:*`, `subject_fragment`)
- Subject: ≤60 chars; lowercase; signal/city-specific; no spam words (`subjects.py`)
- AI tells: no em dashes, zero AI slop / buzzwords (delve, tapestry, game-changer, seamless, cutting-edge, fast-paced, supercharge, revolutionize, elevate, etc.)
- Spam triggers: zero hype, pressure, or spam words (guaranteed, 100% free, act now, risk-free, buy now, click here)
- Company name: never in body or greeting (company tier)
- Truncation: no `...` artifacts in subject or body
- Sequence: no duplicate paragraphs or subjects across the 3 steps
- Campaign: `merge_enriched.py` warns when one subject or paragraph dominates a list (`qa.repetition_warnings`); warnings only, nothing is dropped
- CTA: soft, low-friction (sample offer, example, or short call)

## Export columns

`research_signal`, `research_notes`, `signal_strength`, `copy_variant`, `email_1_subject`, `email_1_body` … `email_3_subject`, `email_3_body`. Use `copy_variant` to compare reply rates per variant and prune weak angles.

## Checkpoint / resume

Batch manifest (`campaigns/*-batch-manifest.json`) tracks status: `pending` → `copy_done` → `exported`. Re-run `run_batches.py --all-pending` to continue interrupted runs; it picks up both `pending` and `copy_done` batches, and a `copy_done` batch rebuilds its export from the research/copy JSON already on disk instead of re-paying for research.

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

