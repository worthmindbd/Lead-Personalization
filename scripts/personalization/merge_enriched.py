#!/usr/bin/env python3
"""Merge per-batch enriched CSVs into one master file."""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from lead_personalization import fsutil  # noqa: E402
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
    fieldnames: list[str] = []
    seen_fields: set[str] = set()
    seen_emails = set()

    for path in files:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            # Union across files like build_enriched does: batches can carry
            # different email_N_* columns, and first-file-only fieldnames plus
            # extrasaction="ignore" used to drop the later ones silently.
            for name in reader.fieldnames or []:
                if name not in seen_fields:
                    seen_fields.add(name)
                    fieldnames.append(name)
            for row in reader:
                email = (row.get("primary_email") or row.get("Email") or "").split("|")[0].strip().lower()
                # A row with no address has nothing to dedupe on: every one of
                # them got copy (the batch never drops a row), and the "" key
                # used to collapse all of them into whichever came first.
                if email:
                    if email in seen_emails:
                        continue
                    seen_emails.add(email)
                all_rows.append(row)

    if not fieldnames:
        fieldnames = ["primary_email"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_output = output_path.with_suffix(f"{output_path.suffix}.tmp.{os.getpid()}")
    try:
        with tmp_output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(all_rows)
        os.replace(tmp_output, output_path)
    except Exception:
        if tmp_output.exists():
            try:
                tmp_output.unlink()
            except OSError:
                pass
        raise

    print(f"Merged {len(files)} batch files -> {len(all_rows)} rows")
    print(f"Output: {output_path}")

    if manifest_path.exists():
        with manifest_lock(manifest_path):
            manifest = fsutil.load_json(manifest_path, None)
            if isinstance(manifest, dict):
                try:
                    rel_out = str(output_path.resolve().relative_to(ROOT.resolve()))
                except (ValueError, OSError):
                    rel_out = str(output_path)
                manifest["merged_output"] = rel_out
                manifest["merged_row_count"] = len(all_rows)
                fsutil.atomic_write_json(manifest_path, manifest)

    return len(all_rows)


def main() -> None:
    merge_enriched()


if __name__ == "__main__":
    main()
