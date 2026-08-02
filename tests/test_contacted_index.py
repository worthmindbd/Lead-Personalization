"""Cross-list suppression: nobody gets two sequences.

Drive lists overlap — the same business appears in more than one export. The
delta used to be deduped only against the list's own enriched CSV, so 192 of
4,961 enriched rows were people already queued on an earlier list, and 1,423
still-unverified addresses sat in 2+ cleaned lists waiting to do the same.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pipeline"))

import run_pipeline as rp  # noqa: E402


def write_csv(path: Path, emails: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["primary_email", "company"])
        writer.writeheader()
        for i, email in enumerate(emails):
            writer.writerow({"primary_email": email, "company": f"Co {i}"})
    return path


@pytest.fixture
def index(tmp_path, monkeypatch):
    """Point the contacted index at a throwaway file."""
    path = tmp_path / ".pipeline" / "contacted.json"
    monkeypatch.setattr(rp, "CONTACTED_FILE", path)
    return path


# ---------------------------------------------------------------------------
# compute_delta
# ---------------------------------------------------------------------------


def test_address_personalized_on_another_list_is_excluded(tmp_path, index):
    verified = write_csv(tmp_path / "b-verified.csv", ["shared@x.com", "fresh@x.com"])
    enriched = tmp_path / "b-enriched.csv"  # list B has personalized nobody yet

    rp.record_contacted("list-a", ["shared@x.com"])
    _, delta, suppressed = rp.compute_delta(
        verified, enriched, contacted=rp.load_contacted(), slug="list-b"
    )

    assert [rp.row_email(r) for r in delta] == ["fresh@x.com"]
    assert suppressed == 1


def test_a_list_is_not_suppressed_by_its_own_claims(tmp_path, index):
    """If a list's enriched CSV is lost, rebuild it — don't skip the leads."""
    verified = write_csv(tmp_path / "a-verified.csv", ["mine@x.com"])
    enriched = tmp_path / "a-enriched.csv"  # gone

    rp.record_contacted("list-a", ["mine@x.com"])
    _, delta, suppressed = rp.compute_delta(
        verified, enriched, contacted=rp.load_contacted(), slug="list-a"
    )

    assert [rp.row_email(r) for r in delta] == ["mine@x.com"]
    assert suppressed == 0


def test_delta_still_dedupes_within_the_list(tmp_path, index):
    verified = write_csv(tmp_path / "v.csv", ["a@x.com", "A@X.com", "b@x.com"])
    enriched = write_csv(tmp_path / "e.csv", ["b@x.com"])

    _, delta, suppressed = rp.compute_delta(verified, enriched, contacted={}, slug="s")

    assert [rp.row_email(r) for r in delta] == ["a@x.com"]
    assert suppressed == 0


def test_no_index_behaves_exactly_as_before(tmp_path, index):
    verified = write_csv(tmp_path / "v.csv", ["a@x.com", "b@x.com"])
    _, delta, suppressed = rp.compute_delta(verified, tmp_path / "missing.csv")
    assert len(delta) == 2 and suppressed == 0


# ---------------------------------------------------------------------------
# record / backfill
# ---------------------------------------------------------------------------


def test_first_writer_keeps_the_address(index):
    rp.record_contacted("list-a", ["x@x.com"])
    added = rp.record_contacted("list-b", ["x@x.com", "y@x.com"])

    assert added == 1
    assert rp.load_contacted() == {"x@x.com": "list-a", "y@x.com": "list-b"}


def test_backfill_attributes_overlap_to_the_older_list(tmp_path, index, monkeypatch):
    monkeypatch.setattr(rp, "ROOT", tmp_path)
    write_csv(tmp_path / "old-enriched.csv", ["shared@x.com", "old@x.com"])
    write_csv(tmp_path / "new-enriched.csv", ["shared@x.com", "new@x.com"])
    state = {
        "lists": {
            # Deliberately newest-first: ordering must come from the dates, not
            # from dict insertion order.
            "New": {"slug": "new", "drive_mtime": "2026-07-31T00:00:00Z",
                    "enriched_csv": "new-enriched.csv"},
            "Old": {"slug": "old", "drive_mtime": "2026-07-06T00:00:00Z",
                    "enriched_csv": "old-enriched.csv"},
        }
    }

    unique, duplicates = rp.backfill_contacted(state)

    assert unique == 3
    assert duplicates == 1
    assert rp.load_contacted()["shared@x.com"] == "old"


def test_backfill_is_idempotent(tmp_path, index, monkeypatch):
    monkeypatch.setattr(rp, "ROOT", tmp_path)
    write_csv(tmp_path / "a-enriched.csv", ["a@x.com"])
    state = {"lists": {"A": {"slug": "a", "drive_mtime": "2026-07-01T00:00:00Z",
                             "enriched_csv": "a-enriched.csv"}}}

    first = rp.backfill_contacted(state)
    second = rp.backfill_contacted(state)

    assert first[0] == second[0] == 1
    assert rp.load_contacted() == {"a@x.com": "a"}


def test_missing_or_corrupt_index_reads_as_empty(index):
    assert rp.load_contacted() == {}
    index.parent.mkdir(parents=True, exist_ok=True)
    index.write_text('{"addresses": null}', encoding="utf-8")
    assert rp.load_contacted() == {}
