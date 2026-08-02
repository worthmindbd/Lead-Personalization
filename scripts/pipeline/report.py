#!/usr/bin/env python3
"""Read-only progress report for the Drive lead pipeline.

Reads .pipeline/state.json (written by run_pipeline.py) plus the per-list stage
CSVs under leads/pipeline/<slug>/ and writes Report.csv at the project root:
one row per list, plus a TOTAL row.

Per-list columns count that list's own rows — what you see when you open its
CSV. The TOTAL row counts *people*. The Drive lists overlap heavily, so summing
the columns invents work that does not exist: 17,243 pending against 15,634 real
addresses, which at 500 verifications a day is three days of imaginary budget.

This script is strictly READ-ONLY with respect to pipeline state: it never
writes to state.json or any working file. It is safe to run repeatedly while
run_pipeline.py is actively rewriting state — state.json reads retry on a
partial/mid-write read (JSONDecodeError).

    .venv/bin/python scripts/pipeline/report.py
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import sheets_sync

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_emails_reoon import (  # noqa: E402
    CACHE_FILE as REOON_CACHE_FILE,
    REJECTED_FILE as REOON_REJECTED_FILE,
    extract_emails_from_csv,
)

STATE_FILE = ROOT / ".pipeline" / "state.json"
WORK_ROOT = ROOT / "leads" / "pipeline"
REPORT_FILE = ROOT / "Report.csv"
# Title of the native Google Sheet in the Drive root that --upload keeps in sync.
DRIVE_SHEET_NAME = "Enrichment-Reports"

# KEEP THIS AT TEN. sheets_sync writes columns A..<len(COLUMNS)> of the
# Enrichment-Reports sheet; column K holds a hand-maintained "Imported to
# Campaign?" column, and an eleventh entry here would overwrite it on the next
# sync. To show something new, spend one of the ten — which is what
# `unique_pending` did to `verify_complete` (a boolean that only ever restated
# `pending_verification == 0`).
COLUMNS = [
    "list_title",
    "stage",
    "raw_leads",
    "cleaned_leads",
    "verified_leads",
    "personalized_leads",
    "pending_verification",
    "unique_pending",
    "pending_personalization",
    "last_updated",
]

# TOTAL counts distinct addresses across every list, so the overlap is counted
# once. `unique_pending` is each list's share of the pending total (an address
# on two lists belongs to the older one), so this column still sums — that is
# what makes the difference between the two pending figures legible.
UNIQUE_COLUMNS = [
    "cleaned_leads",
    "verified_leads",
    "personalized_leads",
    "pending_verification",
]

# Raw rows are not addresses yet (heterogeneous XLSX/CSV sources), and the
# personalization delta is an in-flight count from state. Both stay sums.
SUMMED_COLUMNS = [
    "raw_leads",
    "unique_pending",
    "pending_personalization",
]


def load_state_safely(path: Path, attempts: int = 3, delay: float = 0.4) -> dict:
    """Read state.json, retrying on a partial (mid-write) read.

    run_pipeline.py writes state atomically (tmp + replace), but a JSON decode
    can still fail if the file is swapped between open and read on some
    filesystems, so we retry a couple of times before giving up.
    """
    if not path.is_file():
        return {"version": 1, "lists": {}}
    last_err: Exception | None = None
    for i in range(attempts):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data.setdefault("lists", {})
            return data
        except (json.JSONDecodeError, OSError) as exc:  # partial write / transient
            last_err = exc
            if i < attempts - 1:
                time.sleep(delay)
    print(f"WARNING: could not read {path} cleanly ({last_err}); reporting empty.",
          file=sys.stderr)
    return {"version": 1, "lists": {}}


def read_json_quietly(path: Path) -> dict:
    """Load a JSON object, or {} for anything that goes wrong.

    The report is a monitor: a missing or half-written runtime file should cost
    one number, not the whole report.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def checked_addresses() -> set[str]:
    """Addresses that would no longer cost a Reoon credit.

    The same rule the verifier applies when it decides what to send: a cached
    result, or a tombstone recording a result the cache has since lost. Reading
    them here rather than trusting state's ``pending_verification`` is the
    point — reconcile hard-sets that field to 0 for a list it has marked done,
    so the sheet reported a 0 that had been asserted rather than measured.
    """
    checked = set(read_json_quietly(REOON_CACHE_FILE))
    tombstones = read_json_quietly(REOON_REJECTED_FILE).get("addresses")
    if isinstance(tombstones, dict):
        checked |= set(tombstones)
    return checked


def addresses(path: Path | None) -> set[str] | None:
    """Unique lowercased addresses in a stage CSV; None if it cannot be read.

    None and the empty set mean different things here: an unreadable cleaned
    list is an *unknown* backlog, and reporting it as zero would mark a list
    finished on the strength of a bad file.
    """
    if not path or not path.is_file():
        return None
    try:
        return set(extract_emails_from_csv(path))
    except (SystemExit, OSError, UnicodeDecodeError, csv.Error):
        return None


def csv_data_rows(path: Path) -> int | None:
    """Count data rows (excluding header) in a CSV, handling quoted multi-line
    fields via the csv module. Returns None if the file is missing/unreadable.
    """
    if not path or not path.is_file():
        return None
    try:
        with path.open(newline="", encoding="utf-8-sig") as f:
            return max(0, sum(1 for _ in csv.reader(f)) - 1)
    except OSError:
        return None


def raw_data_rows(path: Path) -> int | None:
    """Count data rows of a raw source (CSV or XLSX). Missing -> None."""
    if not path or not path.is_file():
        return None
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        try:
            import pandas as pd  # available in .venv

            df = pd.read_excel(path)
            return int(len(df))
        except Exception:  # noqa: BLE001 — never let a bad raw file break the report
            return None
    return csv_data_rows(path)


def resolve(entry_rel: str | None, fallback: Path) -> Path:
    """Prefer the path recorded in state; fall back to the conventional name."""
    if entry_rel:
        p = ROOT / entry_rel
        if p.is_file():
            return p
    return fallback


def find_raw(entry: dict, workdir: Path) -> Path | None:
    if entry.get("raw_csv"):
        p = ROOT / entry["raw_csv"]
        if p.is_file():
            return p
    for cand in sorted(workdir.glob("raw.*")):
        if cand.is_file():
            return cand
    return None


def newest_stage_mtime(paths: list[Path]) -> str:
    mtimes = [p.stat().st_mtime for p in paths if p and p.is_file()]
    if not mtimes:
        return ""
    return datetime.fromtimestamp(max(mtimes), tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def blank_if_none(value: int | None) -> object:
    return "" if value is None else value


def build_rows(state: dict) -> tuple[list[dict], dict[str, int]]:
    """One row per list, oldest first, plus the unique-address totals.

    Lists are walked oldest-first so an address shared by two of them is
    attributed to the one that has been working on it longer — the same rule
    the contacted index uses, so the two never disagree about who owns a lead.
    """
    lists = state.get("lists", {})
    ordered = sorted(
        lists.keys(),
        key=lambda t: (lists[t].get("drive_mtime") or lists[t].get("discovered_at") or "", t),
    )
    checked = checked_addresses()
    union: dict[str, set[str]] = {col: set() for col in UNIQUE_COLUMNS}
    rows: list[dict] = []
    for title in ordered:
        entry = lists[title]
        slug = entry.get("slug") or ""
        workdir = WORK_ROOT / slug

        raw_path = find_raw(entry, workdir)
        cleaned = resolve(entry.get("cleaned_csv"), workdir / f"{slug}-cleaned.csv")
        verified = resolve(entry.get("verified_csv"), workdir / f"{slug}-verified.csv")
        enriched = resolve(entry.get("enriched_csv"), workdir / f"{slug}-enriched.csv")

        raw_n = raw_data_rows(raw_path) if raw_path else None
        cleaned_n = csv_data_rows(cleaned)
        verified_n = csv_data_rows(verified)
        enriched_n = csv_data_rows(enriched)

        last_updated = entry.get("last_run") or newest_stage_mtime(
            [raw_path, cleaned, verified, enriched]
        )

        cleaned_set = addresses(cleaned)
        pending_set = None if cleaned_set is None else cleaned_set - checked
        if pending_set is None:
            # No readable cleaned list: report the last figure the pipeline
            # recorded rather than inventing a zero.
            pending_n = entry.get("pending_verification")
            unique_n = None
        else:
            pending_n = len(pending_set)
            unique_n = len(pending_set - union["pending_verification"])

        for col, found in (
            ("cleaned_leads", cleaned_set),
            ("verified_leads", addresses(verified)),
            ("personalized_leads", addresses(enriched)),
            ("pending_verification", pending_set),
        ):
            if found:
                union[col] |= found

        rows.append(
            {
                "list_title": title,
                "stage": entry.get("stage", ""),
                "raw_leads": blank_if_none(raw_n),
                "cleaned_leads": cleaned_n if cleaned_n is not None else 0,
                "verified_leads": verified_n if verified_n is not None else 0,
                "personalized_leads": enriched_n if enriched_n is not None else 0,
                "pending_verification": blank_if_none(pending_n),
                "unique_pending": blank_if_none(unique_n),
                "pending_personalization": blank_if_none(entry.get("pending_delta")),
                "last_updated": last_updated,
            }
        )
    return rows, {col: len(found) for col, found in union.items()}


def total_row(rows: list[dict], unique: dict[str, int]) -> dict:
    """The TOTAL row: distinct addresses where the columns describe people.

    Summing them instead is how the sheet came to claim 17,243 addresses left
    to verify when only 15,634 exist.
    """
    total = {c: "" for c in COLUMNS}
    total["list_title"] = "TOTAL"
    for col in SUMMED_COLUMNS:
        total[col] = sum(int(r[col]) for r in rows if isinstance(r[col], int))
    for col in UNIQUE_COLUMNS:
        total[col] = unique.get(col, 0)
    return total


def write_report(rows: list[dict]) -> None:
    tmp = REPORT_FILE.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(REPORT_FILE)


def print_table(rows: list[dict]) -> None:
    widths = {c: len(c) for c in COLUMNS}
    for row in rows:
        for c in COLUMNS:
            widths[c] = max(widths[c], len(str(row[c])))
    header = "  ".join(c.ljust(widths[c]) for c in COLUMNS)
    print(header)
    print("  ".join("-" * widths[c] for c in COLUMNS))
    for row in rows:
        print("  ".join(str(row[c]).ljust(widths[c]) for c in COLUMNS))


def upload_to_drive(rows: list[dict], remote: str, dry_run: bool = False) -> None:
    """Update the ``Enrichment-Reports`` Google Sheet in place from ``rows``.

    Non-fatal. Writes only the pipeline's own columns (A..J) via the Sheets
    API, matching rows by ``list_title`` and inserting new lists above TOTAL,
    so hand-maintained columns further right survive the update. On any failure
    the sheet is left exactly as it was — there is no CSV-import fallback,
    because that is what used to overwrite those columns.
    """
    try:
        print(sheets_sync.sync(rows, COLUMNS, DRIVE_SHEET_NAME, remote, dry_run))
    except sheets_sync.SheetsSyncError as exc:
        print(f"WARNING: {DRIVE_SHEET_NAME} sheet not updated: {exc}", file=sys.stderr)
        print("         The sheet was left untouched.", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Lead pipeline progress report")
    parser.add_argument(
        "--upload",
        action="store_true",
        help=f"Also update the '{DRIVE_SHEET_NAME}' Google Sheet in place",
    )
    parser.add_argument(
        "--remote",
        default="gdrive",
        help="rclone remote whose stored Drive credentials to reuse (default: gdrive)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With --upload, print the planned sheet writes without applying them",
    )
    args = parser.parse_args()

    state = load_state_safely(STATE_FILE)
    rows, unique = build_rows(state)
    all_rows = rows + [total_row(rows, unique)]
    write_report(all_rows)
    print(f"Lead pipeline progress report — {len(rows)} list(s)")
    print(f"Read state: {STATE_FILE.relative_to(ROOT)} (read-only)")
    print(f"Wrote:      {REPORT_FILE.relative_to(ROOT)}\n")
    print_table(all_rows)
    print(
        "\nTOTAL counts distinct addresses, not a column sum — the lists overlap.\n"
        "unique_pending is each list's own share of that pending total, so that\n"
        "column does sum to it; the address goes to the older of the two lists."
    )
    if args.upload:
        print()
        upload_to_drive(all_rows, args.remote, args.dry_run)


if __name__ == "__main__":
    main()
