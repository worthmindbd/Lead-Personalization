"""Parity guard: the JSON offer pack + new copywriter must produce byte-for-byte
identical copy to the legacy hardcoded engine in scripts/personalization/.

If this fails, the offer pack has drifted from the original pools and the
extraction is no longer a faithful refactor.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lead_personalization.copywriter import (  # noqa: E402
    fix_sequence as new_fix,
    generate_sequence as new_generate,
)
from lead_personalization.offer_pack import load_offer_pack  # noqa: E402

# Imported bare, on purpose. This used to sit in a try/except that set
# LEGACY_AVAILABLE = False and skipped the module — which meant the one test
# tying this suite to the engine that actually ships could disappear while the
# suite stayed green. If scripts/personalization stops importing, that is the
# failure worth seeing, not a skip line nobody reads.
from personalization.process_batch import (  # noqa: E402
    OPENERS as LEGACY_OPENERS,
    SEGMENT_COPY as LEGACY_SEGMENT_COPY,
    fix_sequence as legacy_fix,
    generate_sequence as legacy_generate,
)

PACK = load_offer_pack("aevora")


def _row(segment: str, email: str) -> dict:
    return {
        "primary_email": email,
        "company_name": "Harborline Interiors",
        "Name": "Harborline Interiors",
        "First_category": "Interior designer",
        "City": "Miami",
        "State": "Florida",
        "aevora_segment": segment,
        "fit_score": "medium",
        "Youtube_URL": "https://youtube.com/@harborline",
        "Instagram_URL": "",
    }


def _research(row: dict, evidence: str) -> dict:
    snippet = "Interiors designed for coastal living" if evidence == "positioning" else ""
    li_topic = "lessons from our latest project handoff" if evidence == "linkedin_posts" else ""
    return {
        "email": row["primary_email"],
        "company": row["company_name"],
        "research_signal": (
            f'site positioning: "{snippet}"; video on site: yes; Miami, Florida'
            if snippet
            else "video on site: no; YouTube linked; Miami, Florida"
        ),
        "signal_strength": "strong" if evidence != "weak" else "weak",
        "evidence": evidence,
        "snippet": snippet,
        "social_channel": "YouTube" if evidence == "social_video" else "",
        "linkedin_topic": li_topic,
    }


def test_pack_matches_legacy_pools() -> None:
    assert PACK.openers == LEGACY_OPENERS
    assert PACK.segment_copy == LEGACY_SEGMENT_COPY


def test_generated_copy_matches_legacy() -> None:
    for segment in LEGACY_SEGMENT_COPY:
        for evidence in LEGACY_OPENERS:
            email = f"parity-{segment}-{evidence}@example-biz.com"
            row = _row(segment, email)
            research = _research(row, evidence)

            legacy_seq, legacy_variant = legacy_generate(row, dict(research))
            legacy_seq = legacy_fix(legacy_seq, row, research)

            new_seq, new_variant = new_generate(row, dict(research), PACK)
            new_seq = new_fix(new_seq, row, research, PACK)

            assert new_variant == legacy_variant, f"{segment}/{evidence} variant mismatch"
            assert new_seq == legacy_seq, f"{segment}/{evidence} sequence mismatch"
