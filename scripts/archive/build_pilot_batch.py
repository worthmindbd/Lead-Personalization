#!/usr/bin/env python3
"""Build enriched pilot outputs for a batch (1 or 2+)."""

import argparse
import csv
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CSV = ROOT / "leads" / "Real-Estate-USA-500.csv"

BANNED = [
    "hope this email finds you well",
    "impressive linkedin",
    "pick your brain",
    "circle back",
    "touch base",
    "deep dive",
    "—",
]

BATCH_CONFIG = {
    1: {
        "row_start": 0,
        "row_count": 20,
        "research": "pilot-20-research.json",
        "copy": None,  # embedded in build_pilot_outputs.py batch 1 only
        "out_csv": "pilot-20-enriched.csv",
        "out_json": "pilot-emails.json",
        "out_md": None,
    },
    2: {
        "row_start": 20,
        "row_count": 20,
        "research": "pilot-20-batch2-research.json",
        "copy": "pilot-20-batch2-copy.json",
        "out_csv": "pilot-20-batch2-enriched.csv",
        "out_json": "pilot-emails-batch2.json",
        "out_md": "pilot-review-batch2-{date}.md",
    },
    3: {
        "row_start": 47,
        "row_count": 20,
        "research": "pilot-20-batch3-research.json",
        "copy": "pilot-20-batch3-copy.json",
        "out_csv": "pilot-20-batch3-enriched.csv",
        "out_json": "pilot-emails-batch3.json",
        "out_md": "pilot-review-batch3-{date}.md",
    },
    4: {
        "row_start": 67,
        "row_count": 20,
        "research": "pilot-20-batch4-research.json",
        "copy": "pilot-20-batch4-copy.json",
        "out_csv": "pilot-20-batch4-enriched.csv",
        "out_json": "pilot-emails-batch4.json",
        "out_md": "pilot-review-batch4-{date}.md",
    },
    5: {
        "row_start": 87,
        "row_count": 20,
        "research": "pilot-20-batch5-research.json",
        "copy": "pilot-20-batch5-copy.json",
        "out_csv": "pilot-20-batch5-enriched.csv",
        "out_json": "pilot-emails-batch5.json",
        "out_md": "pilot-review-batch5-{date}.md",
    },
    6: {
        "row_start": 107,
        "row_count": 20,
        "research": "pilot-20-batch6-research.json",
        "copy": "pilot-20-batch6-copy.json",
        "out_csv": "pilot-20-batch6-enriched.csv",
        "out_json": "pilot-emails-batch6.json",
        "out_md": "pilot-review-batch6-{date}.md",
    },
    7: {
        "row_start": 127,
        "row_count": 20,
        "research": "pilot-20-batch7-research.json",
        "copy": "pilot-20-batch7-copy.json",
        "out_csv": "pilot-20-batch7-enriched.csv",
        "out_json": "pilot-emails-batch7.json",
        "out_md": "pilot-review-batch7-{date}.md",
    },
    8: {
        "row_start": 147,
        "row_count": 20,
        "research": "pilot-20-batch8-research.json",
        "copy": "pilot-20-batch8-copy.json",
        "out_csv": "pilot-20-batch8-enriched.csv",
        "out_json": "pilot-emails-batch8.json",
        "out_md": "pilot-review-batch8-{date}.md",
    },
    9: {
        "row_start": 167,
        "row_count": 20,
        "research": "pilot-20-batch9-research.json",
        "copy": "pilot-20-batch9-copy.json",
        "out_csv": "pilot-20-batch9-enriched.csv",
        "out_json": "pilot-emails-batch9.json",
        "out_md": "pilot-review-batch9-{date}.md",
    },
    10: {
        "row_start": 187,
        "row_count": 20,
        "research": "pilot-20-batch10-research.json",
        "copy": "pilot-20-batch10-copy.json",
        "out_csv": "pilot-20-batch10-enriched.csv",
        "out_json": "pilot-emails-batch10.json",
        "out_md": "pilot-review-batch10-{date}.md",
    },
    11: {
        "row_start": 207,
        "row_count": 20,
        "research": "pilot-20-batch11-research.json",
        "copy": "pilot-20-batch11-copy.json",
        "out_csv": "pilot-20-batch11-enriched.csv",
        "out_json": "pilot-emails-batch11.json",
        "out_md": "pilot-review-batch11-{date}.md",
    },
    12: {
        "row_start": 227,
        "row_count": 20,
        "research": "pilot-20-batch12-research.json",
        "copy": "pilot-20-batch12-copy.json",
        "out_csv": "pilot-20-batch12-enriched.csv",
        "out_json": "pilot-emails-batch12.json",
        "out_md": "pilot-review-batch12-{date}.md",
    },
    13: {
        "row_start": 247,
        "row_count": 20,
        "research": "pilot-20-batch13-research.json",
        "copy": "pilot-20-batch13-copy.json",
        "out_csv": "pilot-20-batch13-enriched.csv",
        "out_json": "pilot-emails-batch13.json",
        "out_md": "pilot-review-batch13-{date}.md",
    },
    14: {
        "row_start": 267,
        "row_count": 20,
        "research": "pilot-20-batch14-research.json",
        "copy": "pilot-20-batch14-copy.json",
        "out_csv": "pilot-20-batch14-enriched.csv",
        "out_json": "pilot-emails-batch14.json",
        "out_md": "pilot-review-batch14-{date}.md",
    },
    15: {
        "row_start": 287,
        "row_count": 20,
        "research": "pilot-20-batch15-research.json",
        "copy": "pilot-20-batch15-copy.json",
        "out_csv": "pilot-20-batch15-enriched.csv",
        "out_json": "pilot-emails-batch15.json",
        "out_md": "pilot-review-batch15-{date}.md",
    },
    16: {
        "row_start": 307,
        "row_count": 20,
        "research": "pilot-20-batch16-research.json",
        "copy": "pilot-20-batch16-copy.json",
        "out_csv": "pilot-20-batch16-enriched.csv",
        "out_json": "pilot-emails-batch16.json",
        "out_md": "pilot-review-batch16-{date}.md",
    },
    17: {
        "row_start": 327,
        "row_count": 20,
        "research": "pilot-20-batch17-research.json",
        "copy": "pilot-20-batch17-copy.json",
        "out_csv": "pilot-20-batch17-enriched.csv",
        "out_json": "pilot-emails-batch17.json",
        "out_md": "pilot-review-batch17-{date}.md",
    },
    18: {
        "row_start": 347,
        "row_count": 20,
        "research": "pilot-20-batch18-research.json",
        "copy": "pilot-20-batch18-copy.json",
        "out_csv": "pilot-20-batch18-enriched.csv",
        "out_json": "pilot-emails-batch18.json",
        "out_md": "pilot-review-batch18-{date}.md",
    },
    19: {
        "row_start": 367,
        "row_count": 20,
        "research": "pilot-20-batch19-research.json",
        "copy": "pilot-20-batch19-copy.json",
        "out_csv": "pilot-20-batch19-enriched.csv",
        "out_json": "pilot-emails-batch19.json",
        "out_md": "pilot-review-batch19-{date}.md",
    },
    20: {
        "row_start": 387,
        "row_count": 20,
        "research": "pilot-20-batch20-research.json",
        "copy": "pilot-20-batch20-copy.json",
        "out_csv": "pilot-20-batch20-enriched.csv",
        "out_json": "pilot-emails-batch20.json",
        "out_md": "pilot-review-batch20-{date}.md",
    },
    21: {
        "row_start": 407,
        "row_count": 20,
        "research": "pilot-20-batch21-research.json",
        "copy": "pilot-20-batch21-copy.json",
        "out_csv": "pilot-20-batch21-enriched.csv",
        "out_json": "pilot-emails-batch21.json",
        "out_md": "pilot-review-batch21-{date}.md",
    },
    22: {
        "row_start": 427,
        "row_count": 19,
        "research": "pilot-20-batch22-research.json",
        "copy": "pilot-20-batch22-copy.json",
        "out_csv": "pilot-20-batch22-enriched.csv",
        "out_json": "pilot-emails-batch22.json",
        "out_md": "pilot-review-batch22-{date}.md",
    },
    23: {
        "row_start": 20,
        "row_count": 7,
        "research": "pilot-20-batch23-research.json",
        "copy": "pilot-20-batch23-copy.json",
        "out_csv": "pilot-20-batch23-enriched.csv",
        "out_json": "pilot-emails-batch23.json",
        "out_md": "pilot-review-batch23-{date}.md",
    },
}


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def qa(subject: str, body: str) -> dict:
    issues = []
    wc = word_count(body)
    if wc > 100:
        issues.append(f"word count {wc}>100")
    if len(subject) > 60:
        issues.append(f"subject len {len(subject)}>60")
    low = (subject + body).lower()
    for b in BANNED:
        if b in low:
            issues.append(f"banned:{b}")
    if "calendly" in low or "book 15" in low or "free tuesday" in low:
        issues.append("hard CTA")
    return {"word_count": wc, "subject_len": len(subject), "pass": len(issues) == 0, "issues": issues}


def load_copy(batch: int) -> dict:
    cfg = BATCH_CONFIG[batch]
    if cfg["copy"]:
        data = json.loads((ROOT / "campaigns" / cfg["copy"]).read_text())
        return {k.lower(): v for k, v in data.items()}
    # batch 1: import from legacy script
    import importlib.util

    spec = importlib.util.spec_from_file_location("legacy", ROOT / "scripts" / "build_pilot_outputs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return {k.lower(): v for k, v in mod.COPY.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, default=2)
    args = parser.parse_args()
    batch = args.batch
    cfg = BATCH_CONFIG[batch]

    research = json.loads((ROOT / "campaigns" / cfg["research"]).read_text())
    copy = load_copy(batch)

    with SOURCE_CSV.open(newline="", encoding="utf-8") as f:
        all_rows = list(csv.DictReader(f))

    by_email = {r["Email"].lower(): r for r in all_rows}
    out_rows = []
    json_out = []

    for item in research:
        email = item["email"].lower()
        src = by_email.get(email)
        if not src:
            raise SystemExit(f"Missing source row for {item['email']}")

        seq = copy.get(email)
        if not seq:
            raise SystemExit(f"Missing copy for {item['email']}")

        row = dict(src)
        row["research_signal"] = item["research_signal"]
        row["research_notes"] = item["research_notes"]
        row["research_website"] = item["website"]
        row["research_linkedin"] = item["linkedin"]
        row["research_twitter"] = item["twitter"]
        row["research_facebook"] = item["facebook"]

        lead_json = {
            "batch": batch,
            "lead": {
                "first_name": item["first_name"],
                "last_name": item["last_name"],
                "email": item["email"],
                "company": item["company"],
                "title": item["title"],
            },
            "channels": {
                "website": item["website"],
                "linkedin": item["linkedin"],
                "twitter": item["twitter"],
                "facebook": item["facebook"],
            },
            "signal": item["research_signal"],
            "notes": item["research_notes"],
            "sequence": [],
        }

        delays = [0, 3, 7]
        for i, step in enumerate(seq):
            subj, body = step[0], step[1]
            row[f"email_{i+1}_subject"] = subj
            row[f"email_{i+1}_body"] = body
            q = qa(subj, body)
            lead_json["sequence"].append(
                {"step": i + 1, "delay_days": delays[i], "subject": subj, "body": body, "qa": q}
            )

        out_rows.append(row)
        json_out.append(lead_json)

    out_csv = ROOT / "leads" / cfg["out_csv"]
    out_json_path = ROOT / "copy" / cfg["out_json"]
    md_name = (cfg["out_md"] or "pilot-review-{date}.md").format(date=date.today().isoformat())
    out_md = ROOT / "copy" / md_name

    fieldnames = list(out_rows[0].keys())
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(out_rows)

    out_json_path.parent.mkdir(parents=True, exist_ok=True)
    out_json_path.write_text(json.dumps(json_out, indent=2), encoding="utf-8")

    total_pass = sum(1 for l in json_out for s in l["sequence"] if s["qa"]["pass"])
    total_emails = sum(len(l["sequence"]) for l in json_out)

    lead_count = len(json_out)
    lines = [
        f"# Pilot review batch {batch} ({lead_count} leads)",
        f"Date: {date.today().isoformat()}",
        "Sender: Aevora Media (OFFER.md, BRAND_IDENTITY.md)",
        "",
        f"## QA summary: {total_pass}/{total_emails} passed",
        "",
    ]
    for lead in json_out:
        l = lead["lead"]
        lines.append(f"## {l['first_name']} {l['last_name']} — {l['company']}")
        lines.append(f"**Email:** {l['email']} | **Title:** {l['title']}")
        lines.append(f"**Signal:** {lead['signal']}")
        lines.append("")
        lines.append("**Channels:**")
        for k, v in lead["channels"].items():
            lines.append(f"- {k}: {v or '(none)'}")
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
    print(f"Batch {batch}: QA {total_pass}/{total_emails}")
    print(f"  {out_csv}")
    print(f"  {out_json_path}")
    print(f"  {out_md}")


if __name__ == "__main__":
    main()
