# Fix: subject lines that truncate onto a function word

## Context

The 2026-08-03 daily run personalized 359 July 8 leads cleanly, but a scan of
the enriched CSV found **126 subject lines (~84 leads, 5.4%) that are
incoherent fragments** — e.g. `"a wide selection of"`,
`"able company ltd is the"`, `"second angle on a great source of"`.

Root cause is commit `540b6ed` ("fix: let the research hook reach the subject
line", 08-02). It correctly made the `{hook}` template reachable on the opening
touch (before it, 762 emails shipped with only 13 distinct subjects). But the
hook is raw prospect text — a site's meta description or a research snippet —
and `_clean()` (`lead_personalization/subjects.py:22`) truncates it to 28 chars
at a **word** boundary. Word-boundary trimming prevents cutting mid-word; nothing
prevents cutting mid-**phrase**, so the subject often lands on a function word
(the / of / and / a / is…). `_hook_from_meta` compounds it with a hard 5-word
cap (`subjects.py:47`).

Why QA missed it: a subject only has to clear `subject_has_spam()` and the
50-char cap (`subjects.py:167`). There is no coherence check anywhere in
`qa.py`. The 2 batch-004 "failures" tripped `company_name_in_body` by accident.
The commit's own validation ("QA 1056/1056") was true but measured the wrong
thing.

Why only July 8: timing. July 6/7 were personalized 08-01 (before `540b6ed`),
so 0 of their 13,569 subjects dangle. July 8 is the first list generated after
the change. (My earlier Malta/meta theory was disproven: 68% of affected leads
have a positioning signal vs 67% of unaffected — no correlation.)

**Intended outcome:** keep the hook reaching the subject line (the `540b6ed`
win), but never ship a fragment. Bad hooks fall back to the existing literal
pool, which we verified never ends on a function word — so a fallback always
exists. Add a QA rule so a future regression shows up as failures instead of
silently shipping. Then regenerate July 8 and re-upload.

Note: per repo convention this plan is also saved to `plans/` on execution.

## Approach

A coherent-subject check, defined once in `qa.py` (shared, no drift), used in
three layers: build-time rejection (prevents), `fix_sequence` rebuild
(catch-all), and `qa()` reporting (guard). Plus a smarter hook extractor so
fewer hooks are rejected, preserving the variety `540b6ed` added.

### 1. The check — `lead_personalization/qa.py`

Add a closed-class word set and a predicate (next to `subject_has_spam`):

```python
FUNCTION_WORDS = {
    "the","a","an","of","for","and","or","nor","but","to","in","on","at","by",
    "with","from","into","onto","upon","over","under","as","that","this","is",
    "are","was","were","be","been","being","our","your","their","his","her",
    "its","we","us","they","them","i","me","my","so","if","than","then",
}

def subject_is_fragment(subject: str) -> bool:
    """True when a subject truncates onto a function word ('a wide selection of')."""
    words = (subject or "").strip().lower().split()
    return bool(words) and words[-1] in FUNCTION_WORDS
```

- Add to `qa()` (after the `subject_has_spam` block, ~`qa.py:144`): if
  `subject_is_fragment(subject)`: `issues.append("subject_fragment")`.
  This makes fragments appear as `FAIL (subject_fragment)` in the review `.md`
  files and the QA pass count.

### 2. Build-time rejection — `lead_personalization/subjects.py`

- Import `subject_is_fragment` alongside `subject_has_spam` (`subjects.py:13`).
- In the candidate loop (`subjects.py:163-169`), add the fragment check to the
  existing gate so an incoherent candidate is rejected and the next template is
  tried:

  ```python
  if subj and not subject_has_spam(subj) and not subject_is_fragment(subj):
  ```

  Because every literal template was verified to end on a content word, a clean
  literal fallback always exists — this can never empty the candidate list. Bad
  hook → hooked templates rejected → literal accepted. Good hooks still ship
  unchanged (a coherent hook produces a content-word tail).

### 3. Smarter hook extraction — `lead_personalization/subjects.py`

So rejecting fragments doesn't cost variety, make `_hook_from_meta`
(`subjects.py:36`) and `_hook_from_signal` (`subjects.py:52`) extract the
**longest prefix that ends on a content word** within the length cap, instead of
a blind 5-word / 28-char slice:

- Walk the clause's words, accumulate while ≤ 28 chars, then trim back past any
  trailing function words. If fewer than 2 content words remain, return `""`
  (literal fallback — better no hook than a fragment).
- Drop the hard 5-word cap; the content-word boundary is the real constraint.

This salvages the same leads at shorter but coherent length: a meta like
`"Discover a wide selection of high-quality household goods…"` currently yields
`"a wide selection of"` (dangling on `of`); with content-word trimming it
becomes `"a wide selection"` (ends on a content word). When fewer than 2 content
words fit, it returns `""` and the literal pool carries the subject.

### 4. Catch-all rebuild — `lead_personalization/copywriter.py`

Extend the `fix_sequence` rebuild trigger (`copywriter.py:140`) so a subject
arriving fragmented from any source is rebuilt:

```python
if subject_has_spam(subj) or subject_is_fragment(subj) or len(subj) > 60 or subj in used_subjects:
```

Secondary defense — `build_subject` already rejects fragments (step 2), so this
covers subjects reprocessed from stale data.

## Files to change

- `lead_personalization/qa.py` — add `FUNCTION_WORDS`, `subject_is_fragment()`,
  and the `qa()` issue.
- `lead_personalization/subjects.py` — import the predicate; add the gate in the
  candidate loop; rewrite `_hook_from_meta` / `_hook_from_signal` tail handling.
- `lead_personalization/copywriter.py` — one condition in `fix_sequence`.
- `tests/test_subjects.py` — regression tests using the real July 8 metas.
- `tests/test_qa.py` — assert `qa()` flags a fragment subject.

(One shared definition in `qa.py`; `subjects.py` and `copywriter.py` import it —
no duplication, matching the existing `subject_has_spam` pattern.)

## Verification

1. **Unit tests** (`.venv/bin/pytest tests/test_subjects.py tests/test_qa.py -q`):
   - New `test_subject_never_ends_on_function_word`, parametrized across all
     segments × steps, run over a hostile-hook corpus including the 8 real July 8
     metas (e.g. `"Discover a wide selection of high-quality household goods…"`,
     `"C. Fino + Sons Limited is one of the oldest…"`) → every emitted subject
     ends on a content word and clears `subject_has_spam`.
   - New `test_fragment_subject_flagged_by_qa` → `qa("a wide selection of",
     body)["pass"] is False` with issue `subject_fragment`.
   - Existing tests stay green, especially the hook-reaches and variety tests
     (`test_hooked_batch_produces_near_unique_first_subjects`,
     `test_no_single_subject_dominates_a_step`).
2. **Full suite** (`.venv/bin/pytest -q`) — no regressions.
3. **Replay over real July 8 data** — a focused harness reads the on-disk
   research JSONs (`leads/pipeline/july-8-2026/artifacts/20260803-125721/
   july-8-2026-batch-*-research.json`) + enriched rows, regenerates every
   subject via `build_subject`, and asserts **0 function-word tails** across all
   776 leads (was 126). Confirms the fix on the exact data that failed.
4. **Regenerate + re-upload July 8** (operational, 0 Reoon credits — verify is
   done, research is cached): re-personalize July 8 so the 126 bad subjects are
   replaced in `july-8-2026-enriched.csv` and re-upload to Drive, superseding the
   affected rows. Re-scan the merged CSV: 0 dangling subjects, all bodies intact.

## Non-goals

- Not reverting `540b6ed` — that restores 13 subjects across 762 sends.
- Not changing literal templates or the offer pack — they are already clean.
- Not touching the body copy, research, or verification stages.

## Result

Shipped as scoped to **English** function words (the approved plan). All four
code changes landed (`qa.py`, `subjects.py`, `copywriter.py`) plus tests, and a
one-off regeneration tool.

### What changed beyond the written plan

- **`go-to` added to `FUNCTION_WORDS`** — the initial English set missed the
  hyphenated case `"this is your go-to"` (yazminstevens@trainingroommalta.com).
  After adding it, English-function-word tails = **0** across all 2,328 July 8
  subjects (was 126).
- **Non-English subjects left as-is.** July 8 is Malta/Morocco-heavy; Romance
  function words (`de`, `un`, `est`, `à`…) still produce fragments like
  `"le meilleur centre de"`. A naive multilingual list would over-reject valid
  English (`"hair salon in pembroke, ma"` — MA = Massachusetts). Scoped out per
  the user; the other lists (US-heavy) are fully clean regardless.
- **Content-word truncation left as-is.** Subjects like
  `"fitness classes and personal"` (from "personal training") end on a content
  word, so no tail check catches them — same root cause (raw meta prefix as
  hook) but not deterministically detectable. Flagged as a separate future
  decision, not addressed here.

### Tooling

`scripts/personalization/regen_subjects.py` — re-derives subjects for an
already-personalized list in place, from cached research JSONs (no Reoon
credits, no LLM, no network — the copywriter is deterministic). Needed because
subjects are baked into `*-copy.json` and copied verbatim downstream, so
re-running `build_enriched`/`merge_enriched` alone wouldn't pick up a
`subjects.py` fix. Ran across both July 8 artifact stamps (393 + 359 leads).

### Verification

- 584 tests pass (was 283; the parametrized fragment matrix added 301).
- July 8 enriched CSV: 776 rows, 0 empty bodies, 776 unique emails,
  **0 English-function-word subject tails**.
- Variety preserved: step-1 has 609 distinct subjects for 776 leads (was 13
  before `540b6ed`; would have collapsed if the fix routed everything to
  literals — it doesn't).
- Uploaded to `gdrive:Personalized leads/July 8,2026/` (ModTime 2026-08-04
  08:10 UTC); downloaded remote copy re-checked: 0 fragments.
