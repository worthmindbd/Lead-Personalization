"""Shipped copy is immutable: a category's segment may never silently move.

Every personalized row on disk carries the ``aevora_segment`` its copy was
written under, and much of it is live in ESPs. If a later edit to
``lead_personalization/segments.py`` moves a category to a different segment,
future leads in that category get a different pitch under the same label, and
per-segment reply rates stop being comparable.

This test reads the enriched CSVs under ``leads/pipeline/`` and asserts that
``segment_for_category`` still returns a segment each category actually shipped
with. The only exceptions are the deliberate going-forward migrations from
commit 9240c43 (2026-09-12), which re-angled a handful of home/real-estate
categories AFTER their first rows had already gone out as low_fit.

Skips when no enriched CSVs exist (a fresh clone), so CI without lead data
still passes.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import pytest

from lead_personalization.segments import canonical_segment, segment_for_category

ROOT = Path(__file__).resolve().parents[1]
ENRICHED_GLOB = "leads/pipeline/*/*-enriched.csv"

# Commit 9240c43 mapped these after some rows had already shipped low_fit.
# The old rows keep their generic copy; everything since ships targeted copy.
# Adding a name here requires the same justification: a written-down decision
# to migrate, made knowingly after rows went out under the old segment.
DELIBERATE_MIGRATIONS = {
    "Apartment building",      # -> real_estate (9240c43)
    "Housing development",     # -> real_estate (9240c43)
    "Real estate appraiser",   # -> real_estate (9240c43)
    "Building firm",           # -> home_design  (9240c43)
    # 2026-11-12: studios, photographers, and producers moved out of
    # creative_marketing/general into production_studios. Their old openers
    # told video producers "your site has no video"; the new segment pitches
    # white-label edit capacity. Old rows keep their copy.
    "Aerial photographer", "Animation studio", "Audio visual consultant",
    "Commercial photographer", "Drone service", "Film production company",
    "Movie studio", "Music producer", "Photo booth", "Photo lab", "Photographer",
    "Photography service", "Photography studio", "Portrait studio",
    "Recording studio", "Video duplication service", "Video editing service",
    "Video production service", "Wedding photographer",
}


def _shipped_segments() -> dict[str, set[str]]:
    shipped: dict[str, set[str]] = defaultdict(set)
    for path in ROOT.glob(ENRICHED_GLOB):
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                cat = (row.get("First_category") or "").strip()
                seg = (row.get("aevora_segment") or "").strip()
                if cat and seg:
                    # Rows on disk still carry the pre-rename "low_fit" key.
                    # Canonicalizing keeps the freeze test about real
                    # re-angling rather than about a naming cleanup.
                    shipped[cat].add(canonical_segment(seg))
    return dict(shipped)


def test_no_shipped_category_changes_segment():
    shipped = _shipped_segments()
    if not shipped:  # fresh clone without lead data
        pytest.skip("no enriched CSVs under leads/pipeline/")
    moved = sorted(
        cat for cat, segs in shipped.items()
        if canonical_segment(segment_for_category(cat)) not in segs
        and cat not in DELIBERATE_MIGRATIONS
    )
    assert not moved, (
        f"segment_for_category moved these already-shipped categories: {moved}. "
        "Their copy is live in ESPs; pin them back or add a documented "
        "migration to DELIBERATE_MIGRATIONS."
    )


def test_deliberate_migrations_still_exist():
    shipped = _shipped_segments()
    if not shipped:
        pytest.skip("no enriched CSVs under leads/pipeline/")
    stale = sorted(c for c in DELIBERATE_MIGRATIONS if c not in shipped)
    assert not stale, (
        f"these migrations reference categories with no shipped rows: {stale}; "
        "prune them so the allowlist stays minimal"
    )
