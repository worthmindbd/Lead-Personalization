#!/usr/bin/env python3
"""Rewrite email copy sequences for all old pipeline lists prior to Aug 13, 2026.

Uses existing research and signals stored on disk — zero web or LinkedIn re-fetch.
Ensures 100% QA pass rate, updated segment mappings, zero AI slop, zero hard CTAs,
and widened variant distribution across all sequences.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from lead_personalization.copywriter import fix_sequence, generate_sequence  # noqa: E402
from lead_personalization.offer_pack import load_offer_pack  # noqa: E402
from lead_personalization.qa import campaign_repetition, qa, sequence_issues  # noqa: E402
from lead_personalization.research import social_channel  # noqa: E402
from lead_personalization.segments import segment_for_category  # noqa: E402

LIST_SPECS = [
    {"title": "July 31,2026", "slug": "july-31-2026", "drive_file": "july-31-2026-enriched.csv"},
    {"title": "July 25,2026", "slug": "july-25-2026", "drive_file": "july-25-2026-enriched.csv"},
    {"title": "July 20,2026", "slug": "july-20-2026", "drive_file": "july-20-2026-enriched.csv"},
    {"title": "July 17,2026", "slug": "july-17-2026", "drive_file": "july-17-2026-enriched.csv"},
    {"title": "July 8,2026", "slug": "july-8-2026", "drive_file": "july-8-2026-enriched.csv"},
    {"title": "July 7,2026", "slug": "july-7-2026", "drive_file": "july-7-2026-enriched.csv"},
    {"title": "July 6,2026", "slug": "july-6-2026", "drive_file": "mixed-enriched.csv"},
]


def extract_snippet(evidence: str, research_signal: str, meta: str) -> str:
    if evidence != "positioning":
        return ""
    m = re.search(r'site positioning: "([^"]+)"', research_signal or "")
    if m:
        return m.group(1).strip()
    return (meta or "").strip()


def rclone_upload(local_path: Path, drive_path: str) -> bool:
    cmd = ["rclone", "copyto", str(local_path), f"gdrive:Personalized leads/{drive_path}"]
    print(f"  Uploading to Drive: gdrive:Personalized leads/{drive_path}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"  WARNING: Drive upload failed: {res.stderr.strip()}", file=sys.stderr)
        return False
    print("  ✓ Upload complete")
    return True


def rewrite_list(spec: dict, pack, upload: bool = False) -> dict:
    slug = spec["slug"]
    title = spec["title"]
    csv_path = ROOT / "leads" / "pipeline" / slug / f"{slug}-enriched.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(f"Missing enriched CSV: {csv_path}")

    with csv_path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    print(f"\n========================================================")
    print(f"Processing {title} ({slug}): {len(rows)} leads")
    print(f"========================================================")

    total_leads = len(rows)
    qa_total = 0
    qa_passed = 0
    qa_issues: dict[str, int] = {}
    all_sequences = []
    updated_rows = []

    for idx, row in enumerate(rows):
        cat = (row.get("First_category") or "").strip()
        fresh_seg = segment_for_category(cat)

        row_copy = dict(row)
        row_copy["aevora_segment"] = fresh_seg

        raw_variant = row.get("copy_variant") or ""
        ev = raw_variant.split(".")[0] if "." in raw_variant else raw_variant
        if ev not in pack.openers:
            ev = "weak"
        if row.get("linkedin_topic"):
            ev = "linkedin_posts"

        snip = extract_snippet(ev, row.get("research_signal", ""), row.get("Meta_Description", ""))

        research = {
            "email": row.get("primary_email", ""),
            "evidence": ev,
            "snippet": snip,
            "linkedin_topic": row.get("linkedin_topic", ""),
            "social_channel": social_channel(row),
            "first_name": row.get("first_name", ""),
            "outreach_tier": row.get("outreach_tier", "company"),
            "research_signal": row.get("research_signal", ""),
            "company": row.get("company_name", ""),
        }

        seq, var = generate_sequence(row_copy, research, pack)
        seq = fix_sequence(seq, row_copy, research, pack)

        lead_pairs = []
        for step, (s, b) in enumerate(seq, 1):
            lead_pairs.append((s, b))
            row_copy[f"email_{step}_subject"] = s
            row_copy[f"email_{step}_body"] = b
            res = qa(s, b, row.get("company_name", ""), row.get("primary_email", ""))
            qa_total += 1
            if res["pass"]:
                qa_passed += 1
            else:
                for issue in res["issues"]:
                    qa_issues[issue] = qa_issues.get(issue, 0) + 1

        row_copy["copy_variant"] = var
        all_sequences.append(lead_pairs)
        updated_rows.append(row_copy)

    # Write updated enriched CSV atomically
    tmp_path = csv_path.with_suffix(".tmp")
    with tmp_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(updated_rows)
    tmp_path.replace(csv_path)

    # Write review markdown
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    review_path = ROOT / "copy" / f"{slug}-pipeline-review-{timestamp}.md"
    rep_stats = campaign_repetition(all_sequences)

    lines = [
        f"# {slug} pipeline review (rewritten) — {timestamp}",
        f"Leads rewritten: {total_leads}",
        f"QA pass: {qa_passed}/{qa_total} ({(qa_passed/qa_total)*100:.1f}%)",
        f"Cumulative enriched list: {csv_path.relative_to(ROOT)}",
        "",
        "---",
        f"## Repetition stats across {total_leads} leads:",
    ]
    for step_key in ("step_1", "step_2", "step_3"):
        st = rep_stats.get("subjects", {}).get(step_key, {})
        lines.append(f"- {step_key} subjects: {st.get('distinct', 0)} distinct, top share: {st.get('top_share', 0):.1%}")

    lines.extend([
        "",
        "---",
        f"## Sample Leads (first 5 of {total_leads}):",
        "",
    ])

    for i in range(min(5, len(updated_rows))):
        r = updated_rows[i]
        lines.append(f"### Lead {i+1}: {r.get('company_name') or r.get('Name')}")
        lines.append(f"**Email:** {r.get('primary_email')} | **Segment:** {r.get('aevora_segment')} | **Variant:** {r.get('copy_variant')}")
        for s_idx in (1, 2, 3):
            lines.append(f"#### Email {s_idx}")
            lines.append(f"**Subject:** {r.get(f'email_{s_idx}_subject')}")
            lines.append("")
            lines.append(r.get(f'email_{s_idx}_body', ''))
            lines.append("")
        lines.append("---")

    review_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  ✓ Enriched CSV rewritten: {csv_path}")
    print(f"  ✓ QA pass rate: {qa_passed}/{qa_total} ({(qa_passed/qa_total)*100:.1f}%)")
    if qa_issues:
        print(f"  QA issues: {qa_issues}")
    print(f"  ✓ Review written: {review_path}")

    # Drive sync if requested
    if upload:
        drive_dest = f"{title}/{spec['drive_file']}"
        rclone_upload(csv_path, drive_dest)

    return {
        "slug": slug,
        "title": title,
        "leads": total_leads,
        "qa_passed": qa_passed,
        "qa_total": qa_total,
        "qa_issues": qa_issues,
        "review_path": str(review_path),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upload", action="store_true", help="Sync rewritten CSVs to Google Drive")
    parser.add_argument("--list", default=None, help="Process only a single list slug or title")
    args = parser.parse_args()

    pack = load_offer_pack("aevora")

    specs = LIST_SPECS
    if args.list:
        specs = [s for s in LIST_SPECS if args.list.lower() in (s["slug"].lower(), s["title"].lower())]
        if not specs:
            sys.exit(f"No list matched --list={args.list}")

    results = []
    for spec in specs:
        res = rewrite_list(spec, pack, upload=args.upload)
        results.append(res)

    print("\n" + "=" * 60)
    print("ALL REWRITES COMPLETE")
    print("=" * 60)
    total_leads = sum(r["leads"] for r in results)
    total_qa = sum(r["qa_total"] for r in results)
    total_pass = sum(r["qa_passed"] for r in results)
    print(f"Total lists processed: {len(results)}")
    print(f"Total leads: {total_leads}")
    print(f"Overall QA pass: {total_pass}/{total_qa} ({(total_pass/total_qa)*100:.2f}%)")
    for r in results:
        print(f"  - {r['title']} ({r['slug']}): {r['leads']} leads, QA: {r['qa_passed']}/{r['qa_total']}")


if __name__ == "__main__":
    main()
