Long-running pipeline runs (Lead-Personalization)

- Start long pipeline stages in the background, then poll with `shell_output` using `wait: "output"` and `from_offset` / `max_chars` to page forward from the last read offset — never re-dump or re-read output already seen, and switch to `wait: "exit"` for the final completion. Confidence: 0.8
- While waiting, cross-check real progress against artifacts on disk and the batch manifest JSON rather than trusting log text alone (e.g. count files in the newest `artifacts/<timestamp>/` dir, and `collections.Counter` over batch statuses). If logs and disk disagree, believe disk. Confidence: 0.75
- A stage transition is worth stating explicitly as it happens ("verification done, 500/500 credits used; moving to personalization"), so credit exhaustion and stage boundaries are surfaced, not buried. Confidence: 0.7
- End-of-run summary must be quantified per stage: leads added, leads kept vs dropped, QA pass rate, cumulative totals, what was uploaded (verified/enriched CSVs + review file), and sheet sync status. Confidence: 0.85
- Always close with the remaining backlog in concrete terms (leads left, the rate limit that gates it, implied days-to-clear) and the exact command to resume next time — e.g. the next day's `run_pipeline.py` invocation. Don't end on "done" alone. Confidence: 0.85
