"""The TOTAL row has to count people, not rows.

The Drive lists overlap heavily — 192 addresses were already personalized twice
and 1,423 unverified addresses sit on two or more cleaned lists. Summing the
per-list columns turned that overlap into work: 17,243 addresses reported as
still needing verification when only 15,634 exist, which at 500 a day is three
days of budget that was never there.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pipeline"))

import report  # noqa: E402


def write_list(slug: str, *, cleaned: list[str], verified: list[str] = (),
               enriched: list[str] = ()) -> None:
    """Lay out one list's stage CSVs where build_rows looks for them."""
    workdir = report.WORK_ROOT / slug
    workdir.mkdir(parents=True, exist_ok=True)
    for name, emails in (("cleaned", cleaned), ("verified", verified),
                         ("enriched", enriched)):
        if not emails:
            continue
        with (workdir / f"{slug}-{name}.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["primary_email", "company"])
            writer.writeheader()
            for i, email in enumerate(emails):
                writer.writerow({"primary_email": email, "company": f"Co {i}"})


def set_cache(emails: list[str]) -> None:
    report.REOON_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    report.REOON_CACHE_FILE.write_text(
        json.dumps({e: {"status": "safe"} for e in emails}), encoding="utf-8"
    )


def set_tombstones(emails: list[str]) -> None:
    report.REOON_REJECTED_FILE.parent.mkdir(parents=True, exist_ok=True)
    report.REOON_REJECTED_FILE.write_text(
        json.dumps({"addresses": {e: {"status": "inferred_rejected"} for e in emails}}),
        encoding="utf-8",
    )


def state_for(*entries: tuple[str, str, dict]) -> dict:
    """(title, drive_mtime, extra) -> a state dict. Slug is derived from title."""
    lists = {}
    for title, mtime, extra in entries:
        lists[title] = {
            "slug": title.lower().replace(" ", "-").replace(",", "-"),
            "drive_mtime": mtime,
            **extra,
        }
    return {"version": 1, "lists": lists}


@pytest.fixture
def overlapping():
    """Two lists sharing three of their five cleaned addresses.

    older: shared1..3 + old1, old2   (5 cleaned, shared1 verified+enriched)
    newer: shared1..3 + new1         (4 cleaned)
    Nothing is cached, so 6 distinct addresses are pending against a column
    sum of 9.
    """
    shared = ["shared1@x.com", "shared2@x.com", "shared3@x.com"]
    write_list("older", cleaned=shared + ["old1@x.com", "old2@x.com"],
               verified=["shared1@x.com"], enriched=["shared1@x.com"])
    write_list("newer", cleaned=shared + ["new1@x.com"])
    return state_for(
        ("older", "2026-07-06T00:00:00Z", {"pending_verification": 999}),
        ("newer", "2026-07-31T00:00:00Z", {"pending_verification": 999}),
    )


# ---------------------------------------------------------------------------
# Unique totals
# ---------------------------------------------------------------------------


def test_total_pending_counts_each_address_once(overlapping):
    rows, unique = report.build_rows(overlapping)
    total = report.total_row(rows, unique)

    assert [r["pending_verification"] for r in rows] == [5, 4]  # sums to 9
    assert total["pending_verification"] == 6


def test_unique_pending_sums_to_the_total(overlapping):
    rows, unique = report.build_rows(overlapping)
    total = report.total_row(rows, unique)

    assert sum(r["unique_pending"] for r in rows) == total["pending_verification"]
    assert total["unique_pending"] == total["pending_verification"]


def test_overlap_is_attributed_to_the_older_list(overlapping):
    rows, _ = report.build_rows(overlapping)

    assert rows[0]["list_title"] == "older"
    assert rows[0]["unique_pending"] == 5  # claims all three shared addresses
    assert rows[1]["unique_pending"] == 1  # only its own new1@


def test_total_cleaned_and_personalized_are_unique_too(overlapping):
    rows, unique = report.build_rows(overlapping)
    total = report.total_row(rows, unique)

    assert [r["cleaned_leads"] for r in rows] == [5, 4]
    assert total["cleaned_leads"] == 6
    assert total["personalized_leads"] == 1


def test_raw_rows_still_sum(overlapping):
    """Raw rows are not addresses yet — deduping them would be a guess."""
    rows, unique = report.build_rows(overlapping)
    rows[0]["raw_leads"], rows[1]["raw_leads"] = 100, 200

    assert report.total_row(rows, unique)["raw_leads"] == 300


# ---------------------------------------------------------------------------
# Pending is measured, not recalled
# ---------------------------------------------------------------------------


def test_pending_ignores_a_stale_state_value(overlapping):
    """Every entry claims 999 pending; the CSVs say otherwise."""
    rows, _ = report.build_rows(overlapping)

    assert [r["pending_verification"] for r in rows] == [5, 4]


def test_cached_and_tombstoned_addresses_are_not_pending(overlapping):
    set_cache(["shared1@x.com", "old1@x.com"])
    set_tombstones(["shared2@x.com", "new1@x.com"])

    rows, unique = report.build_rows(overlapping)
    total = report.total_row(rows, unique)

    assert [r["pending_verification"] for r in rows] == [2, 1]  # shared3+old2, shared3
    assert total["pending_verification"] == 2


def test_a_done_list_reads_zero_only_when_the_addresses_are_accounted_for():
    """The bug this replaces: reconcile hard-set 0 for anything marked done."""
    write_list("finished", cleaned=["kept@x.com", "rejected@x.com"],
               verified=["kept@x.com"])
    state = state_for(("finished", "2026-07-06T00:00:00Z",
                       {"stage": "done", "pending_verification": 0}))

    rows, _ = report.build_rows(state)
    assert rows[0]["pending_verification"] == 2  # neither address is accounted for

    set_cache(["kept@x.com"])
    set_tombstones(["rejected@x.com"])
    rows, _ = report.build_rows(state)
    assert rows[0]["pending_verification"] == 0


def test_unreadable_cleaned_list_falls_back_to_state():
    """An unknown backlog must not be reported as an empty one."""
    state = state_for(("missing", "2026-07-06T00:00:00Z",
                       {"pending_verification": 42}))

    rows, unique = report.build_rows(state)

    assert rows[0]["pending_verification"] == 42
    assert rows[0]["unique_pending"] == ""  # not 0 — we cannot attribute it
    assert unique["pending_verification"] == 0


def test_corrupt_cache_does_not_break_the_report(overlapping):
    report.REOON_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    report.REOON_CACHE_FILE.write_text("{not json", encoding="utf-8")

    rows, _ = report.build_rows(overlapping)

    assert [r["pending_verification"] for r in rows] == [5, 4]


# ---------------------------------------------------------------------------
# The sheet's column budget
# ---------------------------------------------------------------------------


def test_the_pipeline_owns_exactly_ten_columns():
    """Column K of the Enrichment-Reports sheet is hand-maintained.

    sheets_sync writes A..<len(COLUMNS)>, so an eleventh column here silently
    overwrites the human's "Imported to Campaign?" values on the next sync.
    """
    assert len(report.COLUMNS) == 10
    assert set(report.UNIQUE_COLUMNS) | set(report.SUMMED_COLUMNS) <= set(report.COLUMNS)
    assert not set(report.UNIQUE_COLUMNS) & set(report.SUMMED_COLUMNS)


def test_every_row_carries_every_column(overlapping):
    rows, unique = report.build_rows(overlapping)

    for row in rows + [report.total_row(rows, unique)]:
        assert list(row) == report.COLUMNS
