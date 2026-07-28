#!/usr/bin/env python3
"""Create stratified batch manifest for mixed lead personalization."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "leads" / "all-leads-with-email-normalized.csv"
DEFAULT_MANIFEST = ROOT / "campaigns" / "mix-leads-batch-manifest.json"
BATCH_SIZE = 50


def create_manifest(
    source: Path = DEFAULT_SOURCE,
    manifest_path: Path = DEFAULT_MANIFEST,
    batch_size: int = BATCH_SIZE,
) -> dict:
    with source.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

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

    manifest = {
        "source": str(source.relative_to(ROOT)),
        "batch_size": batch_size,
        "total_leads": len(rows),
        "total_batches": len(batches),
        "batches": batches,
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Manifest: {len(batches)} batches, {len(rows)} leads -> {manifest_path}")
    return manifest


def main() -> None:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    if not source.is_absolute():
        source = ROOT / source
    create_manifest(source)


if __name__ == "__main__":
    main()
