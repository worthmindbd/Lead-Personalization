"""Tombstones for addresses a lost cache had already checked.

The verifier caches every Reoon result, rejections included — that path is
fine. What is unrecoverable is history: 4,512 of the 5,012 cache entries are
``reseeded_from_verified_csv`` placeholders, and a reseed can only restore
addresses that *passed*. That left 3,255 addresses on the three completed
lists absent from the cache, one reset away from re-spending 6.5 days of the
500/day budget.
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
def list_state(tmp_path, monkeypatch):
    """One completed list: 4 cleaned, 2 kept, 1 already cached, 1 inferrable."""
    monkeypatch.setattr(rp, "ROOT", tmp_path)
    write_csv(tmp_path / "cleaned.csv", ["keep1@x.com", "keep2@x.com",
                                         "cached@x.com", "gone@x.com"])
    write_csv(tmp_path / "verified.csv", ["keep1@x.com", "keep2@x.com"])
    rp.save_json_atomic(rp.REOON_CACHE_FILE, {"cached@x.com": {"status": "catch_all"}})
    return {
        "lists": {
            "July 6,2026": {
                "slug": "july-6-2026",
                "verify_complete": True,
                "cleaned_csv": "cleaned.csv",
                "verified_csv": "verified.csv",
            }
        }
    }


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------


def test_only_unexplained_addresses_are_tombstoned(list_state):
    found = rp.backfill_rejected(list_state, apply=True)

    assert found == [("july-6-2026", 1)]
    tombstones = rp.load_rejected()
    assert list(tombstones) == ["gone@x.com"]
    assert tombstones["gone@x.com"]["status"] == "inferred_rejected"
    assert tombstones["gone@x.com"]["list"] == "july-6-2026"


def test_a_real_reoon_result_is_never_overwritten(list_state):
    rp.backfill_rejected(list_state, apply=True)
    assert "cached@x.com" not in rp.load_rejected()


def test_preview_writes_nothing(list_state):
    found = rp.backfill_rejected(list_state, apply=False)

    assert found == [("july-6-2026", 1)]
    assert not rp.REOON_REJECTED_FILE.exists()
    assert rp.load_rejected() == {}


def test_unfinished_list_is_left_alone(list_state):
    list_state["lists"]["July 6,2026"]["verify_complete"] = False

    assert rp.backfill_rejected(list_state, apply=True) == []
    assert rp.load_rejected() == {}


def test_backfill_is_idempotent(list_state):
    rp.backfill_rejected(list_state, apply=True)
    assert rp.backfill_rejected(list_state, apply=True) == []
    assert len(rp.load_rejected()) == 1


# ---------------------------------------------------------------------------
# Effect on pending
# ---------------------------------------------------------------------------


def test_tombstoned_address_does_not_count_as_pending(list_state, tmp_path):
    cleaned = tmp_path / "cleaned.csv"

    assert rp.pending_verification(cleaned) == 3  # keep1, keep2, gone
    rp.backfill_rejected(list_state, apply=True)
    assert rp.pending_verification(cleaned) == 2  # keep1, keep2 (reseed's job)


def test_corrupt_tombstone_file_reads_as_empty():
    rp.REOON_REJECTED_FILE.parent.mkdir(parents=True, exist_ok=True)
    rp.REOON_REJECTED_FILE.write_text('{"addresses": []}', encoding="utf-8")
    assert rp.load_rejected() == {}


# ---------------------------------------------------------------------------
# The verifier honours the tombstones
# ---------------------------------------------------------------------------


def test_verifier_skips_tombstoned_addresses(tmp_path, monkeypatch):
    import verify_emails_reoon as ver

    monkeypatch.setattr(ver, "REJECTED_FILE", tmp_path / "rejected.json")
    ver.save_json(
        tmp_path / "rejected.json",
        {"addresses": {"gone@x.com": {"status": "inferred_rejected"}}},
    )
    source = write_csv(tmp_path / "src.csv", ["fresh@x.com", "gone@x.com"])

    emails = ver.extract_emails_from_csv(source)
    rejected = ver.load_rejected()

    assert [e for e in emails if e not in rejected] == ["fresh@x.com"]
