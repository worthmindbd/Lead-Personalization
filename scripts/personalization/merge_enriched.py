#!/usr/bin/env python3
"""Merge per-batch enriched CSVs into one master file."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENRICHED_DIR = ROOT / "leads" / "enriched"
DEFAULT_OUT = ROOT / "leads" / "all-leads-with-email-enriched.csv"
MANIFEST = ROOT / "campaigns" / "mix-leads-batch-manifest.json"


def merge_enriched(
    enriched_dir: Path = ENRICHED_DIR,
    output_path: Path = DEFAULT_OUT,
    manifest_path: Path = MANIFEST,
) -> int:
    files = sorted(enriched_dir.glob("mix-leads-batch-*-enriched.csv"))
    if not files:
        raise SystemExit(f"No enriched batch files in {enriched_dir}")

    all_rows = []
    fieldnames = None
    seen_emails = set()

    for path in files:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if fieldnames is None:
                fieldnames = list(reader.fieldnames or [])
            for row in reader:
                email = (row.get("primary_email") or row.get("Email") or "").split("|")[0].strip().lower()
                if email in seen_emails:
                    continue
                seen_emails.add(email)
                all_rows.append(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Merged {len(files)} batch files -> {len(all_rows)} rows")
    print(f"Output: {output_path}")

    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["merged_output"] = str(output_path.relative_to(ROOT))
        manifest["merged_row_count"] = len(all_rows)
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return len(all_rows)


def main() -> None:
    merge_enriched()


if __name__ == "__main__":
    main()
