---
name: drive-lead-pipeline
description: Runs the automated Google Drive lead pipeline (Raw Leads -> Cleaned -> Verified -> Personalized) via the orchestrator script, monitors its stage banners, and reports a final summary. Use when the user says "run the lead pipeline", "process the Drive leads", "daily lead run", or similar.
---

# Drive lead pipeline

One command drives every lead list on Google Drive through reconcile → clean → verify → personalize, uploading each stage's output back to Drive. The orchestrator is fully resumable: run it daily and each list advances by up to 500 verified emails (Reoon free-tier cap), personalizing only the newly verified delta. Before touching a list it **reconciles with Drive** — it reads the real row counts already in `Cleaned/Verified/Personalized leads/<title>/` and skips (marks `done`) any list whose personalized output already covers its verified rows, so manual or prior work is never redone. At the end of every run it refreshes a native Google Sheet named **`Enrichment-Reports`** in the Drive root (in-place, idempotent).

## How to run

```bash
.venv/bin/python scripts/pipeline/run_pipeline.py
```

Run it in the foreground and watch the output — it prints a banner per list and a `-- STAGE:` line with counts for each step (download, clean, upload cleaned, verify, upload verified, personalize, upload personalized). A full run with personalization can take many minutes (10 parallel workers × 50-lead batches, live website research per lead), so allow a generous timeout or background it and monitor the terminal output.

Useful variants:

```bash
# Show tracked lists and their stages without doing anything
.venv/bin/python scripts/pipeline/run_pipeline.py --status

# Only one list
.venv/bin/python scripts/pipeline/run_pipeline.py --list "July 25,2026"

# Local test without Drive (inject a raw CSV, skip Reoon)
.venv/bin/python scripts/pipeline/run_pipeline.py --local-only \
  --raw path/to/raw.csv --title "My List" --no-verify --no-render --no-linkedin
```

## Prerequisites (report clearly if missing)

- rclone remote named `gdrive` configured (one-time OAuth). If `rclone lsjson "gdrive:Raw Leads"` fails, tell the user rclone auth is not ready and stop; do not retry in a loop.
- `REOON_API_KEY` in `.env` — if missing, verification is deferred (the pipeline still runs the other stages and says so).

## What the agent should do

1. Run the orchestrator (exact command above). Do not pass `--no-verify` on real runs.
2. Watch the stage banners. Expected per-list flow: reconcile (skip if already `done` on Drive) → download → clean → upload cleaned → verify (may defer the remainder to tomorrow at the 500/day cap; the list stays in stage `verifying` — this is normal, not a failure) → upload verified → personalize delta → upload personalized. After the last list it regenerates `Report.csv` and updates the `Enrichment-Reports` Google Sheet.
3. If a list fails, the orchestrator prints the traceback and continues with the other lists (exit code 1 at the end). Report which list failed and why; the next run resumes it automatically.
4. When it finishes, report the final `PIPELINE SUMMARY` block: per list — stage, verified rows, still-unchecked count, cumulative enriched count. Mention explicitly how many emails remain unverified ("run again tomorrow" when the daily cap was hit) and which lists were skipped as already `done` via reconcile.

## Where things live

- State: `.pipeline/state.json` (per-list stage, Drive title ↔ local slug mapping, upload markers, in-flight delta).
- Working files: `leads/pipeline/<slug>/` (`raw.csv`, `<slug>-cleaned.csv`, `<slug>-verified.csv`, `<slug>-enriched.csv` cumulative, `artifacts/<run>/` archived batch outputs).
- Reviews: `copy/<slug>-pipeline-review-<stamp>.md` (uploaded to `Personalized leads/<title>/` along with the enriched CSV).
- Drive folders: `Raw Leads`, `Cleaned Leads`, `Verified Leads`, `Personalized leads` — each downstream stage gets a `<title>/` subfolder named after the raw file.
- Report: `scripts/pipeline/report.py` writes `Report.csv` locally (read-only view of state) and, with `--upload` or automatically at the end of a run, imports it as the native Google Sheet `Enrichment-Reports` in the Drive root (updated in place — one sheet, stable ID).

Never edit `.pipeline/state.json` by hand unless the user asks; never delete `leads/pipeline/` working directories for lists that are not `done`.
