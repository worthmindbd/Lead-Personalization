"""fit_score is what keeps skip-tier leads out of the campaign.

``process_batch`` excludes leads whose ``fit_score`` is ``"skip"``. That only
works if normalization actually sets the column — and
``lead_personalization.pipeline.normalize_row`` did not. Anything normalized
through the library path came out with no ``fit_score`` at all, which never
equals ``"skip"``, so every skip-tier lead would have been researched, written
copy for, and exported.

On a real 3,045-row list that is 740 leads — 24% of the file.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lead_personalization.pipeline import DERIVED_FIELDS, normalize_row  # noqa: E402
from lead_personalization.segments import fit_score_for  # noqa: E402


def row(category: str) -> dict:
    return {
        "Name": "Lakeview Custom Homes LLC",
        "Email": "hello@lakeview.com",
        "Website": "https://lakeview.com",
        "First_category": category,
        "City": "Austin",
        "State": "Texas",
    }


def test_normalize_row_always_sets_fit_score():
    assert "fit_score" in normalize_row(0, row("Custom home builder"))


def test_fit_score_is_in_the_declared_schema():
    """Present on the row but missing from DERIVED_FIELDS is the same bug one
    layer up: the CSV writer would drop it."""
    assert "fit_score" in DERIVED_FIELDS


@pytest.mark.parametrize("category", ["Custom home builder", "Interior designer", "Dentist", ""])
def test_normalized_fit_score_matches_the_segment_rule(category: str):
    out = normalize_row(0, row(category))
    assert out["fit_score"] == fit_score_for(out["aevora_segment"], category)


# The real skip tier is the competition — you do not pitch video editing to a
# video production house. These are the four commonest skip categories on the
# july-20-2026 list (228 + 53 + 48 + 34 rows of the 740 it skips).
SKIP_CATEGORIES = [
    "Film production company",
    "Recording studio",
    "Animation studio",
    "Video editing service",
]


@pytest.mark.parametrize("category", SKIP_CATEGORIES)
def test_a_competitor_is_actually_marked_skip(category: str):
    """The guard in process_batch is worthless if nothing ever produces "skip"."""
    out = normalize_row(0, row(category))
    assert out["aevora_segment"] == "low_fit"
    assert out["fit_score"] == "skip"
