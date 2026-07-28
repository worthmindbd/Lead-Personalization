#!/usr/bin/env python3
"""Read-only progress report for the Drive lead pipeline.

Reads .pipeline/state.json (written by run_pipeline.py) plus the per-list stage
CSVs under leads/pipeline/<slug>/ and writes Report.csv at the project root:
one row per list, plus a TOTAL row.

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
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE_FILE = ROOT / ".pipeline" / "state.json"
WORK_ROOT = ROOT / "leads" / "pipeline"
REPORT_FILE = ROOT / "Report.csv"
# Title of the native Google Sheet the report is imported to in the Drive root.
DRIVE_SHEET_NAME = "Enrichment-Reports"

COLUMNS = [
    "list_title",
    "stage",
    "raw_leads",
    "cleaned_leads",
    "verified_leads",
    "personalized_leads",
    "pending_verification",
    "pending_personalization",
    "verify_complete",
    "last_updated",
]

# Columns summed in the TOTAL row.
NUMERIC_COLUMNS = [
    "raw_leads",
    "cleaned_leads",
    "verified_leads",
    "personalized_leads",
    "pending_verification",
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


def build_rows(state: dict) -> list[dict]:
    lists = state.get("lists", {})
    ordered = sorted(
        lists.keys(),
        key=lambda t: (lists[t].get("drive_mtime") or lists[t].get("discovered_at") or "", t),
    )
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

        rows.append(
            {
                "list_title": title,
                "stage": entry.get("stage", ""),
                "raw_leads": blank_if_none(raw_n),
                "cleaned_leads": cleaned_n if cleaned_n is not None else 0,
                "verified_leads": verified_n if verified_n is not None else 0,
                "personalized_leads": enriched_n if enriched_n is not None else 0,
                "pending_verification": blank_if_none(entry.get("pending_verification")),
                "pending_personalization": blank_if_none(entry.get("pending_delta")),
                "verify_complete": entry.get("verify_complete", ""),
                "last_updated": last_updated,
            }
        )
    return rows


def total_row(rows: list[dict]) -> dict:
    total = {c: "" for c in COLUMNS}
    total["list_title"] = "TOTAL"
    for col in NUMERIC_COLUMNS:
        total[col] = sum(int(r[col]) for r in rows if isinstance(r[col], int))
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


def resolve_rclone() -> str:
    """Locate the rclone binary the same way run_pipeline.py reaches it.

    Prefers $RCLONE_BIN, then ~/.local/bin/rclone, then PATH.
    """
    candidates = [
        os.environ.get("RCLONE_BIN"),
        str(Path.home() / ".local" / "bin" / "rclone"),
        "rclone",
    ]
    for cand in candidates:
        if not cand:
            continue
        if os.sep in cand:
            if Path(cand).is_file():
                return cand
        else:
            found = shutil.which(cand)
            if found:
                return found
    return "rclone"


def upload_to_drive(remote: str) -> None:
    """Import the report as the native Google Sheet ``remote:Enrichment-Reports``.

    Non-fatal. Stages a copy named ``Enrichment-Reports.csv`` so rclone's Drive
    import titles the sheet accordingly (``copy`` keeps the basename, import
    strips the ``.csv``). Matching import/export formats make repeat runs update
    the SAME sheet in place (stable ID, exactly one sheet) rather than creating
    duplicates. The local Report.csv is left untouched.
    """
    staged = REPORT_FILE.with_name(f"{DRIVE_SHEET_NAME}.csv")
    cmd = [
        resolve_rclone(), "copy", str(staged), f"{remote}:",
        "--drive-import-formats", "csv", "--drive-export-formats", "csv",
    ]
    try:
        shutil.copyfile(REPORT_FILE, staged)
        subprocess.run(cmd, check=True)
        print(f"Uploaded {REPORT_FILE.name} -> {remote}:{DRIVE_SHEET_NAME} (native Google Sheet)")
    except Exception as exc:  # noqa: BLE001 — report upload must not crash callers
        print(f"WARNING: {DRIVE_SHEET_NAME} sheet upload to Drive failed: {exc}", file=sys.stderr)
    finally:
        staged.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Lead pipeline progress report")
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Also push the generated Report.csv to the Drive root",
    )
    parser.add_argument(
        "--remote", default="gdrive", help="rclone remote name (default: gdrive)"
    )
    args = parser.parse_args()

    state = load_state_safely(STATE_FILE)
    rows = build_rows(state)
    all_rows = rows + [total_row(rows)]
    write_report(all_rows)
    print(f"Lead pipeline progress report — {len(rows)} list(s)")
    print(f"Read state: {STATE_FILE.relative_to(ROOT)} (read-only)")
    print(f"Wrote:      {REPORT_FILE.relative_to(ROOT)}\n")
    print_table(all_rows)
    if args.upload:
        upload_to_drive(args.remote)


if __name__ == "__main__":
    main()
