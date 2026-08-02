"""The same copy-engine smoke test, against the engine that actually ships.

``tests/test_copy_engine.py`` covers ``lead_personalization`` — the refactor
nothing imports yet. This one covers ``scripts/personalization``, the code the
pipeline runs. It was already written, as ``scripts/personalization/test_copy_engine.py``,
but it sat inside the package with a ``__main__`` block and ``testpaths =
["tests"]`` meant pytest never collected it: it had not run in CI or locally
since it was committed. Ported here so it does.

Every segment x evidence combo must produce a 3-email sequence that passes QA
with zero sequence issues.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

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


@pytest.mark.parametrize("segment", list(SEGMENT_COPY))
@pytest.mark.parametrize("evidence", list(OPENERS))
def test_sequence_passes_qa(segment: str, evidence: str) -> None:
    email = f"lead-{segment}-{evidence}@example-biz.com"
    row = fake_row(segment, email)
    research = fake_research(row, evidence)
    seq, variant = generate_sequence(row, research)
    seq = fix_sequence(seq, row, research)

    assert len(seq) == 3, f"{segment}/{evidence}: expected 3 emails"
    assert variant, f"{segment}/{evidence}: empty copy_variant"

    for step, (subj, body) in enumerate(seq, start=1):
        result = qa(subj, body, research["company"])
        assert result["pass"], (
            f"{segment}/{evidence} email {step}: {result['issues']} (subject={subj!r})"
        )
        assert body.startswith("Hi,\n\n"), (
            f"{segment}/{evidence} email {step}: greeting is not bare 'Hi,'"
        )

    assert not sequence_issues(seq), f"{segment}/{evidence}: sequence issues"


def test_sanitize_drops_poisoned_paragraph() -> None:
    """A banned word takes its whole paragraph, not just itself.

    Word-stripping leaves 'We offer and edits for your brand.' — grammatical
    wreckage that reads worse than the sentence being gone.
    """
    _, body = sanitize_email(
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
