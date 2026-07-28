#!/usr/bin/env python3
"""Split a mixed lead CSV into per-category files under leads/, email rows only."""

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEADS_DIR = ROOT / "leads"
MERGED_OUTPUT = LEADS_DIR / "all-leads-with-email.csv"
CATEGORY_FIELD = "First_category"
EMAIL_FIELD = "Email"
UNCATEGORIZED = "uncategorized"


def slugify(text: str) -> str:
    slug = text.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-") or UNCATEGORIZED


def has_email(row: dict) -> bool:
    return bool((row.get(EMAIL_FIELD) or "").strip())


def category_key(row: dict) -> str:
    value = (row.get(CATEGORY_FIELD) or "").strip()
    return value if value else UNCATEGORIZED


def unique_slug(slug: str, used: set[str]) -> str:
    if slug not in used:
        used.add(slug)
        return slug
    index = 2
    while True:
        candidate = f"{slug}-{index}"
        if candidate not in used:
            used.add(candidate)
            print(f"Warning: slug collision for '{slug}', using '{candidate}'")
            return candidate
        index += 1


def write_group(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_manifest(path: Path, entries: list[tuple[str, str, int]]) -> None:
    lines = [
        "# Lead split manifest",
        "",
        f"Total output rows: {sum(count for _, _, count in entries)}",
        f"Output files: {len(entries)}",
        "",
        "| File | Category | Rows |",
        "| --- | --- | ---: |",
    ]
    for filename, category, count in sorted(entries, key=lambda item: (-item[2], item[0])):
        safe_category = category.replace("|", "\\|")
        lines.append(f"| `{filename}` | {safe_category} | {count} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def split_leads(source: Path, output_dir: Path = LEADS_DIR) -> list[tuple[str, str, int]]:
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        if not fieldnames:
            raise ValueError(f"No header row found in {source}")

        groups: dict[str, list[dict]] = defaultdict(list)
        total_rows = 0
        kept_rows = 0

        for row in reader:
            total_rows += 1
            if not has_email(row):
                continue
            kept_rows += 1
            groups[category_key(row)].append(row)

    output_dir.mkdir(parents=True, exist_ok=True)
    used_slugs: set[str] = set()
    manifest_entries: list[tuple[str, str, int]] = []

    for category in sorted(groups, key=lambda value: value.lower()):
        rows = groups[category]
        slug = unique_slug(slugify(category), used_slugs)
        filename = f"{slug}.csv"
        write_group(output_dir / filename, fieldnames, rows)
        manifest_entries.append((filename, category, len(rows)))

    manifest_path = output_dir / "split-manifest.md"
    write_manifest(manifest_path, manifest_entries)

    print(f"Source: {source}")
    print(f"Total rows read: {total_rows}")
    print(f"Rows with email kept: {kept_rows}")
    print(f"Categories written: {len(manifest_entries)}")
    print(f"Output directory: {output_dir}")
    print(f"Manifest: {manifest_path}")
    print("")
    print(f"{'Rows':>6}  {'File':<40}  Category")
    print(f"{'-' * 6}  {'-' * 40}  {'-' * 30}")
    for filename, category, count in sorted(manifest_entries, key=lambda item: (-item[2], item[0])):
        print(f"{count:6d}  {filename:<40}  {category}")

    return manifest_entries


def merge_leads(
    input_dir: Path = LEADS_DIR,
    output_path: Path = MERGED_OUTPUT,
) -> int:
    source_files = sorted(
        path
        for path in input_dir.glob("*.csv")
        if path.resolve() != output_path.resolve()
    )
    if not source_files:
        raise ValueError(f"No CSV files found in {input_dir}")

    merged_rows: list[dict] = []
    fieldnames: list[str] | None = None
    skipped_no_email = 0

    for source_file in source_files:
        with source_file.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                continue
            if fieldnames is None:
                fieldnames = list(reader.fieldnames)
            for row in reader:
                if not has_email(row):
                    skipped_no_email += 1
                    continue
                merged_rows.append(row)

    if not fieldnames:
        raise ValueError("No header row found in category CSV files")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_group(output_path, fieldnames, merged_rows)

    print(f"Merged file: {output_path}")
    print(f"Source files: {len(source_files)}")
    print(f"Rows written: {len(merged_rows)}")
    if skipped_no_email:
        print(f"Rows skipped (no email): {skipped_no_email}")

    return len(merged_rows)


def main() -> None:
    args = sys.argv[1:]
    merge_only = "--merge" in args or "--merge-only" in args
    if merge_only:
        args = [arg for arg in args if arg not in {"--merge", "--merge-only"}]

    if merge_only:
        merge_leads()
        return

    source = Path(args[0]) if args else ROOT / "Mix-Leads-13K.csv"
    if not source.is_absolute():
        source = ROOT / source
    if not source.exists():
        raise SystemExit(f"Source file not found: {source}")

    split_leads(source)
    merge_leads()


if __name__ == "__main__":
    main()
