Outreach copy & content rules
- Hard rule for generated outreach copy: never invent offers, stats, or signals. Any claim must be traceable to OFFER.md / BRAND_IDENTITY.md. Untraceable claims (e.g. "HIPAA compliant", compliance promises) are a defect and a real legal exposure in regulated verticals. Confidence: 0.85
- Hates copy that reads templated. Repeated subject lines, reused step-2/3 hook templates, and small global variant pools are quality bugs, not cosmetics — comment intent in code is not enough if the templates still ship. Confidence: 0.75
- Variant pools must be large and balanced; pools of 2-4 entries exhaust campaign-wide and every recipient sees the repetition. Wants cross-lead duplication checks in the report, not just per-lead checks. Confidence: 0.7
- Personalization must be real: greetings need plausible human first names. Company names, scraped garbage tokens, or `None` leaking into a greeting is the highest-severity defect because it is the first line every recipient sees. Confidence: 0.75
- Wants brand voice to actually be audible in shipped output — verifies power words (VFX, motion graphics, cinematic, retention, architect) by counting them. A report claiming the brand voice is missing is to be distrusted unless counted. Confidence: 0.65
- Values QA/validation gates that actually block or repair; advisory-only checks that print to stderr and return are considered broken. Confidence: 0.7
- Expects tests to be generalized across all segments and steps rather than hardcoded to one segment and one step. Confidence: 0.7
