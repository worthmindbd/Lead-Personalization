# Pipeline review fixes — 2026-08-02

Plan for the findings from the full-project review. Ordered by impact/effort.
Every step: change + test + run, then commit straight to `main`.

Baseline at time of writing: 107 tests pass; 4,961 enriched rows across 7 lists;
15,634 unique addresses still unverified; 5,012 Reoon cache entries of which only
500 are real results.

Tracked as tasks #1–#9, one per step below. Dependencies: #4 waits on #3 (done
lists read non-zero without the tombstones), #6 on #1/#2/#3/#5, #7 on #6, #8 on #1.

---

## Step 1 — Make the hook reach the subject line

**Problem.** `scripts/personalization/subjects.py:154` walks the template list in
order and returns the first non-spam candidate. Every segment's step-1 list is
`["<literal>", "{hook}", "<literal>"]`, so the literal always wins and `{hook}`
is unreachable. Steps 2 and 3 have no `{hook}` at all. Result: 13 unique subjects
across 762 emails, `client reel finish` sent to 245 prospects, and the research
signal never touches the line that decides opens.

**Change.**
- In `build_subject`, prefer a `{hook}`-bearing template whenever a usable hook
  exists; fall back to the literals only when it does not.
- Select among the remaining literals with the same deterministic per-email hash
  `_pick` already uses in `process_batch.py:304`, instead of always index 0.
- Add `{hook}` variants to the step-2 and step-3 template rows.
- Mirror into `lead_personalization/subjects.py` + `offer_packs/aevora.json`
  (see Step 8 — if the merge lands first, this is one edit, not two).

**Verify.**
- New test: same segment + step, two leads with different hooks produce different
  subjects; a lead with no hook still produces a clean, spam-free subject.
- New test: subject uniqueness across a synthetic 200-lead batch clears a floor
  (no single subject >20% of a step).
- Re-run QA over a regenerated batch; pass rate must stay 100%.

**Risk.** Subjects feed `subject_has_spam` and the ≤60-char cap; hooks are
prospect-supplied text. `_clean` + `snippet_is_usable` already gate them, but the
new test must cover a hostile hook (spam word, over-length, forbidden term).

---

## Step 2 — Global cross-list dedupe so nobody is emailed twice

**Problem.** `compute_delta` (`run_pipeline.py:446`) dedupes only against the
list's own enriched CSV. 4,961 enriched rows resolve to 4,769 unique addresses —
192 people already have two sequences queued. 1,423 of the still-unverified
addresses appear in 2+ cleaned lists, so it grows as the backlog drains.

**Change.**
- Add a contacted-address index (e.g. `.pipeline/contacted.json`), written on
  every successful merge into a cumulative enriched list, recording address ->
  first list that personalized it.
- `compute_delta` excludes any address already in the index, regardless of list.
- Backfill the index from all existing `leads/pipeline/*/*-enriched.csv`.
- Report the count skipped per run so the suppression is visible, not silent.

**Verify.**
- Test: an address present in list A's enriched output is excluded from list B's
  delta.
- Test: backfill over two overlapping fixture lists produces one entry per unique
  address, attributed to the older list.
- Dry-run the backfill and confirm it reports the 192 known duplicates.

---

## Step 3 — Tombstone cache for rejected addresses

**Problem.** Reoon rejections are dropped, so a re-check looks unavoidable.
`seed_cache_from_verified` can only restore passing addresses. Today July 6/7/25
show `pending_verification=0` in the sheet while 3,273 of their addresses are
absent from the cache. Harmless only because `reconcile_list_with_drive:770`
short-circuits on `stage == "done"` — the flag is the sole guard. Any reset or
same-title re-upload silently re-spends ~3,273 credits (6.5 days of budget).

**Change.**
- Persist every checked-and-dropped address to `.reoon/rejected.json` at the
  point of verification, with status and date.
- `pending_verification` treats a tombstoned address as checked.
- Backfill what is recoverable: addresses in a cleaned list, absent from both the
  cache and that list's verified CSV, on a list whose verification genuinely
  completed. Mark these `inferred_rejected` — distinct from a real result, so a
  future audit can tell them apart.

**Verify.**
- Test: a tombstoned address does not count toward pending and is not re-sent to
  the API.
- Test: a real Reoon result always wins over a tombstone (mirrors the existing
  `test_seed_cache_never_overwrites_a_real_reoon_result`).
- After backfill, recompute per-list pending and confirm July 6/7/25 read 0 for
  the right reason rather than because a flag says so.

---

## Step 4 — Report totals count unique work

**Problem.** `report.py:188` sums per-list columns. Summing
`pending_verification` gives 17,243 against 15,634 unique addresses; the 14,826
on the sheet is stale on top of that.

**Change.**
- TOTAL row computes unique addresses across lists, not a column sum.
- Add a `unique_pending` column so the double-count is legible rather than
  hidden.
- Refresh per-list pending for `done` lists too, so the sheet stops reporting a
  frozen 0 (depends on Step 3, else they will read non-zero and alarm).

**Verify.** Existing `test_sheets_sync.py` planning tests must still pass; add a
totals test over two overlapping fixture lists.

---

## Step 5 — Verification correctness and failure handling

Three independent fixes, one commit each.

**5a. Multi-address rows.** `write_verified_list`
(`verify_emails_reoon.py:256`) only ever considers `emails[0]`, while
`extract_emails_from_csv` splits on `|`/`;` and returns all of them — secondaries
are paid for but can never yield a row, and a row whose primary is bad is dropped
even when its secondary is safe. Latent today (0 multi-email rows) — fix before a
source introduces them. Keep the first address with a KEEP status; test both
orderings.

**5b. `SystemExit` in workers.** `_run_one_batch` (`run_batches.py:108`) catches
`Exception`; batch code raises `SystemExit` in six places
(`build_enriched.py:63,67`, `process_batch.py:787`, `merge_enriched.py:24`, …).
As a `BaseException` it escapes, propagates through `future.result()`, and kills
the run instead of landing in `failures`. Catch `BaseException` there (or convert
those raises to real exceptions) so nine healthy workers still deliver.

**5c. Manifest locking.** `merge_enriched:51` writes the manifest without
`manifest_lock` while `update_batch_status` takes it. Safe only because
`auto_merge` is off when `workers > 1`. Wrap it.

---

## Step 6 — Close the test gaps behind Steps 1–5

- `test_offer_pack_parity.py:24` swallows an import failure and skips via
  `pytestmark`, so the one test bridging the suite to the shipping engine can
  vanish while the suite stays green. Let that import fail loudly.
- No coverage for `write_verified_list`, `compute_delta`, `merge_into_cumulative`,
  or `stage_verify` — findings 1, 2 and 5a all live in that gap. Add direct tests.
- `scripts/personalization/test_copy_engine.py` sits in the package and is never
  collected (`testpaths = ["tests"]`). Move it or delete it.

---

## Step 7 — Namespace batch artifacts per list

`campaigns/mix-leads-batch-manifest.json` and the fixed `mix-leads-batch-*`
filenames are global, which is why `relocate_orphan_artifacts`
(`run_pipeline.py:460`) and the archive step exist and why only one list can
personalize at a time. Namespacing artifacts by slug deletes both workarounds.
Larger refactor — do it after Steps 1–6 are green.

---

## Step 8 — Collapse the two engines

`subjects.py` has genuinely diverged (templates moved into the offer pack);
`qa.py`/`sanitize.py` differ only by import line; `segments.py` is byte-identical.
Make `scripts/personalization` import from `lead_personalization` so drift is
impossible and the parity test becomes unnecessary rather than load-bearing.
Sequence Step 1 before this, or fold the two subject edits together.

---

## Step 9 — Housekeeping

- Delete `scripts/archive/` (9,409 lines of one-off scripts; git has them).
- README leads with `lead_personalization/` as "Core library" above the code that
  actually runs — one line clarifying which is which.

---

## Not doing

- Re-verifying the 3,273 addresses on `done` lists. They are near-certainly known
  rejections; Step 3 records that instead of re-spending the budget.
- Any change to Reoon's KEEP status set (`safe`, `role_account`) — that is a
  business call, not a code fix.
