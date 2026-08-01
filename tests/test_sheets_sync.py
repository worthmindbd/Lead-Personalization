"""Planning tests for the in-place Enrichment-Reports sheet sync.

These cover `plan_writes` only — the pure layer. No network, no credentials.
The guarantee under test: the pipeline writes columns A..J and nothing else,
so hand-maintained columns (e.g. "Imported to Campaign?") survive every run.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pipeline"))

from sheets_sync import (  # noqa: E402
    SheetsSyncError,
    column_letter,
    plan_writes,
)

COLUMNS = [
    "list_title", "stage", "raw_leads", "cleaned_leads", "verified_leads",
    "personalized_leads", "pending_verification", "pending_personalization",
    "verify_complete", "last_updated",
]

# The live sheet: header + six lists + TOTAL.
SHEET_COLUMN_A = [
    "list_title", "July 6,2026", "July 7,2026", "July 8,2026",
    "July 17,2026", "July 20,2026", "July 25,2026", "TOTAL",
]


def row(title: str, **kwargs) -> dict:
    data = {col: "" for col in COLUMNS}
    data["list_title"] = title
    data.update(kwargs)
    return data


def ranges(plan) -> list[str]:
    return [rng for rng, _ in plan.updates]


def test_column_letter() -> None:
    assert column_letter(1) == "A"
    assert column_letter(10) == "J"
    assert column_letter(27) == "AA"


def test_existing_lists_update_in_place_without_inserts() -> None:
    rows = [row("July 8,2026", stage="verifying"), row("TOTAL")]
    plan = plan_writes(SHEET_COLUMN_A, COLUMNS, rows, COLUMNS)

    assert plan.inserts == []
    # July 8 is sheet row 4; TOTAL is row 8. Neither moves.
    assert ranges(plan) == ["A4:J4", "A8:J8"]


def test_new_list_is_inserted_above_total() -> None:
    rows = [row("July 6,2026"), row("July 31,2026", stage="cleaning"), row("TOTAL")]
    plan = plan_writes(SHEET_COLUMN_A, COLUMNS, rows, COLUMNS)

    # TOTAL sits at row 8 -> insert at 0-based index 7, pushing TOTAL to row 9.
    assert plan.inserts == [7]
    assert ranges(plan) == ["A2:J2", "A8:J8", "A9:J9"]

    written = dict(plan.updates)
    assert written["A8:J8"][0] == "July 31,2026"
    assert written["A9:J9"][0] == "TOTAL"


def test_two_new_lists_each_get_a_row() -> None:
    rows = [row("July 31,2026"), row("Aug 1,2026"), row("TOTAL")]
    plan = plan_writes(SHEET_COLUMN_A, COLUMNS, rows, COLUMNS)

    assert plan.inserts == [7, 8]
    assert ranges(plan) == ["A8:J8", "A9:J9", "A10:J10"]
    assert dict(plan.updates)["A10:J10"][0] == "TOTAL"


def test_sheet_without_total_appends() -> None:
    column_a = ["list_title", "July 6,2026"]
    rows = [row("July 6,2026"), row("July 7,2026"), row("TOTAL")]
    plan = plan_writes(column_a, COLUMNS, rows, COLUMNS)

    assert plan.inserts == []
    assert ranges(plan) == ["A2:J2", "A3:J3", "A4:J4"]
    assert dict(plan.updates)["A4:J4"][0] == "TOTAL"


def test_list_in_sheet_but_absent_from_report_is_left_alone() -> None:
    rows = [row("July 6,2026"), row("TOTAL")]
    plan = plan_writes(SHEET_COLUMN_A, COLUMNS, rows, COLUMNS)

    # Rows 3-7 (July 7 .. July 25) are neither written nor deleted.
    assert ranges(plan) == ["A2:J2", "A8:J8"]


def test_header_written_only_when_it_differs() -> None:
    rows = [row("July 6,2026"), row("TOTAL")]

    matching = plan_writes(SHEET_COLUMN_A, COLUMNS, rows, COLUMNS)
    assert "A1:J1" not in ranges(matching)

    stale = plan_writes(SHEET_COLUMN_A, ["list_title", "stage"], rows, COLUMNS)
    assert ranges(stale)[0] == "A1:J1"
    assert dict(stale.updates)["A1:J1"] == COLUMNS


def test_every_write_stops_at_the_last_pipeline_column() -> None:
    """The core guarantee: manual columns (K onward) are never in a range."""
    rows = [row(t) for t in ("July 6,2026", "July 31,2026")] + [row("TOTAL")]
    plan = plan_writes(SHEET_COLUMN_A, ["stale"], rows, COLUMNS)

    assert plan.updates, "expected writes to plan"
    for rng, values in plan.updates:
        assert rng.split(":")[1].rstrip("0123456789") == "J"
        assert len(values) == len(COLUMNS) == 10


def test_trailing_blank_rows_are_not_mistaken_for_data() -> None:
    padded = SHEET_COLUMN_A + ["", "", "  "]
    rows = [row("July 6,2026"), row("TOTAL")]
    plan = plan_writes(padded, COLUMNS, rows, COLUMNS)

    assert ranges(plan) == ["A2:J2", "A8:J8"]


def test_empty_report_refuses_to_write() -> None:
    with pytest.raises(SheetsSyncError, match="no list rows"):
        plan_writes(SHEET_COLUMN_A, COLUMNS, [row("TOTAL")], COLUMNS)

    with pytest.raises(SheetsSyncError, match="no list rows"):
        plan_writes(SHEET_COLUMN_A, COLUMNS, [], COLUMNS)


def test_values_follow_column_order() -> None:
    rows = [row("July 6,2026", stage="done", raw_leads=14901, verify_complete=True),
            row("TOTAL")]
    plan = plan_writes(SHEET_COLUMN_A, COLUMNS, rows, COLUMNS)

    values = dict(plan.updates)["A2:J2"]
    assert values[0] == "July 6,2026"
    assert values[1] == "done"
    assert values[2] == 14901
    assert values[8] is True
