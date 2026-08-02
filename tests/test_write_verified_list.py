"""Building the verified list from the source CSV plus the Reoon cache.

A row can carry several addresses (``a@x.com|b@x.com``) and the verifier sends
every one of them, so every one costs a credit. The list-writer used to look at
the first address only: a secondary we had paid to verify could never produce a
row, and a business was dropped over a dead info@ while its owner's working
address sat verified in the same cell.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from verify_emails_reoon import write_verified_list  # noqa: E402


def source_csv(tmp_path: Path, rows: list[dict], column: str = "primary_email") -> Path:
    path = tmp_path / "source.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[column, "company"])
        writer.writeheader()
        writer.writerows(rows)
    return path


def read(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run(tmp_path: Path, rows: list[dict], cache: dict) -> tuple[list[dict], int, dict]:
    source = source_csv(tmp_path, rows)
    kept, checked, counts, out = write_verified_list(source, tmp_path / "out.csv", cache)
    written = read(out)
    assert kept == len(written)
    return written, checked, counts


SAFE = {"status": "safe"}
BAD = {"status": "invalid"}


# ---------------------------------------------------------------------------
# Multi-address rows
# ---------------------------------------------------------------------------


def test_a_safe_secondary_keeps_the_row(tmp_path):
    written, _, _ = run(
        tmp_path,
        [{"primary_email": "dead@x.com|owner@x.com", "company": "Acme"}],
        {"dead@x.com": BAD, "owner@x.com": SAFE},
    )

    assert len(written) == 1
    assert written[0]["primary_email"] == "owner@x.com"  # not the dead one
    assert written[0]["company"] == "Acme"


def test_a_safe_primary_wins_over_a_safe_secondary(tmp_path):
    written, _, _ = run(
        tmp_path,
        [{"primary_email": "first@x.com|second@x.com", "company": "Acme"}],
        {"first@x.com": SAFE, "second@x.com": SAFE},
    )

    assert [r["primary_email"] for r in written] == ["first@x.com"]


def test_a_row_with_no_passing_address_is_dropped(tmp_path):
    written, _, _ = run(
        tmp_path,
        [{"primary_email": "a@x.com|b@x.com", "company": "Acme"}],
        {"a@x.com": BAD, "b@x.com": {"status": "disabled"}},
    )

    assert written == []


def test_every_checked_address_is_counted_not_just_the_first(tmp_path):
    """The run prints checked against a count of addresses, not of rows."""
    _, checked, counts = run(
        tmp_path,
        [{"primary_email": "a@x.com|b@x.com|c@x.com", "company": "Acme"}],
        {"a@x.com": BAD, "b@x.com": SAFE, "c@x.com": {"status": "catch_all"}},
    )

    assert checked == 3
    assert counts == {"invalid": 1, "safe": 1, "catch_all": 1}


def test_an_unchecked_secondary_does_not_block_a_safe_primary(tmp_path):
    written, checked, _ = run(
        tmp_path,
        [{"primary_email": "good@x.com|never-checked@x.com", "company": "Acme"}],
        {"good@x.com": SAFE},
    )

    assert [r["primary_email"] for r in written] == ["good@x.com"]
    assert checked == 1


# ---------------------------------------------------------------------------
# Behaviour that must not regress
# ---------------------------------------------------------------------------


def test_only_keep_statuses_survive(tmp_path):
    written, _, _ = run(
        tmp_path,
        [{"primary_email": "safe@x.com", "company": "A"},
         {"primary_email": "role@x.com", "company": "B"},
         {"primary_email": "catch@x.com", "company": "C"},
         {"primary_email": "bad@x.com", "company": "D"}],
        {"safe@x.com": SAFE, "role@x.com": {"status": "role_account"},
         "catch@x.com": {"status": "catch_all"}, "bad@x.com": BAD},
    )

    assert [r["primary_email"] for r in written] == ["safe@x.com", "role@x.com"]
    assert [r["Status"] for r in written] == ["safe", "role_account"]


def test_unverified_rows_are_left_for_a_later_run(tmp_path):
    """No cache entry is 'not yet checked', which is not the same as rejected."""
    written, checked, _ = run(
        tmp_path,
        [{"primary_email": "known@x.com", "company": "A"},
         {"primary_email": "pending@x.com", "company": "B"}],
        {"known@x.com": SAFE},
    )

    assert [r["primary_email"] for r in written] == ["known@x.com"]
    assert checked == 1


def test_the_same_address_is_written_once(tmp_path):
    written, _, _ = run(
        tmp_path,
        [{"primary_email": "dup@x.com", "company": "First"},
         {"primary_email": "DUP@x.com", "company": "Second"}],
        {"dup@x.com": SAFE},
    )

    assert [r["company"] for r in written] == ["First"]


def test_rows_without_an_address_are_skipped(tmp_path):
    written, checked, _ = run(
        tmp_path,
        [{"primary_email": "", "company": "A"},
         {"primary_email": "ok@x.com", "company": "B"}],
        {"ok@x.com": SAFE},
    )

    assert [r["company"] for r in written] == ["B"]
    assert checked == 1


def test_status_column_is_added_to_a_source_that_lacks_one(tmp_path):
    written, _, _ = run(
        tmp_path, [{"primary_email": "safe@x.com", "company": "A"}], {"safe@x.com": SAFE}
    )

    assert list(written[0]) == ["primary_email", "company", "Status"]


def test_an_empty_cache_writes_a_header_only_file(tmp_path):
    source = source_csv(tmp_path, [{"primary_email": "a@x.com", "company": "A"}])
    kept, checked, counts, out = write_verified_list(source, tmp_path / "out.csv", {})

    assert (kept, checked, counts) == (0, 0, {})
    assert read(out) == []
