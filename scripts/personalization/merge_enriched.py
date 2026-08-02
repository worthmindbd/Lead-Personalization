#!/usr/bin/env python3
"""Merge per-batch enriched CSVs into one master file."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from personalization import artifacts  # noqa: E402
from personalization.manifest_lock import manifest_lock  # noqa: E402

ENRICHED_DIR = ROOT / "leads" / "enriched"
DEFAULT_OUT = ROOT / "leads" / "all-leads-with-email-enriched.csv"
MANIFEST = artifacts.manifest_path()


def merge_enriched(
    enriched_dir: Path = ENRICHED_DIR,
    output_path: Path = DEFAULT_OUT,
    manifest_path: Path = MANIFEST,
    prefix: str | None = None,
) -> int:
    # Scoped to this run's prefix. The glob used to be a flat
    # mix-leads-batch-*, which is how another list's leftovers in
    # leads/enriched/ could be folded into this list's merged output — and why
    # the pipeline had to sweep the directory before every run.
    pattern = artifacts.enriched_glob(prefix or artifacts.prefix_for(manifest_path))
    files = sorted(enriched_dir.glob(pattern))
    if not files:
        raise SystemExit(f"No enriched batch files matching {pattern} in {enriched_dir}")

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
        # Under the same lock update_batch_status takes: a worker flipping a
        # batch to "done" between this read and this write would have its status
        # erased, and the batch would be re-run. Safe today only because
        # auto_merge is switched off whenever workers > 1 — which is a caller's
        # promise, not a property of this function.
        with manifest_lock(manifest_path):
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["merged_output"] = str(output_path.relative_to(ROOT))
            manifest["merged_row_count"] = len(all_rows)
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return len(all_rows)


def main() -> None:
    merge_enriched()


if __name__ == "__main__":
    main()
