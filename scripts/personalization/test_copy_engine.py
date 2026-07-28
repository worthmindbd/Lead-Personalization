#!/usr/bin/env python3
"""Offline smoke test for the copy engine: every segment x evidence combo
must produce a 3-email sequence that passes QA with zero sequence issues.

Run: python3 scripts/personalization/test_copy_engine.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from personalization.process_batch import (  # noqa: E402
    OPENERS,
    SEGMENT_COPY,
    fix_sequence,
    generate_sequence,
)
from personalization.qa import qa, sequence_issues  # noqa: E402
from personalization.sanitize import sanitize_email  # noqa: E402
from personalization.subjects import _clean  # noqa: E402


def fake_row(segment: str, email: str) -> dict:
    return {
        "primary_email": email,
        "company_name": "Lakeview Custom Homes LLC",
        "Name": "Lakeview Custom Homes LLC",
        "First_category": "Custom home builder",
        "City": "Austin",
        "State": "Texas",
        "aevora_segment": segment,
        "fit_score": "medium",
        "Youtube_URL": "https://youtube.com/@lakeview",
        "Instagram_URL": "",
    }


def fake_research(row: dict, evidence: str) -> dict:
    snippet = "Custom homes built around family living" if evidence == "positioning" else ""
    li_topic = "how we cut project turnaround times" if evidence == "linkedin_posts" else ""
    return {
        "email": row["primary_email"],
        "company": row["company_name"],
        "research_signal": f'site positioning: "{snippet}"; video on site: yes; Austin, Texas'
        if snippet
        else "video on site: no; YouTube linked; Austin, Texas",
        "signal_strength": "strong" if evidence != "weak" else "weak",
        "evidence": evidence,
        "snippet": snippet,
        "social_channel": "YouTube" if evidence == "social_video" else "",
        "linkedin_topic": li_topic,
    }


def main() -> None:
    failures: list[str] = []
    checked = 0

    for segment in SEGMENT_COPY:
        for evidence in OPENERS:
            email = f"lead-{segment}-{evidence}@example-biz.com"
            row = fake_row(segment, email)
            research = fake_research(row, evidence)
            seq, variant = generate_sequence(row, research)
            seq = fix_sequence(seq, row, research)

            if len(seq) != 3:
                failures.append(f"{segment}/{evidence}: expected 3 emails, got {len(seq)}")
                continue

            for step, (subj, body) in enumerate(seq, start=1):
                checked += 1
                result = qa(subj, body, research["company"])
                if not result["pass"]:
                    failures.append(
                        f"{segment}/{evidence} email {step}: {result['issues']} "
                        f"(subject={subj!r})"
                    )
                if not body.startswith("Hi,\n\n"):
                    failures.append(
                        f"{segment}/{evidence} email {step}: greeting is not bare 'Hi,'"
                    )

            seq_issues = sequence_issues(seq)
            if seq_issues:
                failures.append(f"{segment}/{evidence}: sequence issues {seq_issues}")
            if not variant:
                failures.append(f"{segment}/{evidence}: empty copy_variant")

    # Guard behavior: poisoned paragraph is dropped, not word-stripped.
    subj, body = sanitize_email(
        "site clip pacing",
        "Hi,\n\nWe offer cheap and affordable edits for your brand.\n\n"
        "We finish supplied footage with retention pacing.\n\nWorth a look?",
    )
    if "cheap" in body or "affordable" in body:
        failures.append("sanitize_email left forbidden words in body")
    if "We finish supplied footage with retention pacing." not in body:
        failures.append("sanitize_email dropped a clean paragraph")

    # Subject truncation must not produce ellipsis artifacts.
    if "..." in _clean("a very long subject line hook that keeps going and going", 20):
        failures.append("_clean produced '...' artifact")

    # QA must flag company name in body and truncation artifacts.
    flagged = qa("test subject", "Hi,\n\nLakeview Custom Homes LLC does great work.", "Lakeview Custom Homes LLC")
    if "company_name_in_body" not in flagged["issues"]:
        failures.append("qa missed company name in body")
    flagged = qa("test subject", "Hi,\n\nSome truncated text...")
    if "truncation_artifact" not in flagged["issues"]:
        failures.append("qa missed '...' artifact")

    print(f"Checked {checked} emails across {len(SEGMENT_COPY)} segments x {len(OPENERS)} evidence types")
    if failures:
        print(f"\nFAIL ({len(failures)} issues):")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("PASS: all sequences clean (QA, greeting, variants, sequence checks)")


if __name__ == "__main__":
    main()
