# Remove fit judgement; keep every valid-email lead — 2026-08-02

**Directive.** A lead with a valid email stays in the campaign. No fit score, no
"good fit" judgement, no quality-based exclusion anywhere.

**Decided with the user:**
- Closed-business drop — **removed**.
- 2-per-domain cap — **kept** (avoids emailing five people at one firm).
- `aevora_segment` — **kept**. It selects the copy angle and subject templates;
  it never removes anyone.
- `fit_score` — **removed entirely**.

---

## Correction to the record first

The README (line 40), `process_batch.py:12`, `pipeline.py:175`, the skill docs
and `tests/test_fit_score.py` all state that leads with `fit_score == "skip"`
are excluded from copy. **They are not, and never were.** The selection is:

```python
batch_rows = [all_rows[i] for i in batch["rows"]]   # process_batch.py:109
```

Identical in every commit back to `a676e35`. Confirmed against real output:
July 6 2,381 verified → 2,381 personalized; July 7 2,142 → 2,142; July 25
102 → 102. Nothing was dropped. The "740 of 3,045 rows" figure in the README is
the count of rows *assigned* a skip label, not rows removed.

So this change deletes a column nothing read plus a docs claim that was false —
and one cleaner filter that genuinely did remove people.

## Measured: what the cleaner actually removes

July 31 raw list, 29,086 rows, current defaults:

| Removal | Rows | Verdict |
|---|---|---|
| No email found | 20,525 | keep removing |
| Placeholder email | 117 | keep removing |
| Duplicate email (same address twice) | 288 | keep removing |
| Permanently closed business | 0 | **filter removed** |
| 2-per-domain cap | 49 | **kept, per user** |

The closed filter removed 0 rows here, but it is on by default and would bite a
list that carries the status.

---

## Step 1 — Drop the closed-business filter

`scripts/personalization/clean_gmb_leads.py`: delete the `drop_closed`
parameter, the `--keep-closed` flag, and the filter block at :192.

Keep `CLOSED_STATUSES` and the `closed_businesses_kept` stat line — a count is
information, not a filter, and it is now always the true count.

**Verify.** Re-run the July 31 breakdown; only no-email / placeholder /
duplicate / domain-cap removals appear. Test that a permanently-closed row with
a valid email survives cleaning.

## Step 2 — Delete fit_score

- `lead_personalization/segments.py` — delete `fit_score_for` and the 11
  `default_fit` keys in `MACRO_SEGMENTS`.
- `lead_personalization/pipeline.py` — drop the import, drop `"fit_score"` from
  `DERIVED_FIELDS`, drop it from `normalize_row`, delete the comment at :175
  that states the false exclusion claim.
- `lead_personalization/research.py:300` — drop the passthrough.
- `scripts/personalization/normalize_leads.py:35` — drop the import.
- `scripts/personalization/build_enriched.py` — drop `"fit_score"` from the
  lead JSON (:95) and `**Fit:**` from the review markdown (:158).
  **Leave `"fit_score"` in `DROP_COLUMNS` (:23)** with a comment: normalized
  CSVs already on disk still carry the column, and without it they would leak
  it into new enriched exports.
- `scripts/personalization/process_batch.py:12` — rewrite the docstring line to
  say every lead in the list gets copy.

## Step 3 — A guard that no lead is dropped

`tests/test_fit_score.py` (its whole premise is the exclusion that never
existed) is replaced by `tests/test_no_lead_is_dropped.py`:

- Every row handed to `process_batch` appears in its research and copy output,
  including a category that used to score `skip` — the regression guard the
  suite never had.
- `normalize_row` emits no `fit_score`, and it is absent from `DERIVED_FIELDS`.
- A permanently-closed business with a valid email survives `clean_gmb_leads`.
- No module exposes `fit_score_for` any more.

Fix the `fit_score` fixture key in `tests/test_copy_engine.py:32`.

**Mutation-check both guards** — restore the closed filter and re-add a
`fit_score` filter to `process_batch`, and confirm the new tests fail.

## Step 4 — Correct the docs

README:40, `.cursor/skills/lead-email-personalization/SKILL.md` :45 and :124,
and `segments.md:81` all repeat the exclusion claim. Replace with: every lead
with a valid email is personalized; segments choose the angle, nothing gates
entry.

---

---

## ✅ Done

Suite **273 → 283**. `tests/test_fit_score.py` (7 tests asserting an exclusion
that never existed) deleted; `tests/test_no_lead_is_dropped.py` (20) replaces it.

**All three guards mutation-checked, not asserted:**

| Mutation | Result |
|---|---|
| Re-add a segment filter to `process_batch` | 2 failures |
| Restore the closed-business filter | 3 failures (parametrized over the real `CLOSED_STATUSES`) |
| Put `fit_score` back in `normalize_row` + `DERIVED_FIELDS` | 7 failures |

The closed-business case was initially parametrized over invented spellings, one
of which (`CLOSED_PERMANENTLY`) is not in `CLOSED_STATUSES` and so passed under
both trees. Now parametrized over the real set, so every case bites.

**Verified against real data:** the July 31 list (29,086 rows) re-cleans to the
same 8,107, with `removed_closed_business` gone from the breakdown — no-email
20,525, placeholder 117, duplicate 288, domain cap 49. `normalize_leads.py` run
directly from `/tmp` on real rows emits no `fit_score` and keeps all 19
`low_fit` rows, Film production companies included.

One thing the plan did not anticipate: `is_placeholder` matches on *domain*
(`example.com`, `*.example`), not on the local part — so `noreply@` and `info@`
at a real domain are kept, and Reoon decides deliverability later on evidence.
That is correct under this directive, so a test now pins it rather than the
first draft's wrong assumption.

Also added: a "one rule" section at the top of the README stating the five
removal reasons and that nothing else applies. This claim has been misdocumented
in four places for months; stating it once, prominently, is what stops it drifting again.

## Not doing

- Removing the 2-per-domain cap or the duplicate-address dedupe — user kept both.
- Removing `aevora_segment` / `low_fit` — `low_fit` is a full copy pool with its
  own subject templates, not a demotion.
- Backfilling old enriched CSVs. The column is inert; new runs stop writing it.
