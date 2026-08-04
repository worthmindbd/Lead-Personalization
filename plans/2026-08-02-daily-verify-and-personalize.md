# 2026-08-02 — Daily run: verify 500, personalize the delta

## Goal

Spend today's 500 Reoon verifications and personalize everything they unlock.

## Starting state (`run_pipeline.py --status`)

| List | Stage | Pending verification | Enriched |
|---|---|---|---|
| July 6,2026 | done | 0 | 2381 |
| July 7,2026 | done | 0 | 2142 |
| July 8,2026 | verifying | 1320 | 24 |
| July 17,2026 | verifying | 3363 | 7 |
| July 20,2026 | verifying | 2536 | 51 |
| July 25,2026 | done | 0 | 102 |
| July 31,2026 | verifying | 7607 | 254 |

`.reoon/daily_usage.json` = `{"date": "2026-08-01", "verified_count": 500}` —
yesterday's budget was fully spent; today's counter resets on first use.

## Approach

One command: `.venv/bin/python scripts/pipeline/run_pipeline.py`.

No `--list` override — `prioritise()` already encodes backlog-first
(in-progress → never-touched → done, oldest first), so **July 8 leads** and the
500 lands on the oldest unfinished list rather than the newest upload. This is
the rule in `lead-pipeline-backlog-first`.

### Why the shared cap is safe across lists

`stage_verify()` passes `--limit 500` to `verify_emails_reoon.py` *per list*,
which looks like it could spend 500 × 4 = 2000. It cannot:
`remaining_today()` returns `min(daily_limit - usage.verified_count, api_daily)`
against the global `.reoon/daily_usage.json`, and `record_usage()` increments it
after every batch. Once July 8 consumes the 500, lists 2–4 compute a budget of 0
and verify nothing. The API's own `remaining_daily_credits` is a second ceiling.

Expected: July 8 verifies 500 (→ ~820 pending), the other three no-op on verify
but still personalize any already-verified delta they have.

## Steps

1. Run the pipeline end to end (verify → upload verified → personalize delta →
   upload personalized → report).
2. Confirm the spend was exactly one budget and landed on the right list:
   `.reoon/daily_usage.json` reads `{"date": "2026-08-02", "verified_count": 500}`.
3. Re-check `--status` and record the deltas below.

## Result

Both predictions held. `.reoon/daily_usage.json` = `{"date": "2026-08-02",
"verified_count": 500}` — one budget, spent entirely on July 8. Lists 2–4 each
printed `Daily budget remaining: 0` and skipped verification, exactly as the
shared-counter argument said they would.

**July 8:** 500 verified → 393 kept (safe/role_account), all 393 personalized
and merged. `enriched` 24 → **417**; `pending_verification` 1320 → **800**.

| List | Pending (before → after) | Enriched (before → after) |
|---|---|---|
| July 8,2026 | 1320 → 800 | 24 → **417** |
| July 17,2026 | 3363 → 3279 | 7 (unchanged) |
| July 20,2026 | 2536 → 2076 | 51 (unchanged) |
| July 31,2026 | 7607 → 6113 | 254 (unchanged) |

The other three lists' pending counts fell without spending credits — reconcile
recomputes pending against the Reoon cache and `.reoon/rejected.json`
tombstones, so previously-paid-for rejections stopped being counted as unchecked
(84 for July 17, 458 for July 20, 638 for July 31). This is the
[[lead-pipeline-reconcile-completeness]] effect: the gap was rejections, not
unverified mail.

July 31 additionally skipped 856 addresses already sequenced on an older list
via `.pipeline/contacted.json`.

### Hiccup: batch 003 failed, then resumed cleanly

The first run exited 1. Batch 003 of July 8 died on `IncompleteRead(161457
bytes read)` — a transient network read during website research. Because
`run_batches` returns non-zero, `stage_personalize` raised **before the harvest
step**, so the 343 leads from the 7 successful batches sat in
`leads/enriched/july-8-2026-batch-*.csv` unmerged and the summary still read
`enriched: 24`. The work was not lost, just unharvested.

Resumed with `--list "July 8,2026"`. The `active_delta` + manifest resume path
did the right thing: `resuming interrupted run: 1/8 batches pending` — only
batch 003 re-ran (50 leads, 150/150 QA pass), no credits re-spent and no
re-research of the 343. Then `merged 8 batch file(s): +393 leads -> 417 total`.
Exit 0, 417 rows uploaded to `Personalized leads/July 8,2026/`, report synced.

Verified afterwards: the enriched CSV has 417 rows and **0 rows with an empty
first-email body**.

### Worth noting

- Reoon's API reported 46 daily credits still remaining when our local counter
  hit 500. Our cap is marginally more conservative than their actual allowance;
  it errs the safe way, so no action taken.
- A transient network failure in any one batch currently costs the *whole*
  delta its merge until a rerun. The resume path recovers it fully, so this is
  a papercut rather than a bug — but an in-run retry of a failed batch would
  have made this a zero-touch day.

## Follow-ups (not done)

- July 8 has 800 still unchecked — roughly two more daily budgets.
- Backlog total is ~12,268 pending across four lists.
