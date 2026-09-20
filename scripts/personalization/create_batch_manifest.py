#!/usr/bin/env python3
"""Create stratified batch manifest for mixed lead personalization."""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from lead_personalization import fsutil  # noqa: E402
from personalization import artifacts  # noqa: E402

DEFAULT_SOURCE = ROOT / "leads" / "all-leads-with-email-normalized.csv"
DEFAULT_MANIFEST = artifacts.manifest_path()
BATCH_SIZE = 50


def create_manifest(
    source: Path = DEFAULT_SOURCE,
    manifest_path: Path = DEFAULT_MANIFEST,
    batch_size: int = BATCH_SIZE,
) -> dict:
    if batch_size <= 0:
        raise ValueError(f"batch_size must be positive, got {batch_size}")
    if not source.is_file():
        raise FileNotFoundError(f"Source file not found: {source}")

    with source.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    if not rows:
        print(f"Warning: Source file {source} contains no data rows.", file=sys.stderr)

    by_segment: dict[str, list[int]] = defaultdict(list)
    for i, row in enumerate(rows):
        by_segment[row.get("aevora_segment", "low_fit")].append(i)

    segment_order = sorted(by_segment.keys(), key=lambda s: (-len(by_segment[s]), s))
    segment_queues = {s: list(indices) for s, indices in by_segment.items()}
    ordered_indices: list[int] = []

    while any(segment_queues.values()):
        for seg in segment_order:
            queue = segment_queues[seg]
            if queue:
                ordered_indices.append(queue.pop(0))

    batches = []
    if ordered_indices:
        for batch_num, start in enumerate(range(0, len(ordered_indices), batch_size), start=1):
            chunk = ordered_indices[start : start + batch_size]
            segments_in_batch = {rows[i].get("aevora_segment", "low_fit") for i in chunk}
            batches.append(
                {
                    "id": f"{batch_num:03d}",
                    "rows": chunk,
                    "row_start": chunk[0],
                    "row_end": chunk[-1],
                    "count": len(chunk),
                    "segments": sorted(segments_in_batch),
                    "status": "pending",
                }
            )

    # Recorded, not just implied by the filename: every downstream artifact
    # name is built from it, and a manifest that has been moved or renamed
    # should still name its own files.
    try:
        source_rel = str(source.resolve().relative_to(ROOT.resolve()))
    except (OSError, ValueError):
        source_rel = str(source)
    manifest = {
        "prefix": artifacts.prefix_from_manifest_name(manifest_path),
        "source": source_rel,
        "batch_size": batch_size,
        "total_leads": len(rows),
        "total_batches": len(batches),
        "batches": batches,
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fsutil.atomic_write_json(manifest_path, manifest)

    print(f"Manifest: {len(batches)} batches, {len(rows)} leads -> {manifest_path}")
    return manifest


def _resolve(raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


def main() -> None:
    """Usage: create_batch_manifest.py [source.csv] [manifest.json]

    The manifest path is worth passing: its filename becomes the prefix on
    every artifact the run writes, so two lists processed side by side need one
    manifest each. Omitted, it is the shared ``mix-leads`` manifest.
    """
    source = _resolve(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    manifest_path = _resolve(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_MANIFEST
    create_manifest(source, manifest_path)


if __name__ == "__main__":
    main()
