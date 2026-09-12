---
name: lead-email-personalization
description: >-
  Researches B2B leads from CSV lists and writes hyper-personalized cold email
  sequences (not mail-merge). Discovers prospect signals, maps sender offer to
  relevance, enforces copy frameworks and quality checks, outputs enriched CSV
  and markdown review. Tool-agnostic—works with any ESP or outreach platform.
  Use when personalizing lead lists, cold outreach, outbound email, CSV
  enrichment, or multi-step email sequences.
---

# Lead Email Personalization

Personalized cold email at scale: research each lead, write copy that earns attention, export for **any** marketing tool (no vendor lock-in).

## Before you start

1. **Confirm** you understand the goal (cold → warm intent, not cold → close).
2. **Propose a plan** (pilot size, columns, outputs, sequence length). Wait for user approval before bulk work.
3. **Load sender context** (required for value-led copy):
   - This repo: read [OFFER.md](../../../OFFER.md) and [BRAND_IDENTITY.md](../../../BRAND_IDENTITY.md) at project root.
   - Other projects: `OFFER.md`, `BRAND.md`, or URL/docs the user provides. If missing, ask once; do not invent offers or stats.

## Project layout

```
leads/                    # input + normalized + enriched CSV
leads/enriched/           # per-batch enriched outputs
campaigns/                # manifest, research JSON, copy JSON
copy/                     # markdown reviews, JSON exports
scripts/personalization/  # normalize, batch, QA, merge tooling
```

Keep originals; write enriched outputs as new files.

## Mixed-list workflow (required for `all-leads-with-email.csv`)

### Step 0: Normalize

```bash
python3 scripts/personalization/normalize_leads.py leads/all-leads-with-email.csv
```

Produces `leads/all-leads-with-email-normalized.csv` with derived fields:
`primary_email`, `company_name`, `first_name`, `last_name`, `title`, `outreach_tier`, `aevora_segment`, `research_urls`.

There is no fit or quality score. Every lead with a mailable address is
personalized; `aevora_segment` chooses the copy angle, it does not gate entry.

### Step 1: Create batch manifest

```bash
python3 scripts/personalization/create_batch_manifest.py
```

Writes `campaigns/mix-leads-batch-manifest.json` (50 leads/batch, stratified by segment).

### Step 2: Process batches

```bash
# Single batch
python3 scripts/personalization/process_batch.py --batch-id 001

# Range
python3 scripts/personalization/run_batches.py --from 001 --to 160 --merge

# All pending
python3 scripts/personalization/run_batches.py --all-pending --merge
```

Per batch: website research → research JSON → segment copy → QA → enriched CSV + review markdown.

### Step 3: Merge

```bash
python3 scripts/personalization/merge_enriched.py
```

Output: `leads/all-leads-with-email-enriched.csv`

## Mixed CSV column mapping

| Source column | Normalized usage |
|---------------|------------------|
| `Name` | Parse into `first_name`, `last_name`, `title`, `company_name` |
| `Email` | Split pipes → `primary_email` (prefer personal over generic) |
| `Website` | Primary research URL |
| `First_category` | Maps to `aevora_segment` via [segments.md](segments.md) |
| `Linkedin_URL`, social | Secondary research channels |
| `City`, `State` | Location context in signals |

Legacy real-estate list (`Real-Estate-USA-500.csv`) uses `company`/`title` columns directly; mixed lists require normalization first.

## Dual-tier outreach

| Tier | When | Greeting |
|------|------|----------|
| `person` | Named contact + non-generic email | `Hi {first_name},` |
| `company` | GMB / generic inbox / business-only name | `Hi,` — **no company name anywhere in the copy** (use "your site", "your team") |

**Company-tier body structure (enforced by `process_batch.py`):** observed issue → our solution → soft CTA. Openers, solutions, and CTAs come from variant pools picked deterministically per lead (`copy_variant` column records the combination).

See [frameworks.md](frameworks.md) and [segments.md](segments.md) for segment angles.

## Standard workflow checklist

```
- [ ] Sender context loaded (offer + brand voice)
- [ ] CSV normalized (mixed lists)
- [ ] Batch manifest created
- [ ] Research complete (signal per lead)
- [ ] Copy generated + quality checks passed
- [ ] Outputs written (CSV + markdown + JSON)
- [ ] Merged enriched CSV (full-list runs)
```

### Pilot first (default)

Default **50 leads** unless the user requests full scale. Stratify across `aevora_segment` values.

### Research

Per lead the research step gathers, in priority order:
1. **LinkedIn recent posts** (if `Linkedin_URL` present) via Apify `harvestapi/linkedin-profile-posts` — latest 3 posts, cached per handle in `.apify/` so re-runs never re-pay. Needs `APIFY_API_TOKEN` (supports multiple fallback tokens via comma-separated list or `APIFY_FALLBACK_TOKENS`) in `.env`. Disable with `--no-linkedin`.
2. **Website** title/meta/H1 + **video evidence** (embedded video, YouTube/Instagram links). When the plain fetch fails or returns nothing usable (JS-built sites: Wix, Squarespace), `process_batch.py` retries with headless Chromium (`render_page.js`; disable with `--no-render`).

Evidence priority for the opener: `linkedin_posts` → `site_video` → `social_video` → `positioning` → `weak`. `signal_strength` (strong/weak) is recorded per lead; weak-signal leads get the honest generic variant, never a fabricated observation. Signal must be verifiable. No lead is excluded from copy — a weak signal changes which variant it gets, never whether it gets one. Note thin research in `research_notes`.

### Copy

Follow [frameworks.md](frameworks.md). Segment playbook: [segments.md](segments.md).

**Sequence (default):** 3 emails — day 0, +3, +7.

### QA (automated via `scripts/personalization/qa.py`)

| Check | Rule |
|-------|------|
| Word count | ≤100 words |
| First line | Specific signal; no small talk |
| Banned phrases | See frameworks.md |
| CTA | Soft, low-friction (sample offer, example, or short call) |
| Subject | ≤60 chars; lowercase; signal/city-specific; no spam words (see `scripts/personalization/subjects.py`) |
| AI tells | No em dashes |
| Company name | Never in body or greeting (company tier) |
| Truncation | No `...` artifacts in subject or body |
| Sequence | No duplicate paragraphs or subjects across the 3 steps (`sequence_issues`) |

### Export columns

- `research_signal`, `research_notes`, `signal_strength`, `copy_variant`
- `email_1_subject`, `email_1_body` … `email_3_subject`, `email_3_body`

`copy_variant` records which opener/solution/CTA combination each lead received — use it to compare reply rates per variant and prune weak angles.

**Do not** call ESP APIs unless explicitly requested.

## Checkpoint / resume

Update `status` in `campaigns/mix-leads-batch-manifest.json`:
`pending` → `copy_done` → `exported`

Re-run `run_batches.py --all-pending` to continue interrupted runs. It picks up
both unfinished states: a `copy_done` batch (crashed after research/copy were
written, before the export) rebuilds its export from the JSON on disk instead
of re-paying for research.

## Additional resources

- Segment playbooks: [segments.md](segments.md)
- Copy rules: [frameworks.md](frameworks.md)
- Examples: [examples.md](examples.md) — includes **canonical GMB company-tier 3-email sequence** for Google Maps lists

## Google Maps lists (no contact name)

1. Clean CSV via `scripts/personalization/clean_gmb_leads.py`: keeps only rows with a real email, dedupes, trims columns, drops closed businesses, caps 2 leads per business domain
2. Verify via Reoon (500/day free) → one stable `leads/<campaign>-verified.csv` that keeps only `safe` and `role_account`; each daily run grows the same file
3. Research: website (positioning + video evidence) → social links → fill `research_signal` + `signal_strength`
4. Copy: company tier (`Hi,`, no company name in copy), issue → solution → CTA, variant pools in `process_batch.py`
5. QA: `python3 scripts/personalization/qa.py` checks on every email before export
6. Pilot **50 leads** across segments before scaling the full verified list
