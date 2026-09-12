# Full-project review — improvement findings (2026-09-11)

Scope: every module in `lead_personalization/`, `scripts/`, `tests/`, packaging,
config and docs. Baseline: **624 tests pass in ~1.8s**, working tree clean, no
secrets tracked in git, `.env` never committed.

Overall the codebase is in unusually good shape: the one-engine consolidation
holds (guarded by `test_one_engine.py`), state files are atomic + lock-guarded,
the reconcile logic defends against the stale-Drive-clobber scenario, and the
inline comments record *why* decisions were made. The findings below are ordered
by impact; the first five were confirmed by executing code, not just reading it.

---

## A. Confirmed bugs

> **Status: all five fixed** in this working tree, each with regression tests
> (`test_merge_enriched.py`, `test_no_lead_is_dropped.py`,
> `tests/test_copy_done_resume.py`, `tests/test_regen_subjects.py`,
> `test_pipeline_stages.py`, `test_pipeline_reconcile.py`). Suite: 624 → 643 passing.

### A1. `merge_enriched` silently drops all but the first email-less row
`scripts/personalization/merge_enriched.py:47-51` — the dedup key for a row with
no email is `""`, so the second and later email-less rows are treated as
duplicates of the first and discarded.

Reproduced: 3 email-less rows across two batch files → 1 row after merge.

The Drive pipeline path is safe (verified CSVs always carry an address), but the
manual batch path documented in AGENTS.md (normalize → manifest → `run_batches
--merge`) includes email-less rows — every row gets copy per the never-drop
rule — so leads vanish at the merge step. Note that
`run_pipeline.merge_into_cumulative` already handles this correctly; the two
mergers disagree. Fix: keep email-less rows unconditionally (or key them by
`row_index`).

### A2. `clean_gmb_leads` hard-crashes when the source lacks `Email_From_WEBSITE`
`scripts/personalization/clean_gmb_leads.py:155` — `df["Email_From_WEBSITE"]`
raises a bare `KeyError` for any raw export that carries a plain `Email` column.
Reproduced. In the Drive pipeline the list is marked failed and re-fails every
run with an opaque `KeyError: 'Email_From_WEBSITE'` as its `last_error`. Fix:
pick the first present email-ish column, or fail with an actionable message
listing the columns that were found.

### A3. `copy_done` is a dead state — interrupted batches never resume
`process_batch.py:173` writes status `copy_done` after research/copy JSON exist,
`exported` after the enriched CSV is built. `run_batches --all-pending`
(`run_batches.py:157`) selects **only `pending`**. A crash between the two
strands the batch: its export is never rebuilt, its leads are missing from the
cumulative merge, and AGENTS.md's documented resume procedure
(`--all-pending`) skips right over it. The leads do reappear in a *later* delta
(compute_delta diffs against the cumulative CSV), so nothing is lost
permanently — but they pay for website research twice and the status machine
lies. Fix: include `copy_done` in `--all-pending`, and in `process_batch`
rebuild-from-disk (skip research) when status is `copy_done` and the
research/copy JSONs still exist.

### A4. `regen_subjects` matches source rows by email — wrong row for shared addresses
`regen_subjects.py:119-124` — `next(r for r in all_rows if <email matches>)`.
Two rows sharing an email address is a scenario the main path explicitly
supports and tests (`test_two_rows_sharing_an_email_each_get_their_own_sequence`);
here both research items resolve to the *first* matching row, so the second
lead's regenerated subject uses the wrong city/category/name. Research items
already carry the authoritative `row_index` (as `build_batch` uses) — key the
lookup by that. Bonus: the linear scan per item is O(n²); one dict index fixes
both. Module is at **0% test coverage** despite rewriting shipped data in place.

### A5. Drive never receives regenerated subjects
`run_pipeline.stage_upload_personalized` (line 948) skips the upload when the
row count equals `uploads.enriched_rows`. `regen_subjects` rewrites the
cumulative CSV in place *without changing the row count* and without touching
that counter — so after a regen, every subsequent pipeline run reports
"unchanged (skip)" and the Drive copy keeps the stale subjects forever. Fix:
compare a content hash (or mtime+size), or have `regen_subjects` reset
`uploads.enriched_rows` in state.

---

## B. Robustness / consistency

### B1. Batch manifests are not written atomically, contradicting `fsutil`'s contract
`fsutil.py` docstring: "Every JSON file this project treats as durable state
(... batch manifests ...) is written atomically." In fact
`manifest_lock.update_batch_status` (line 30), `merge_enriched.py:72` and
`create_batch_manifest.py:73` all use plain `write_text`. A crash mid-write
corrupts the manifest; `fsutil.load_json` then *quarantines* it (renames it
away), which turns "resume the delta" into "recompute the delta". Fix:
`fsutil.atomic_write_json` under the existing lock (and add the `.json.tmp`
name to `batch_artifact_paths` for the archive sweep).

### B2. Two CSV row counters that disagree
`run_pipeline.csv_row_count` skips blank rows; `report.csv_data_rows` counts
them. Reproduced: same file → 2 vs 3. The Google Sheet can show a number the
pipeline's own upload guard disagrees with. This repo's standard is "spelled
once" — move one helper (e.g. into `lead_personalization` or a shared scripts
util) and use it in both.

### B3. Four variants of "first email of a row"
- `run_pipeline.row_email` — honors `EMAIL_COLUMNS`, splits on `;` and `|`
- `verify_emails_reoon.split_emails` — splits on `;` and `|`
- `build_enriched.py:65` inline — splits on `|` only
- `merge_enriched.py:47` inline — splits on `|` only

An address cell like `a@x.com;b@x.com` produces different keys in different
stages, so dedup/delta logic can disagree across files. Consolidate on one
helper.

### B4. Apify token-fallback catches `Exception` — literally
`linkedin.py:242-248`: `except (URLError, HTTPError, TimeoutError, OSError,
Exception)`. The `Exception` makes the first four decoration and means a
persistent programming error (bad payload, JSON shape change) burns one API
call per configured token, prints "falling back", and is then silently
skipped. Narrow the clause to network/HTTP/API errors; let bugs surface.

### B5. Subprocess timeouts orphan grandchild processes
`run_pipeline` runs verify/personalize as subprocesses with generous timeouts
(1h / 4h). On expiry `subprocess.run` kills the direct child only — the
ThreadPoolExecutor workers' `node render_page.js` + Chromium processes survive.
Fix: `start_new_session=True` and `os.killpg` on `TimeoutExpired`.

### B6. Research render fallback pays a full Chromium launch per lead
`renderers.NodePlaywrightRenderer.render` spawns `node` + Chromium for every
URL needing a render (≈1-3s each before the page even loads). For JS-heavy
lists this dominates research wall time. A batch mode (one browser, N pages —
`render_page.js` already accepts a single URL; extend it to a URL list or keep
a persistent process) would cut it several-fold. Also: Python's
`RENDER_TIMEOUT_S` (45) never reaches the JS page timeout (argv[3], default
20s) — pass it.

### B7. `write_verified_list` writes the verified CSV non-atomically
`verify_emails_reoon.py:396` — a crash mid-write truncates the file the
pipeline later uploads to Drive and `adopt_authoritative_csv` may re-adopt.
`merge_into_cumulative` already does tmp+replace; do the same here.

### B8. Bad `REOON_DAILY_LIMIT` crashes CLI startup with a traceback
`run_pipeline.py:1275` and `verify_emails_reoon.py:420` evaluate
`int(os.environ.get("REOON_DAILY_LIMIT", "500"))` as an argparse default —
a malformed value raises `ValueError` before any friendly message can print.
`Config.from_env` already models the tolerant pattern; reuse it.

### B9. `merge_enriched` takes fieldnames from the first batch file only
`merge_enriched.py:44-45` — columns present only in later batches are dropped
silently by `extrasaction="ignore"`. `build_enriched` computes a per-row union
for exactly this reason; do the same across files. Latent today (fixed 3-step
sequences), silent when it bites.

### B10. Reconcile re-downloads every Drive CSV of every unfinished list, every run
`adopt_authoritative_csv` downloads *each candidate file* to count its rows
even when nothing changed — for a list mid-multi-day verification that is
cleaned + verified + enriched re-fetched daily (the aug-13 workdir is 117 MB).
`drive_folder_csvs` already has `Size`/`ModTime` from `lsjson`: skip the
download when they match what was last adopted (record size+mtime in the state
entry).

---

## C. Tests & tooling

Measured with pytest-cov (installed temporarily for this review, then removed):
**58% overall**, with the pure library well covered and the file-orchestration
edges thin:

| Module | Cover | Why it matters |
|---|---:|---|
| `regen_subjects.py` | 0% | rewrites shipped copy in place (bug A4 lives here) |
| `split_leads_by_category.py` | 0% | merge fallback globs `leads/*.csv` |
| `build_enriched.py` | 13% | the export path every lead travels |
| `apply_sanitize_all.py` | 23% | bulk-rewrites copy JSON |
| `normalize_leads.py` | 33% | entry point for all manual lists |
| `verify_emails_reoon.py` | 41% | spends money |
| `run_batches.py` | 43% | failure/resume semantics (bug A3 lives here) |
| `sheets_sync.py` | 47% | writes to a live Google Sheet |
| `sanitize.py` | 52% | the copy guard of last resort |
| `renderers.py` | 55% | tier-2 research |

Recommendations:
1. **Add CI.** 624 tests in <2s — a GitHub Actions (or pre-commit) workflow
   running `pytest -q` is essentially free and is the only thing that would
   catch a regression outside this machine. There is currently no
   `.github/workflows`.
2. **Add `ruff`** (lint+format check) to dev extras; it flags B4-style dead
   exception tuples and unused imports automatically.
3. Targeted tests for A1–A5 fixes first; then `build_enriched` and
   `regen_subjects` happy+edge paths.
4. Add `pytest-cov` to `[project.optional-dependencies].dev` if you want the
   number tracked over time.

## D. Packaging / docs / hygiene (minor)

1. **Stale "web app" references** — `pyproject.toml` description says "with a
   localhost web app"; `copywriter.generate_sequence` docstring references "the
   app's 'regenerate' action". No app exists in this repo; point at the real
   one or drop the references.
2. **Undocumented env vars** — `REOON_POLL_DEADLINE_S`, `RCLONE_BIN`,
   `RCLONE_CONFIG`, `APIFY_API_TOKENS` are read by code but absent from
   `.env.example` (`APIFY_FALLBACK_TOKENS` is documented).
3. **Dependency truth split** — `requirements.txt` pins `pandas==3.0.5`,
   `pyproject.toml` says `pandas>=2.0`. Keep one source of truth (or document
   requirements.txt as the lockfile).
4. **Duplicated skill files** — `.agents/skills/playwright-cli/` and
   `.cursor/skills/playwright-cli/` are byte-identical 404-line copies; symlink
   one to the other to prevent drift (the exact failure mode this repo keeps
   fixing elsewhere).
5. **Variant pools are small** — 2 openers per evidence bucket, 2
   solutions/angles per segment, 2 closers, 3 CTAs. At hundreds of sends/day
   per segment, email 2 has ≤12 distinct bodies per segment, and every unmapped
   category shares the `low_fit` pool. `copy_variant` already exists for
   reply-rate comparison — widening the pools in the next offer-pack version is
   the highest-leverage *marketing* improvement available without touching
   code.
6. **Workdir growth** — `leads/pipeline/` is ~370 MB and archives grow every
   delta. AGENTS.md rightly forbids deleting unfinished lists' workdirs;
   consider a compression/retention policy for `stage == "done"` lists.
7. README's line-count claims drift slightly (process_batch "→ 233", actually
   249). Cosmetic.

---

## Suggested order of work

1. A1 + A3 (data-loss/resume holes in the daily path) — small, test-friendly.
2. A5 + A4 (regen correctness + Drive freshness) — one state-field fix and one
   row-key fix.
3. A2 (fail with a useful message; fallback column).
4. B1, B2, B3, B7 (consistency with the repo's own "spelled once / atomic"
   doctrine — mostly mechanical).
5. CI + ruff (C1, C2), then coverage targets around the touched code.
6. B4–B6, B8–B10 as opportunity allows; D items whenever convenient.
