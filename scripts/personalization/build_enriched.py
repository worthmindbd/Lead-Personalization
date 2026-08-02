#!/usr/bin/env python3
"""Build enriched CSV, JSON, and markdown review from research + copy JSON."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from lead_personalization.qa import qa, sequence_issues  # noqa: E402
from personalization import artifacts  # noqa: E402

DELAYS = [0, 3, 7]

# Internal-only columns that should not appear in the enriched export.
DROP_COLUMNS = {"row_index", "fit_score"}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_batch(
    source: Path,
    research_path: Path,
    copy_path: Path,
    batch_id: str,
    enriched_dir: Path | None = None,
    copy_dir: Path | None = None,
    prefix: str = artifacts.DEFAULT_PREFIX,
) -> dict:
    enriched_dir = enriched_dir or ROOT / "leads" / "enriched"
    copy_dir = copy_dir or ROOT / "copy"
    enriched_dir.mkdir(parents=True, exist_ok=True)
    copy_dir.mkdir(parents=True, exist_ok=True)

    with source.open(newline="", encoding="utf-8") as handle:
        all_rows = list(csv.DictReader(handle))

    by_email = {}
    for row in all_rows:
        email = (row.get("primary_email") or row.get("Email") or "").split("|")[0].strip().lower()
        if email:
            by_email[email] = row

    research = load_json(research_path)
    copy_data = load_json(copy_path)
    copy_by_email = {k.lower(): v for k, v in copy_data.items()}

    out_rows = []
    json_out = []
    total_pass = 0
    total_emails = 0

    for item in research:
        email = item["email"].lower()
        src = by_email.get(email)
        if not src:
            raise SystemExit(f"Missing source row for {item['email']}")

        seq = copy_by_email.get(email)
        if not seq:
            raise SystemExit(f"Missing copy for {item['email']}")

        row = dict(src)
        row["research_signal"] = item["research_signal"]
        row["research_notes"] = item.get("research_notes", "")
        row["research_website"] = item.get("website", "")
        row["research_linkedin"] = item.get("linkedin", "")
        row["research_twitter"] = item.get("twitter", "")
        row["research_facebook"] = item.get("facebook", "")
        row["signal_strength"] = item.get("signal_strength", "")
        row["copy_variant"] = item.get("copy_variant", "")
        row["linkedin_topic"] = item.get("linkedin_topic", "")
        row["linkedin_posts_found"] = item.get("linkedin_posts_count", 0)
        row["linkedin_last_post"] = item.get("linkedin_last_post", "")

        lead_json = {
            "batch_id": batch_id,
            "lead": {
                "first_name": item.get("first_name", ""),
                "last_name": item.get("last_name", ""),
                "email": item["email"],
                "company": item.get("company", ""),
                "title": item.get("title", ""),
                "outreach_tier": item.get("outreach_tier", ""),
                "aevora_segment": item.get("aevora_segment", ""),
                "fit_score": item.get("fit_score", ""),
            },
            "channels": {
                "website": item.get("website", ""),
                "linkedin": item.get("linkedin", ""),
                "twitter": item.get("twitter", ""),
                "facebook": item.get("facebook", ""),
            },
            "signal": item["research_signal"],
            "signal_strength": item.get("signal_strength", ""),
            "copy_variant": item.get("copy_variant", ""),
            "notes": item.get("research_notes", ""),
            "sequence": [],
        }

        pairs = []
        for i, step in enumerate(seq):
            if isinstance(step, dict):
                subj, body = step["subject"], step["body"]
            else:
                subj, body = step[0], step[1]
            pairs.append((subj, body))
            row[f"email_{i+1}_subject"] = subj
            row[f"email_{i+1}_body"] = body
            q = qa(subj, body, item.get("company", ""))
            total_emails += 1
            if q["pass"]:
                total_pass += 1
            lead_json["sequence"].append(
                {"step": i + 1, "delay_days": DELAYS[i], "subject": subj, "body": body, "qa": q}
            )

        lead_json["sequence_issues"] = sequence_issues(pairs)

        out_rows.append(row)
        json_out.append(lead_json)

    out_csv = artifacts.enriched_csv(prefix, batch_id, enriched_dir)
    out_json_path = artifacts.emails_json(prefix, batch_id, copy_dir)
    out_md = artifacts.review_md(prefix, batch_id, copy_dir)

    fieldnames = [k for k in out_rows[0].keys() if k not in DROP_COLUMNS]
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(out_rows)

    out_json_path.write_text(json.dumps(json_out, indent=2), encoding="utf-8")

    lines = [
        f"# {prefix} review batch {batch_id} ({len(json_out)} leads)",
        f"Date: {date.today().isoformat()}",
        "Sender: Aevora Media (OFFER.md, BRAND_IDENTITY.md)",
        "",
        f"## QA summary: {total_pass}/{total_emails} passed",
        "",
    ]
    for lead in json_out:
        l = lead["lead"]
        name = f"{l['first_name']} {l['last_name']}".strip() or l["company"]
        lines.append(f"## {name} — {l['company']}")
        lines.append(
            f"**Email:** {l['email']} | **Tier:** {l['outreach_tier']} | "
            f"**Segment:** {l['aevora_segment']} | **Fit:** {l['fit_score']}"
        )
        lines.append(f"**Signal:** {lead['signal']} ({lead.get('signal_strength', '')})")
        lines.append(f"**Variant:** {lead.get('copy_variant', '')}")
        if lead.get("sequence_issues"):
            lines.append(f"**Sequence issues:** {', '.join(lead['sequence_issues'])}")
        lines.append(f"\n**Notes:** {lead['notes']}\n")
        for step in lead["sequence"]:
            q = step["qa"]
            status = "PASS" if q["pass"] else f"FAIL ({', '.join(q['issues'])})"
            lines.append(f"### Email {step['step']} (+{step['delay_days']}d) — {status}")
            lines.append(f"**Subject:** {step['subject']} ({q['subject_len']} chars, {q['word_count']} words)")
            lines.append("")
            lines.append(step["body"])
            lines.append("")
        lines.append("---\n")

    out_md.write_text("\n".join(lines), encoding="utf-8")

    return {
        "batch_id": batch_id,
        "leads": len(out_rows),
        "qa_pass": total_pass,
        "qa_total": total_emails,
        "csv": str(out_csv),
        "json": str(out_json_path),
        "md": str(out_md),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="leads/all-leads-with-email-normalized.csv")
    parser.add_argument("--research", required=True)
    parser.add_argument("--copy", required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument(
        "--prefix",
        default=artifacts.DEFAULT_PREFIX,
        help="Names the output files; the pipeline passes the list slug",
    )
    args = parser.parse_args()

    source = Path(args.source)
    if not source.is_absolute():
        source = ROOT / source
    research = Path(args.research)
    if not research.is_absolute():
        research = ROOT / research
    copy = Path(args.copy)
    if not copy.is_absolute():
        copy = ROOT / copy

    result = build_batch(source, research, copy, args.batch_id, prefix=args.prefix)
    print(f"Batch {result['batch_id']}: QA {result['qa_pass']}/{result['qa_total']}")
    print(f"  {result['csv']}")
    print(f"  {result['json']}")
    print(f"  {result['md']}")


if __name__ == "__main__":
    main()
