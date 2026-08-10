# 2026-08-10 — Daily run on a fresh machine: recover state, verify 500, personalize the delta

## Goal

Spend today's 500 Reoon verifications and personalize everything they unlock —
but first rebuild all pipeline state, because **this checkout had never run the
pipeline**: no `.pipeline/`, no `.reoon/`, no `leads/`, and rclone was not even
installed. Everything had to be recovered from Drive before a single credit
could be spent safely.

## Starting state

- `.pipeline/state.json` — absent (gitignored, never created here)
- `.reoon/` — absent: no verification cache, no daily-usage counter, no tombstones
- `.pipeline/contacted.json` — absent
- `rclone` — not installed; no `gdrive` remote configured

Drive itself was intact: all 7 raw lists in `Raw Leads/`, all stage outputs in
`Cleaned/Verified/Personalized`, and the `Enrichment-Reports` sheet readable.

## Recovery steps (before any spend)

1. **Installed rclone v1.75.0** to `~/.local/bin/rclone` (the first path
   `sheets_sync.resolve_rclone()` checks) and created the `gdrive` remote via
   `rclone authorize "drive"` with the `.env` OAuth client, writing the
   captured token into `~/.config/rclone/rclone.conf`.
2. **Reconciled all 7 lists against Drive** (the pipeline's own
   `discover()` + `reconcile_list_with_drive()`), which downloaded the
   authoritative Cleaned/Verified/Personalized CSV per list and reseeded
   `.reoon/verified_cache.json` from the verified rows (6,411 entries) so
   already-passed emails cannot re-burn credits.
3. **Recovered 3,686 lost rejected-tombstones by inference.** The fresh
   machine had no `.reoon/rejected.json`, which made the four *completed*
   lists look unfinished (their cleaned−verified gap counted as unchecked) and
   would have starved the real backlog of budget for a week. Evidence of
   completion: the 2026-08-02 run log (July 6/7/25 explicitly `done`) and
   Drive mtimes (July 8's verified/enriched uploaded 2026-08-04, with younger
   lists having received the shared budget since — so July 8 had drained).
   For those four lists, every cleaned address in neither cache nor verified
   CSV must have been checked and rejected, so tombstones were written in
   `backfill_rejected`'s exact format (`status: inferred_rejected`,
   `source: inferred_from_completed_list`). The shipped backfill itself could
   not run: it gates on state's `verify_complete` flag, which was lost with
   the state. After recovery all four lists read `pending_verification: 0`.
4. **The contacted index seeded itself** at run start (6,411 addresses, 192
   found on more than one list).

## Result

`.reoon/daily_usage.json` = `{"date": "2026-08-10", "verified_count": 500}` —
one budget, spent entirely on July 17 (oldest unfinished).

**July 17:** 500 checked → **16 kept** (4 safe, 12 role_account), all 16
personalized and merged (48/48 QA pass in the batch). `enriched` 690 → **706**;
`pending_verification` 2,594 → **2,094**.

The keep-rate (3.2%) is far below August's ~79% and is a property of what is
left in July 17, not a fault: the 500 broke down as 350 catch-all, 99 unknown,
21 invalid, 14 disabled, 4 safe, 12 role-account. `KEEP_STATUSES` is
deliberately `{safe, role_account}` — catch-alls are dropped rather than
risked at the ESP, and every answer is now cached so no credit is re-spent.

July 20 and July 31 skipped verification (budget 0). July 20's personalization
delta was fully suppressed by the contacted index (its verified addresses were
already sequenced on older lists — enriched stayed 51). July 31's verified CSV
grew 1,120 → 1,123 purely from shared-cache overlap; enriched stayed 254 for
the same reason.

| List | Stage | Pending | Enriched |
|---|---|---|---|
| July 6,2026 | done | 0 | 2381 |
| July 7,2026 | done | 0 | 2142 |
| July 8,2026 | done | 0 | 983 |
| July 17,2026 | verifying | 2594 → 2094 | 690 → **706** |
| July 20,2026 | verifying | 2100 → 2095 | 51 |
| July 25,2026 | done | 0 | 102 |
| July 31,2026 | verifying | 6256 → 6252 | 254 |

Exit 0. Enriched CSV verified: 706 rows, 0 empty first-email bodies/subjects.
`Enrichment-Reports` synced in place (8 rows, A:J only; the hand-maintained
"Imported to Campaign?" column untouched). July 8's raw file was re-downloaded
and re-registered so the report's `raw_leads` TOTAL (66,157) matches the
pre-loss sheet.

## Known gap

The exact reject lists for **July 17/20/31** were on the old machine only and
are not on Drive. Their pending counts here are therefore upper bounds (sheet
before today: 2077/2067/6099 vs local 2594/2095/6252 — the difference is
lost rejects). Those addresses will be re-checked over coming days at the
cost of some wasted credits; every re-check rebuilds the tombstone, so the
counts converge and no wrong answer is possible. If the old machine's
`.reoon/rejected.json` is still reachable, copying it here would skip that
waste entirely.

## Follow-ups

- ~10,049 unique addresses still pending across July 17/20/31 — ~20 daily budgets.
- If the old machine is reachable: copy its `.reoon/rejected.json` and merge
  (any entry not already cached becomes a tombstone).
- July 17's remainder is mostly catch-all domains; expect keep-rates well
  below the early-list norm until it drains.
