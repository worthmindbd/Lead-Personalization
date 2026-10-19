#!/usr/bin/env python3
"""Merge rewritten enriched leads across pre-Aug 13 pipeline lists into a single deduplicated campaign CSV."""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.personalization.clean_gmb_leads import is_departmental_email

SOURCE_FILES = [
    ("Aug 13, 2026", ROOT / "leads/pipeline/aug-13-2026/aug-13-2026-enriched.csv"),
    ("July 31, 2026", ROOT / "leads/pipeline/july-31-2026/july-31-2026-enriched.csv"),
    ("July 25, 2026", ROOT / "leads/pipeline/july-25-2026/july-25-2026-enriched.csv"),
    ("July 20, 2026", ROOT / "leads/pipeline/july-20-2026/july-20-2026-enriched.csv"),
    ("July 17, 2026", ROOT / "leads/pipeline/july-17-2026/july-17-2026-enriched.csv"),
    ("July 8, 2026", ROOT / "leads/pipeline/july-8-2026/july-8-2026-enriched.csv"),
    ("July 7, 2026", ROOT / "leads/pipeline/july-7-2026/july-7-2026-enriched.csv"),
    ("July 6, 2026", ROOT / "leads/pipeline/july-6-2026/july-6-2026-enriched.csv"),
]

DEFAULT_OUT = ROOT / "leads/campaign-leads-merged-enriched.csv"


def merge_leads(out_path: Path = DEFAULT_OUT) -> tuple[int, int]:
    all_rows = []
    fieldnames = []
    seen_fields = set()
    seen_emails = set()
    total_raw = 0
    dupes_skipped = 0
    dept_skipped = 0

    print("Merging enriched lists:")
    for label, file_path in SOURCE_FILES:
        if not file_path.is_file():
            print(f"  Warning: {file_path} not found, skipping.")
            continue

        with file_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for f in reader.fieldnames or []:
                if f not in seen_fields:
                    seen_fields.add(f)
                    fieldnames.append(f)

            count_in_file = 0
            for row in reader:
                total_raw += 1
                email = (row.get("primary_email") or row.get("Email") or "").split("|")[0].strip().lower()
                if email:
                    if is_departmental_email(email):
                        dept_skipped += 1
                        continue
                    if email in seen_emails:
                        dupes_skipped += 1
                        continue
                    seen_emails.add(email)
                all_rows.append(row)
                count_in_file += 1

            print(f"  - {label}: {count_in_file} rows loaded (file: {file_path.name})")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(f"{out_path.suffix}.tmp.{os.getpid()}")
    with tmp_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)
    tmp_path.replace(out_path)

    print("\nMerge complete:")
    print(f"  Total raw rows scanned: {total_raw}")
    print(f"  Departmental inboxes removed: {dept_skipped}")
    print(f"  Cross-list duplicates removed: {dupes_skipped}")
    print(f"  Final unique leads in merged file: {len(all_rows)}")
    print(f"  Saved to: {out_path}")

    return len(all_rows), dupes_skipped


def upload_to_drive(local_path: Path):
    dest = f"gdrive:Personalized leads/{local_path.name}"
    print(f"\nUploading merged file to Drive: {dest}")
    cmd = ["rclone", "copyto", str(local_path), dest]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print("  ✓ Uploaded to Drive successfully")
    else:
        print(f"  Warning: Drive upload failed: {res.stderr.strip()}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Path for merged CSV")
    parser.add_argument("--upload", action="store_true", help="Upload merged CSV to Google Drive")
    args = parser.parse_args()

    merge_leads(args.out)
    if args.upload:
        upload_to_drive(args.out)


if __name__ == "__main__":
    main()
