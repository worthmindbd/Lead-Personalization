# Pipeline review fixes — 2026-08-02

Plan for the findings from the full-project review. Ordered by impact/effort.
Every step: change + test + run, then commit straight to `main`.

Baseline at time of writing: 107 tests pass; 4,961 enriched rows across 7 lists;
15,634 unique addresses still unverified; 5,012 Reoon cache entries of which only
500 are real results.

Tracked as tasks #1–#9, one per step below. Dependencies: #4 waits on #3 (done
lists read non-zero without the tombstones), #6 on #1/#2/#3/#5, #7 on #6, #8 on #1.

---

## Step 1 — Make the hook reach the subject line ✅ done (540b6ed)

Landed as described, plus a word-boundary trim on over-long subjects. Replayed
over the 352 leads whose research JSON survives: 13 unique subjects → 367, top
subject 340 → 105, QA 1056/1056 with zero sequence issues. 22 new tests in
`tests/test_subjects.py`, including one asserting the two engines' templates
have not drifted.


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

## Step 2 — Global cross-list dedupe so nobody is emailed twice ✅ done

Landed as `.pipeline/contacted.json` + `--backfill-contacted`. Backfill over
real state produced exactly the predicted numbers: 4,769 unique addresses, 192
already personalized on 2+ lists, overlaps attributed to the older list
(july-6 2,381 / july-7 2,126 / july-31 159 / july-25 79 / july-8 23 / july-17 1).


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

## Step 3 — Tombstone cache for rejected addresses ✅ done

Landed as `.reoon/rejected.json` + `--backfill-rejected` (previews unless
`--apply`) + `verify_emails_reoon.py --recheck-rejected`. Backfill tombstoned
3,255 addresses across the three completed lists (july-6 1,482, july-7 1,727,
july-25 46 — 18 fewer than the review's 3,273 because july-7 has 18 addresses in
its verified CSV but not the cache, and the backfill correctly refuses to
tombstone anything that passed).

Every cleaned address on those lists is now accounted for by a cache entry or a
tombstone, zero unexplained: july-6 2,392+1,482 of 3,874; july-7 2,228+1,745 of
3,973; july-25 102+46 of 148. `pending_verification` reads 0 for all three
computed directly, with no `stage == "done"` short-circuit involved. Pending on
the unfinished lists also dropped (july-17 3,363→3,279, july-20 2,536→2,078,
july-31 7,607→6,113, july-8 1,320→1,300) — those are cross-list duplicates that
were already checked and rejected under another list, so the budget was never
going to buy anything there. 8 new tests in `tests/test_rejected_tombstones.py`;
`tests/conftest.py` now pins the runtime-state paths at a tmp dir so the suite
can never read this machine's real cache.


**Problem.** *Re-scoped after measuring the cache.* The live path is fine:
`verify_emails_reoon.py:427` does `cache.update(verified)` for every result, so
rejections **are** persisted (the cache holds 190 `catch_all`, 41 `unknown`,
7 `invalid`, 6 `disabled`, 2 `disposable`). What is lost is historical: 4,512
of the 5,012 cache entries are `reseeded_from_verified_csv` placeholders, and
`seed_cache_from_verified` can only restore addresses that *passed*. The
rejects from those runs are gone.

That leaves 3,273 addresses on the three `verify_complete` lists absent from
the cache (july-6: 1,482, july-7: 1,745, july-25: 46) while the sheet shows
`pending_verification=0`. Harmless only because `reconcile_list_with_drive:770`
short-circuits on `stage == "done"` — the flag is the sole guard. Any reset or
same-title re-upload silently re-spends ~3,273 credits (6.5 days of budget).

So there is nothing to fix at the point of verification; the work is to record
what the lost cache knew.

**Change.**
- `.reoon/rejected.json` holds addresses known checked *without* a result, kept
  separate from the cache so an inference is never mistaken for a Reoon answer.
- `pending_verification` and the verifier's own pending list both treat a
  tombstoned address as checked (`--recheck-rejected` overrides).
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

## Step 4 — Report totals count unique work ✅ done

TOTAL now counts distinct addresses; `unique_pending` carries each list's own
share (older list wins a tie) so the column still sums to it. Pending is
recomputed live from the cleaned CSVs against the cache + tombstones instead of
being read from state, so a `done` list reads 0 only when its addresses are
accounted for. Live sheet after sync: 12,379 pending (was a 17,243 sum against a
stale 14,826 on the sheet), 20,646 unique cleaned against a 23,917 column sum,
4,769 unique personalized — matching the contacted index exactly.

One thing the plan did not know: **column K of the sheet is a hand-maintained
`Imported to Campaign?` column with real values**, and `sheets_sync` writes
`A..len(COLUMNS)`. Adding an eleventh column would have overwritten it on the
next run. So `unique_pending` took the slot of `verify_complete` — a boolean
that only ever restated `pending_verification == 0` and that nothing read. The
column count is now asserted at 10 by a test that says why. Verified by dry-run
before applying, and re-read afterwards: K still holds its TRUE/FALSE values.
12 new tests in `tests/test_report_totals.py`; `test_sheets_sync.py` now imports
the real `COLUMNS` instead of keeping a copy that could drift.


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

## Step 5 — Verification correctness and failure handling ✅ done

Three commits: `dc5d0c5` (5a), `116ad8a` (5b), `ac7177e` (5c).

**5a** now checks every address in a row, keeps the row if any passed, and
writes that address back to the email column — a row kept on its secondary
would otherwise send mail to the address we know is bad. Statuses count per
address, which is what the "checked / total" line always claimed to measure.
Confirmed a no-op on current data by running both algorithms over the same
cache: byte-identical output for all three completed lists. 11 tests.

**5b** catches SystemExit in the worker; KeyboardInterrupt still propagates so
Ctrl-C is not filed as a batch failure. 8 tests, 3 of which fail on the old
code. **5c** wraps the merge's manifest write in `manifest_lock`; its test
holds the lock and asserts the merge is still blocked, and fails without it.
6 tests.

Noted while measuring, not fixed: `seed_cache_from_verified` reseeds every
recovered address as `safe`, so regenerating a verified list downgrades a
`role_account` label. Both are KEEP statuses, so no row changes hands — the
Status column is just less specific than it was. Also visible: july-7's stored
verified CSV is one row behind its own cache.

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

## Step 6 — Close the test gaps behind Steps 1–5 ✅ done

Suite 182 → 261.

The parity test's import is bare now; confirmed by hiding `process_batch.py`
and watching collection fail instead of skip. The 127-line
`scripts/personalization/test_copy_engine.py` had never once run — it lived in
the package with a `__main__` block, and `testpaths = ["tests"]` meant pytest
never saw it. Ported to `tests/test_copy_engine_shipping.py` (58 tests, one per
segment x evidence combo plus the sanitize/QA guards) and deleted. That is the
first coverage this suite has had of the *shipping* engine's QA and sanitize
paths — `tests/test_copy_engine.py` only ever tested `lead_personalization`.
Both pass, so the two engines are clean on the same inputs.

`tests/test_pipeline_stages.py` adds 21: `merge_into_cumulative` (6, including
a widening header and a mid-write failure leaving the previous file intact),
`compute_delta`'s remaining gaps (3 — fieldnames, address-less rows, empty
list), and `stage_verify` (12: `--no-verify`, missing and placeholder API key,
a full cache hit, tombstones counting as checked, a rebuild when the verified
CSV is gone, a capped run, a non-zero exit, and the row-count line). Checked
they bite by mutating two behaviours in `run_pipeline.py` — dropping the
tombstone term from `pending_verification` and deriving `verify_complete` from
the row count — which fails 4 of them.

Left as-is: `compute_delta` was already covered for suppression by
`test_contacted_index.py`, so only its edges were missing.


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
