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
(`run_pipeline.py:595`) and the archive step exist and why only one list can
personalize at a time. Namespacing artifacts by slug deletes both workarounds.
Larger refactor — do it after Steps 1–6 are green.

**Design.** One prefix per list, threaded through every artifact name.

- New `scripts/personalization/artifacts.py` owns every name: the manifest, the
  per-batch research/copy/enriched/emails/review files, the master review, the
  normalized JSON, the merged output, and the glob `merge_enriched` uses. Today
  those strings are spelled out in seven files; after this they are spelled out
  once.
- The prefix comes from the manifest — `create_manifest` records it, everything
  downstream reads it, and it falls back to the manifest filename so an
  older manifest still works. `run_pipeline` passes the list slug, so
  `campaigns/july-6-batch-manifest.json` drives `july-6-batch-001-*`.
- `merge_enriched` globs `<prefix>-batch-*-enriched.csv` instead of
  `mix-leads-batch-*`. Cross-list contamination stops being possible, so
  `relocate_orphan_artifacts` goes.
- `merged_output_path` derives from the prefix too. It currently derives from
  the source stem and stops at the first digit, so `july-6-delta-normalized`,
  `july-7-delta-normalized` and `july-8-delta-normalized` all resolve to
  `leads/july-enriched.csv` — three lists writing one file. Only the archive
  step's move hides it.

**Keeping the archive step**, contrary to the line above. Its second job is not
a workaround: prefixes separate *lists*, not *runs of the same list*. A second
delta on july-6 renumbers from batch 001 and would overwrite the previous run's
review markdown and copy JSON. Moving them to `leads/pipeline/<slug>/artifacts/
<stamp>/` is what keeps that history. `relocate_orphan_artifacts` is the pure
workaround, and only it goes.

**Verify.** Two lists' artifacts must not collide: build manifests for two slugs
and assert every generated name differs and each merge glob sees only its own
batches. Existing `run_batches`/`merge_enriched` tests must still pass with the
default prefix.

### ✅ Done

`scripts/personalization/artifacts.py` is now the only place any artifact name is
spelled. `create_manifest` records the prefix; `process_batch`, `build_enriched`,
`apply_sanitize_all`, `run_batches`, `merge_enriched` and `run_pipeline` all read
it. `relocate_orphan_artifacts` is deleted along with the `ORPHAN_DIR`,
`MANIFEST` and `CAMPAIGNS_DIR` constants it needed; the archive step stays, for
the reason given above, with its comment rewritten to say so.

Suite **261 → 289 passed**. New `tests/test_artifact_namespacing.py` (24) covers
the disjointness of two lists' names, the merge selecting only its own batches,
the manifest round-trip and its filename fallback, the `merged_output_path`
collision the old derivation produced, and the archive list covering every file
a run writes. `tests/test_merge_enriched.py` was parametrized over
`mix-leads`/`july-6` (7 → 10): it hardcoded the default prefix, so it would have
passed just as happily if the prefix were ignored.

Both claims were checked by mutation rather than asserted. Restoring the flat
`mix-leads-batch-*` glob and the unprefixed per-batch names failed 7 of the new
tests; dropping the sidecar wiring below failed 1.

**Two things the design missed, found while wiring it up:**

- `normalize_leads` writes a sidecar JSON that still defaulted to a single
  `campaigns/mix-leads-normalized.json` for every list. The pipeline now passes
  `json_out=artifacts.normalized_json(slug)` — otherwise it stayed a shared name
  *and* the archive step would have looked for a file that was never written.
- `create_batch_manifest.py` had no way to write a manifest anywhere but the
  shared path, so the manual flow could not run two lists side by side even
  though `run_batches.py --manifest` accepts one. It now takes the destination as
  an optional second argument.

README documents the per-list names, the `--manifest` flag, and why the archive
step outlives the collisions it used to prevent.

---

## Step 8 — Collapse the two engines

`subjects.py` has genuinely diverged (templates moved into the offer pack);
`qa.py`/`sanitize.py` differ only by import line; `segments.py` is byte-identical.
Make `scripts/personalization` import from `lead_personalization` so drift is
impossible and the parity test becomes unnecessary rather than load-bearing.
Sequence Step 1 before this, or fold the two subject edits together.

**Design.** `scripts/personalization` keeps the pipeline plumbing (research,
batching, artifacts, export) and stops carrying its own copy of the copy engine.

- Delete `scripts/personalization/{qa,sanitize,segments,subjects}.py`. Three are
  duplicates modulo one import line; `subjects.py` differs only in that
  `SUBJECT_TEMPLATES` is a module constant instead of a `build_subject`
  argument, and `tests/test_subjects.py` already asserts the two are equal.
- Delete `process_batch.py`'s `OPENERS`, `SEGMENT_COPY`, `CTA_POOLS`, `CLOSERS`,
  `SUPPORT_LINES`, `_pick`, `peer_phrase`, `trim_body`, `generate_sequence`,
  `fix_sequence` (~370 lines). The two call sites take the offer pack:
  `generate_sequence(row, item, OFFER_PACK)` / `fix_sequence(seq, row, item, OFFER_PACK)`.
- `OFFER_PACK = load_offer_pack("aevora")` at module level, with `--offer-pack`
  to swap it. The hardcoded pools become one JSON file that already exists.
- Every affected module adds `ROOT` to `sys.path` beside `ROOT/"scripts"` —
  otherwise `import lead_personalization` only works because `python -m pytest`
  happens to put the repo root on the path, which a direct
  `python3 scripts/personalization/run_batches.py` does not.
- `scripts/personalization/render_page.js` is byte-identical to the library's;
  point `RENDER_SCRIPT` at that one and delete the copy.

**Tests.** `tests/test_offer_pack_parity.py` and `tests/test_copy_engine_shipping.py`
both go: with one engine there is nothing to compare and nothing separate to
smoke-test. So does `test_subjects.py::test_shipping_engine_templates_match_the_offer_pack`.
Their coverage is not lost — `tests/test_copy_engine.py` runs the same
segment × evidence matrix against the surviving engine. What replaces them is a
test that the shipping path *is* the library path: `process_batch` exposes no
copy pools of its own, and its generate/fix names resolve to
`lead_personalization.copywriter`.

**Verify.** The parity test proves byte-for-byte equality across every
segment × evidence combination, so this must not change a single character of
output. Snapshot the shipping engine's copy for the full matrix before the
change and diff it against the same matrix after. Then run the scripts directly
(not through pytest) to prove the `sys.path` change is real.

**Out of scope, and still duplicated afterwards.** `lead_personalization/research.py`,
`linkedin.py` and `pipeline.py` duplicate `process_batch.py`'s research code and
`linkedin_apify.py`. That is the larger half of the split and nothing imports it
in production either — see Step 10. Step 8 collapses the copy engine only, which
is the half the parity test covers and therefore the half that can be moved
without guessing.

### ✅ Done

`process_batch.py` went 918 → 573 lines. The four duplicate modules and the
duplicate `render_page.js` are deleted; `qa`, `sanitize`, `segments`, `subjects`
and `copywriter` now exist once each, in `lead_personalization`.

**Output is unchanged, and this was checked against the real prior code rather
than asserted.** `git archive bdbb9d0` into a scratch dir, ran the same
segment × evidence × 6-leads matrix (330 leads, 990 emails) through the old
inline engine and the new library one, diffed the two JSON dumps: **identical
byte-for-byte**, subjects, bodies and `copy_variant` included.

**The guards bite.** Re-adding an `OPENERS` pool to `process_batch.py`, wrapping
`generate_sequence` in a local shim, and touching a second
`scripts/personalization/render_page.js` produced 3 failures in
`tests/test_one_copy_engine.py`. Restored and confirmed identical to the backup.

**Two things the plan promised and this delivered beyond it:**

- `--offer-pack` exists on both `process_batch.py` and `run_batches.py`, and it
  accepts a path as well as a pack name. It is validated *at argument-parse
  time*, not at first use — a typo used to be discoverable only after the batch
  had spent its fetches and Apify credits. Bad names now exit 2 with
  `error: offer pack not found: ...` instead of a mid-run traceback.
- The `sys.path` fix is real: `run_batches.py`, `process_batch.py`,
  `build_enriched.py`, `apply_sanitize_all.py` and `normalize_leads.py` were each
  run directly with `.venv/bin/python`, outside pytest. All import.

**Tests:** 289 → 244. The drop is deletions, not lost coverage —
`test_offer_pack_parity.py` (44 parametrized parity cases over an engine that no
longer exists) and `test_copy_engine_shipping.py` (a duplicate of
`test_copy_engine.py`) are gone, replaced by 16 in `test_one_copy_engine.py`.
`test_copy_engine.py` still runs the full segment × evidence matrix, and it now
covers what ships rather than one of two things that ship.

**Also fixed while here:** the README led with "Core library" describing
`lead_personalization/` as the thing you use, above the `scripts/` code that
actually runs. It now says which is which, and says plainly that the research
half is still duplicated and that `scripts/` is authoritative there.

---

## Step 9 — Housekeeping

- Delete `scripts/archive/` (9,409 lines of one-off scripts; git has them).
- README leads with `lead_personalization/` as "Core library" above the code that
  actually runs — one line clarifying which is which.

### ✅ Done

`scripts/archive/` deleted: 13 files, 9,409 lines. Checked before deleting rather
than after — nothing in the repo imports or references them, and they were dead
twice over: every one computes `ROOT = parents[1]`, which from `scripts/archive/`
resolves to `scripts/` rather than the repo root, and all of them read a
`leads/Real-Estate-USA-500.csv` that no longer exists. None of them could have
run from where they sat. The README's Archive section now records the count and
the exact recovery command (`git show a676e35:scripts/archive/<name>.py`) instead
of a bare "git has them".

The README half was done in Step 8 — see the "How the two packages relate"
section, which also names the research duplication Step 10 still has to clear.

Suite unchanged at 244 passed: nothing referenced the archive.

---

## Step 10 — Collapse the research half

Step 8 leaves `lead_personalization/research.py`, `linkedin.py` and `pipeline.py`
duplicating `process_batch.py`'s research code and `linkedin_apify.py`. Nothing
imports them in production, and unlike the copy engine there is no parity test
proving the two produce the same signals — so this needs its own before/after
snapshot over real leads, not a mechanical swap. Bigger and riskier than Step 8;
worth doing, not worth rushing into the same commit.

### Survey — how far apart are they, actually?

Measured rather than guessed, by parsing both sides and diffing each shared
function's source (`ast.get_source_segment`):

| Pair | Shared fns | Byte-identical | Differ |
|---|---|---|---|
| `process_batch.py` ↔ `research.py` | 11 | 6 | 5 |
| `linkedin_apify.py` ↔ `linkedin.py` | 9 | 4 | 5 |
| `normalize_leads.py` ↔ `pipeline.py` | 6 | 4 | 2 |

Reading the 12 that differ: **ten of them differ only in comments, line wrapping,
a module alias, or a private-name prefix.** The library is mostly a
comment-stripped copy. Two are substantive, and in both the library is *ahead*:

1. **`research_lead` takes an injected `PageRenderer`** instead of reaching for
   the `RENDER_FALLBACK` module global and a hardcoded `render_page_signals`.
   `NodePlaywrightRenderer.render` is `render_page_signals` with the three
   constants moved into `__init__`.
2. **`linkedin.scrape_profiles` holds an exclusive `flock` and writes the cache
   atomically** (temp file + `os.replace`). `linkedin_apify` does neither.

**That second one is a live bug, not a style difference.** `run_batches.py
--workers N` runs batches in a `ThreadPoolExecutor`, and each worker calls
`scrape_profiles` → `_save_cache` → a plain `write_text` over the shared
`.apify/linkedin_cache.json`. `_warm_linkedin_cache` mitigates it by scraping
everything up front so workers find the cache warm — but that is a workaround
with a hole in it: when an Apify chunk fails, the code deliberately leaves those
handles uncached "for a later retry", so exactly the handles a warm pass could
not resolve are the ones parallel workers then race to write. The library
already solved this. Collapsing onto it fixes the race as a side effect.

And one divergence where the **library is wrong**:

3. **`pipeline.normalize_row` never sets `fit_score`.** The shipping version
   sets `fit_score_for(segment, category)`. Downstream, `process_batch` excludes
   `fit_score == "skip"` leads from copy entirely — so anything normalized by the
   library path would have `fit_score == ""`, never match `"skip"`, and get copy
   written and exported. Good evidence that this path has never been run
   end to end. Fix the library before importing it.

**So the plan's premise was too pessimistic.** This is much closer to a
mechanical swap than "collapse and hope", and the direction is the same as
Step 8: `scripts/` imports the library, keeping only what is genuinely
environment-specific (`.env` loading, `api_token()`, cache location, the
`RENDER_FALLBACK` global, CLI wiring).

### Design — three sub-steps, three commits

**10a — research.** `process_batch.py` drops `fetch_page_signals`, `needs_render`,
`render_page_signals`, `_norm_tokens`, `positioning_snippet`, `social_channel`,
`snippet_is_usable`, `_ORG_STOPWORDS`, `linkedin_profile_matches`,
`linkedin_topic`, `classify_evidence`, `build_signal`, `research_lead`, plus
`USER_AGENT`, `FETCH_TIMEOUT`, `VIDEO_EVIDENCE`, `GENERIC_TITLE_PARTS`. It
imports `research_lead` and constructs
`NodePlaywrightRenderer(RENDER_SCRIPT, ROOT, RENDER_TIMEOUT_S)` inside
`process_batch()` — not at module level, because `--no-render` mutates
`RENDER_FALLBACK` after import.

**10b — LinkedIn.** `linkedin_apify.py` becomes the environment shim it should
always have been: `load_dotenv`, `api_token`, `CACHE_FILE`, and a
`scrape_profiles(urls, max_posts)` that supplies those to the library, re-exporting
`li_handle` / `posts_for_url` / `clean_post_topic`. It keeps raising `SystemExit`
on a missing token — the library raises `RuntimeError`, and `process_batch`
catches `SystemExit` to *skip* LinkedIn rather than fail the batch. Swapping the
exception type silently converts "run without LinkedIn" into "batch dies", so the
shim checks the token itself and raises before delegating.

**10c — normalize.** Add the missing `fit_score` to `pipeline.normalize_row`
first. Then `normalize_leads.py` drops `split_emails`, `pick_primary_email`,
`domain_company`, `research_urls`, `parse_name_field`, `normalize_row`,
`outreach_tier` (a one-line alias for the library's `resolve_outreach_tier`) and
the three module regexes, keeping the file-level concerns: `campaign_stem`,
`strip_count_suffix`, `count_named_path`, `normalized_output_path`,
`normalize_leads`, `main`.

### Verify — against real data, without spending a cent

No network, no Apify calls, and no synthetic-only corpus:

- **Research:** replay real rows from
  `leads/pipeline/july-20-2026/july-20-2026-cleaned.csv` (3,045 rows) through
  `research_lead` with `urlopen` stubbed to serve a recorded page and the
  renderer stubbed, before and after; diff the full result dicts. Cross the rows
  with real LinkedIn posts from `.apify/linkedin_cache.json` so
  `linkedin_topic`, `linkedin_profile_matches` and `build_signal` are exercised
  on real post text, not invented strings.
- **LinkedIn:** snapshot `li_handle`, `clean_post_topic`, `_summarize_post`,
  `_post_handles` and `posts_for_url` over every entry in the real 226 KB cache,
  before and after.
- **Normalize:** run the whole 3,045-row CSV through `normalize_rows` before and
  after and diff the output byte-for-byte — including `fit_score`, which is the
  one column expected to change (from absent to populated) on the library side.
- **The lock:** a new test that spawns concurrent writers against one cache file
  and asserts no entry is lost. It must fail against `linkedin_apify`'s current
  unlocked `_save_cache` — otherwise it is not testing anything.

### ✅ Done

Three commits, each proven output-neutral against the real 3,045-row list before
the next one started.

**10a — research (`39c11b5`).** `process_batch.py` 573 → 233 lines. Deleted its
copies of `fetch_page_signals`, `render_page_signals`, `needs_render`,
`positioning_snippet`, `classify_evidence`, `build_signal`, `linkedin_topic`,
`linkedin_profile_matches`, `snippet_is_usable`, `social_channel`,
`VIDEO_EVIDENCE` and `GENERIC_TITLE_PARTS`; it now calls
`lead_personalization.research.research_lead` and injects a
`NodePlaywrightRenderer` rather than reaching for a module global. The renderer
is built at the call site, not at import, because `--no-render` flips
`RENDER_FALLBACK` after the module has already loaded.

*Evidence:* 3,045 real rows crossed with the real `.apify/linkedin_cache.json`,
`urlopen` and the renderer stubbed deterministically, before and after —
**identical**. Coverage confirmed rather than assumed: all five evidence buckets,
both signal strengths, 1,898 profile-mismatch rows, 612 fetch failures, and 612
rows that actually invoked the injected renderer, so the new DI path is exercised
and not merely bypassed.

**10b — LinkedIn (`89cd256`).** `linkedin_apify.py` 230 → 76 lines, rewritten as
an environment shim: it resolves the token and cache path from `.env`, then
delegates to `lead_personalization.linkedin`. It deliberately keeps raising
`SystemExit` when no token is set — `process_batch` catches that to *skip*
enrichment, and the library's `RuntimeError` would have turned "run without
LinkedIn" into "the batch dies".

*Evidence:* the helpers were byte-identical after the collapse across the whole
real cache — 175 handles, 1,225 `li_handle` calls, 639 `clean_post_topic`, 213
summaries, 175 `posts_for_url`. More importantly the collapse fixed a live bug.
The old `_save_cache` neither locked nor wrote atomically, and `run_batches
--workers N` drives it from a `ThreadPoolExecutor`. Eight threads released
simultaneously against the pre-10b tree: **1 of 8 handles survived, 7 lost** —
seven profiles' worth of Apify credits spent and discarded. Against the library's
`flock` + `os.replace`: 8 of 8. `tests/test_linkedin_cache.py` pins both the lock
and the atomicity (it monkeypatches `os.replace` to snapshot the destination
mid-swap, so a partial write can never be visible).

**10c — normalize (`this commit`).** `normalize_leads.py` 276 → 137 lines; the
row logic now comes from `lead_personalization.pipeline`. Four of the six shared
functions were already byte-identical and the other two differed only in
formatting — but `pipeline.normalize_row` **never set `fit_score`**. That is the
column `process_batch` reads to drop competitors, so anything normalized through
the library path (the web-app/orchestrator route) would have had every skip-tier
lead researched, written to, and exported. On this list that is 740 of 3,045
rows — 24% of the file, and the skips are the competition: Film production
company (228), Recording studio (53), Animation studio (48), Video editing
service (34), Movie studio (26). Fixed in the library first, so the collapse
subtracts nothing: the header list is now spelled once, as `DERIVED_FIELDS`,
because the writer's `extrasaction="ignore"` would silently drop a column derived
in one place and forgotten in the other.

*Evidence:* 3,045 rows through `normalize_row` before and after — **identical**,
distributions included (high 2,138 / skip 740 / medium 134 / low 33, zero blank).
Run directly from a foreign cwd, outside pytest, to prove the `sys.path` wiring
holds for `python3 scripts/...` and not just `python -m pytest`. Both new guards
mutation-tested: dropping `fit_score` from `DERIVED_FIELDS` fails 2 tests,
dropping it from `normalize_row` fails 10.

Suite: 261 → **273 passing**. `tests/test_one_copy_engine.py` is now
`tests/test_one_engine.py` — it guards all four halves, not just the copy one.

---

## Not doing

- Re-verifying the 3,273 addresses on `done` lists. They are near-certainly known
  rejections; Step 3 records that instead of re-spending the budget.
- Any change to Reoon's KEEP status set (`safe`, `role_account`) — that is a
  business call, not a code fix.
