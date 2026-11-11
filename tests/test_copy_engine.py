"""Copy engine smoke test: every segment x evidence combo must produce a
3-email sequence that passes QA with zero sequence issues.

``lead_personalization`` is now the only copy engine — the pipeline calls it
through ``scripts/personalization/process_batch.py``, which used to carry its
own duplicate of all of this. So this file no longer has a twin, and covering
it covers what ships.
"""

from __future__ import annotations

import pytest

from lead_personalization.copywriter import fix_sequence, generate_sequence
from lead_personalization.offer_pack import load_offer_pack
from lead_personalization.qa import qa, sequence_issues
from lead_personalization.sanitize import sanitize_email
from lead_personalization.subjects import _clean

PACK = load_offer_pack("aevora")


def fake_row(segment: str, email: str) -> dict:
    return {
        "primary_email": email,
        "company_name": "Lakeview Custom Homes LLC",
        "Name": "Lakeview Custom Homes LLC",
        "First_category": "Custom home builder",
        "City": "Austin",
        "State": "Texas",
        "aevora_segment": segment,
        "Youtube_URL": "https://youtube.com/@lakeview",
        "Instagram_URL": "",
    }


def fake_research(row: dict, evidence: str) -> dict:
    snippet = "Custom homes built around family living" if evidence == "positioning" else ""
    li_topic = "how we cut project turnaround times" if evidence == "linkedin_posts" else ""
    return {
        "email": row["primary_email"],
        "company": row["company_name"],
        "research_signal": (
            f'site positioning: "{snippet}"; video on site: yes; Austin, Texas'
            if snippet
            else "video on site: no; YouTube linked; Austin, Texas"
        ),
        "signal_strength": "strong" if evidence != "weak" else "weak",
        "evidence": evidence,
        "snippet": snippet,
        "social_channel": "YouTube" if evidence == "social_video" else "",
        "linkedin_topic": li_topic,
    }


@pytest.mark.parametrize("segment", list(PACK.segment_copy.keys()))
@pytest.mark.parametrize("evidence", list(PACK.openers.keys()))
def test_sequence_passes_qa(segment: str, evidence: str) -> None:
    email = f"lead-{segment}-{evidence}@example-biz.com"
    row = fake_row(segment, email)
    research = fake_research(row, evidence)
    seq, variant = generate_sequence(row, research, PACK)
    seq = fix_sequence(seq, row, research, PACK)

    assert len(seq) == 3, f"{segment}/{evidence}: expected 3 emails"
    assert variant, f"{segment}/{evidence}: empty copy_variant"

    for step, (subj, body) in enumerate(seq, start=1):
        result = qa(subj, body, research["company"])
        assert result["pass"], f"{segment}/{evidence} email {step}: {result['issues']} (subject={subj!r})"
        assert body.split("\n\n")[0] in {"Hi,", "Hey,", "Hello,"}, (
            f"{segment}/{evidence} email {step}: company-tier greeting must be bare"
        )

    assert not sequence_issues(seq), f"{segment}/{evidence}: sequence issues"


def test_sanitize_drops_poisoned_paragraph() -> None:
    subj, body = sanitize_email(
        "site clip pacing",
        "Hi,\n\nWe offer cheap and affordable edits for your brand.\n\n"
        "We finish supplied footage with retention pacing.\n\nWorth a look?",
    )
    assert "cheap" not in body and "affordable" not in body
    assert "We finish supplied footage with retention pacing." in body


def test_clean_no_ellipsis_artifact() -> None:
    assert "..." not in _clean("a very long subject line hook that keeps going and going", 20)


def test_qa_flags_company_and_ellipsis() -> None:
    flagged = qa(
        "test subject",
        "Hi,\n\nLakeview Custom Homes LLC does great work.",
        "Lakeview Custom Homes LLC",
    )
    assert "company_name_in_body" in flagged["issues"]
    flagged = qa("test subject", "Hi,\n\nSome truncated text...")
    assert "truncation_artifact" in flagged["issues"]
