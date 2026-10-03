#!/usr/bin/env python3
"""CLI utility to manage, validate, and inject Ghost Ink for Listmonk and cold email outreach.

Implements Jay's Ghost Ink Framework (https://leadgenjay.com/value/ghost-ink/success):
- Injects or updates the single <div data-gi="1"> block in HTML templates.
- Enriches CSV lead lists with deterministic ghost_ink_1, ghost_ink_2, ghost_ink_3 columns.
- Audits and verifies HTML files against the 4 Golden Rules.

Usage:
  # Check an HTML file against the 4 rules:
  python3 scripts/personalization/inject_ghost_ink.py --check templates/listmonk/sequence_1_template.html

  # Inject / update ghost ink in an HTML template:
  python3 scripts/personalization/inject_ghost_ink.py --html my_email.html --out my_email_gi.html

  # Enrich a CSV lead list with deterministic ghost_ink columns:
  python3 scripts/personalization/inject_ghost_ink.py --csv leads/my-list.csv --out leads/my-list-gi.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lead_personalization.ghost_ink import (  # noqa: E402
    GHOST_INK_PASSAGES,
    GHOST_INK_RE,
    GHOST_INK_STYLE,
    has_ghost_ink,
    inject_ghost_ink,
    pick_ghost_ink,
)


def audit_html(html_path: Path) -> bool:
    """Verify an HTML file against the 4 Golden Rules."""
    print(f"Auditing Ghost Ink in: {html_path}")
    text = html_path.read_text(encoding="utf-8")

    matches = list(GHOST_INK_RE.finditer(text))
    if not matches:
        print("  ❌ [Rule 2 Failure]: No Ghost Ink block (<div data-gi=\"1\"...>) found.")
        return False

    if len(matches) > 1:
        print(f"  ❌ [Rule 2 Failure]: Multiple Ghost Ink blocks found ({len(matches)}). Only 1 block allowed!")
        return False
    print("  ✅ [Rule 2 Pass]: Exactly 1 Ghost Ink block found.")

    block_html = matches[0].group(0)

    # Check required style declarations
    required_styles = [
        "color:transparent",
        "font-size:0px",
        "line-height:0px",
        "max-height:0px",
        "mso-hide:all",
        "overflow:hidden",
        "display:none",
        "opacity:0",
    ]
    missing = [s for s in required_styles if s not in block_html]
    if missing:
        print(f"  ❌ [Rule 1 Failure]: Missing required CSS declarations: {', '.join(missing)}")
        return False
    print("  ✅ [Rule 1 Pass]: All 8 client-surviving CSS declarations are present.")

    # Check if template expression or literal passage
    inner = re.sub(r"<[^>]+>", "", block_html).strip()
    if "{{" in block_html:
        print("  ✅ [Listmonk Dynamic]: Uses Go template expressions (supports dynamic attribute / Sprig rotation).")
    else:
        words = len(inner.split())
        print(f"  ℹ️ [Static Passage]: {words} words.")
        if words < 200:
            print(f"  ⚠️ Warning: Passage word count ({words}) is shorter than recommended ~300 words.")

    print("  ✅ Ghost Ink check passed successfully!\n")
    return True


def enrich_csv_leads(input_csv: Path, output_csv: Path) -> None:
    """Add deterministic ghost_ink_1, ghost_ink_2, ghost_ink_3 columns to a CSV."""
    with input_csv.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    new_fields = ["ghost_ink_1", "ghost_ink_2", "ghost_ink_3", "ghost_ink"]
    for field in new_fields:
        if field not in fieldnames:
            fieldnames.append(field)

    for row in rows:
        email = (row.get("primary_email") or row.get("Email") or row.get("email") or "").split("|")[0].strip().lower()
        gi_1 = pick_ghost_ink(email, step=1)["text"]
        gi_2 = pick_ghost_ink(email, step=2)["text"]
        gi_3 = pick_ghost_ink(email, step=3)["text"]
        row["ghost_ink_1"] = gi_1
        row["ghost_ink_2"] = gi_2
        row["ghost_ink_3"] = gi_3
        row["ghost_ink"] = gi_1

    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Successfully enriched {len(rows)} leads with Ghost Ink columns -> {output_csv}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ghost Ink CLI utility")
    parser.add_argument("--check", type=Path, help="Check an HTML file for Ghost Ink compliance")
    parser.add_argument("--html", type=Path, help="Input HTML file to inject with Ghost Ink")
    parser.add_argument("--out", type=Path, help="Output file path for injected HTML or CSV")
    parser.add_argument("--csv", type=Path, help="Input CSV file to enrich with ghost_ink columns")
    parser.add_argument("--passage", type=str, default="", help="Specific passage text or ID (optional)")

    args = parser.parse_args()

    if args.check:
        passed = audit_html(args.check)
        sys.exit(0 if passed else 1)

    if args.html:
        passage = args.passage or GHOST_INK_PASSAGES[0]["text"]
        content = args.html.read_text(encoding="utf-8")
        updated = inject_ghost_ink(content, passage)
        out_path = args.out or args.html
        out_path.write_text(updated, encoding="utf-8")
        print(f"Injected Ghost Ink into {out_path}")
        sys.exit(0)

    if args.csv:
        out_path = args.out or args.csv.with_name(f"{args.csv.stem}-ghost-ink.csv")
        enrich_csv_leads(args.csv, out_path)
        sys.exit(0)

    parser.print_help()


if __name__ == "__main__":
    main()
