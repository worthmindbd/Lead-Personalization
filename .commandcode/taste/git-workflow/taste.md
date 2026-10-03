Git & commit workflow (Lead-Personalization)

- Commits go straight to `main` and are pushed directly to `origin/main` — no feature branch, no PR, no separate review step. Treat this as the default and don't stop to ask which branch to use. Confidence: 0.7
- Pre-commit hygiene, run every time: confirm branch + upstream + ahead/behind, grep the diff for leftover debug code (`print(`, `breakpoint`, `XXX`/`TODO`/`FIXME`, scratchpad or `/tmp` paths), and re-run the test suite — then `git add -A`. Confidence: 0.7
- Verify the push actually landed instead of assuming it did: confirm the short SHA on `origin/main`, working tree clean, zero divergence. Report the SHA back to the user. Confidence: 0.7
- Commit messages use a conventional-commit prefix (`fix:`, `feat:`) followed by multi-paragraph prose, not a bullet list. Lead with the concrete defect and hard evidence (what actually shipped, counts, percentages, test-count before/after), explain why the fix took the form it did, state what the commit deliberately does NOT cover, and close with a `Co-authored-by: CommandCodeBot <noreply@commandcode.ai>` trailer. Confidence: 0.75
- `.commandcode/taste/` is already tracked in this repo and is not gitignored — include taste-file changes in the commit instead of treating them as local-only scaffolding. Confidence: 0.7
