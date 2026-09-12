"""regen_subjects must resolve each research item to its OWN source row.

The script rewrote shipped subjects by matching research items back to the
normalized CSV *by email*. Two rows sharing an address — a scenario the main
path explicitly supports and tests — both matched the first row, so the second
lead's regenerated subject was built from the wrong city/category/name. The
fix is the resolution ``build_enriched`` already uses: row_index first, email
only as the legacy fallback.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "personalization"))

import regen_subjects  # noqa: E402
from lead_personalization.research import fallback_research_item  # noqa: E402


def norm_row(i: int, city: str, company: str, email: str = "same@x.com") -> dict:
    return {
        "row_index": str(i),
        "primary_email": email,
        "company_name": company,
        "Name": company,
        "first_name": "",
        "last_name": "",
        "title": "",
        "outreach_tier": "company",
        "aevora_segment": "low_fit",
        "City": city,
        "State": "Texas",
        "First_category": "Spa",
        "Website": "",
    }


# ---------------------------------------------------------------------------
# The row resolution
# ---------------------------------------------------------------------------


def test_rows_sharing_an_address_resolve_by_row_index():
    rows = [norm_row(0, "Austin", "Co A"), norm_row(1, "Dallas", "Co B")]
    by_row_index, by_email = regen_subjects.index_source_rows(rows)

    first = regen_subjects.source_row_for({"row_index": 0, "email": "same@x.com"},
                                          by_row_index, by_email)
    second = regen_subjects.source_row_for({"row_index": 1, "email": "same@x.com"},
                                           by_row_index, by_email)

    assert first["City"] == "Austin"
    assert second["City"] == "Dallas"


def test_legacy_items_without_row_index_fall_back_to_email():
    rows = [norm_row(0, "Austin", "Co A", email="a@x.com"),
            norm_row(1, "Dallas", "Co B", email="b@x.com")]
    by_row_index, by_email = regen_subjects.index_source_rows(rows)

    matched = regen_subjects.source_row_for({"email": "B@x.com"}, by_row_index, by_email)

    # The email fallback exists for artifacts that predate row-keyed research
    # JSON, and resolves exactly like build_enriched's (case-insensitive).
    assert matched["City"] == "Dallas"


def test_an_unmatched_item_resolves_to_none():
    rows = [norm_row(0, "Austin", "Co A")]
    by_row_index, by_email = regen_subjects.index_source_rows(rows)

    assert regen_subjects.source_row_for(
        {"row_index": 7, "email": "ghost@x.com"}, by_row_index, by_email
    ) is None


# ---------------------------------------------------------------------------
# End to end through main()
# ---------------------------------------------------------------------------


@pytest.fixture
def regen_env(tmp_path, monkeypatch):
    """A minimal list workdir: state entry + one archived stamp of artifacts."""
    workdir = tmp_path / "leads" / "pipeline" / "test-list"
    stamp_dir = workdir / "artifacts" / "20260911-000000"
    stamp_dir.mkdir(parents=True)

    state = tmp_path / "state.json"
    state.write_text(
        json.dumps({"lists": {"Test List": {"slug": "test-list"}}}), encoding="utf-8"
    )
    monkeypatch.setattr(regen_subjects, "STATE", state)
    monkeypatch.setattr(regen_subjects, "ROOT", tmp_path)

    rows = [norm_row(0, "Austin", "Co A"), norm_row(1, "Dallas", "Co B")]
    normalized = stamp_dir / "test-list-normalized.csv"
    with normalized.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    research_items = [fallback_research_item(row, "stub") for row in rows]
    research_path = stamp_dir / "test-list-batch-001-research.json"
    research_path.write_text(json.dumps(research_items), encoding="utf-8")

    return tmp_path, workdir, stamp_dir


def test_main_regenerates_each_lead_from_its_own_row(regen_env, monkeypatch):
    tmp_path, workdir, stamp_dir = regen_env
    calls: list[tuple] = []
    real_generate = regen_subjects.generate_sequence

    def spy(src, item, pack, **kwargs):
        calls.append((src.get("row_index"), item.get("row_index")))
        return real_generate(src, item, pack, **kwargs)

    monkeypatch.setattr(regen_subjects, "generate_sequence", spy)
    monkeypatch.setattr(sys, "argv", ["regen_subjects.py", "--list", "Test List"])

    regen_subjects.main()

    # The regression: email-only matching produced [("0", 0), ("0", 1)] —
    # both leads regenerated from the first row.
    assert calls == [("0", 0), ("1", 1)]

    copy_path = stamp_dir / "test-list-batch-001-copy.json"
    copy = json.loads(copy_path.read_text(encoding="utf-8"))
    assert sorted(copy) == ["0", "1"]
    for seq in copy.values():
        assert len(seq) == 3

    cumulative = workdir / "test-list-enriched.csv"
    assert cumulative.is_file()
