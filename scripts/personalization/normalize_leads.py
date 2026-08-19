#!/usr/bin/env python3
"""Normalize a mixed lead CSV into the research-ready schema, on disk.

The row-level normalization is ``lead_personalization.pipeline`` — this file is
the CSV/JSON wrapper around it: where the output goes, what the header row looks
like, and the CLI. It used to carry its own copy of the row logic; four of the
six shared functions were already byte-identical and the other two differed only
in formatting.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from lead_personalization.naming import campaign_stem  # noqa: E402
from lead_personalization.pipeline import (  # noqa: E402,F401
    DERIVED_FIELDS,
    domain_company,
    normalized_fieldnames,
    normalize_row,
    parse_name_field,
    pick_primary_email,
    research_urls,
    split_emails,
)
from lead_personalization.segments import (  # noqa: E402,F401
    BUSINESS_NAME_MARKERS,
    CATEGORY_TO_SEGMENT,
    GENERIC_EMAIL_PREFIXES,
    resolve_outreach_tier as outreach_tier,
    segment_for_category,
)

DEFAULT_SOURCE = ROOT / "leads" / "all-leads-with-email.csv"
DEFAULT_CSV_OUT = ROOT / "leads" / "all-leads-with-email-normalized.csv"
DEFAULT_JSON_OUT = ROOT / "campaigns" / "mix-leads-normalized.json"


def count_named_path(stem: str, count: int, label: str, directory: Path) -> Path:
    return directory / f"{stem}-{count}-{label}.csv"


def normalized_output_path(source: Path, row_count: int) -> Path:
    base = campaign_stem(source.stem)
    return count_named_path(base, row_count, "normalized", source.parent)


def normalize_leads(
    source: Path = DEFAULT_SOURCE,
    csv_out: Path | None = None,
    json_out: Path | None = None,
) -> list[dict]:
    with source.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    # Spelled once, in the module that derives them — a column added there but
    # missing here would be computed and then silently dropped by the writer's
    # extrasaction="ignore".
    out_fieldnames = normalized_fieldnames(fieldnames)
    normalized = [normalize_row(i, row) for i, row in enumerate(rows)]

    # An explicitly-passed csv_out is honored. When the caller left it to us:
    # the default source keeps its stable default output; any other source gets
    # the count-named path next to itself.
    if csv_out is None:
        csv_out = (
            DEFAULT_CSV_OUT if source == DEFAULT_SOURCE
            else normalized_output_path(source, len(normalized))
        )
    json_out = json_out or DEFAULT_JSON_OUT

    csv_out.parent.mkdir(parents=True, exist_ok=True)
    with csv_out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=out_fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(normalized)

    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(normalized, indent=2), encoding="utf-8")

    tiers = {}
    segments = {}
    for r in normalized:
        tiers[r["outreach_tier"]] = tiers.get(r["outreach_tier"], 0) + 1
        segments[r["aevora_segment"]] = segments.get(r["aevora_segment"], 0) + 1

    print(f"Normalized {len(normalized)} leads -> {csv_out}")
    print(f"Sidecar JSON -> {json_out}")
    print(f"Outreach tiers: {tiers}")
    print(f"Segments: {segments}")

    unmapped = sorted(
        {
            (r.get("First_category") or "").strip()
            for r in rows
            if (r.get("First_category") or "").strip()
            and (r.get("First_category") or "").strip() not in CATEGORY_TO_SEGMENT
        }
    )
    if unmapped:
        preview = ", ".join(unmapped[:40])
        more = f" (+{len(unmapped) - 40} more)" if len(unmapped) > 40 else ""
        print(
            f"Unmapped categories -> low_fit ({len(unmapped)}): {preview}{more}\n"
            "  Add them to lead_personalization/segments.py CATEGORY_TO_SEGMENT "
            "to improve targeting."
        )
    return normalized


def main() -> None:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    if not source.is_absolute():
        source = ROOT / source
    normalize_leads(source)


if __name__ == "__main__":
    main()
