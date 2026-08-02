#!/usr/bin/env python3
"""Normalize mixed lead CSV into research-ready schema."""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from lead_personalization.segments import (  # noqa: E402
    BUSINESS_NAME_MARKERS,
    CATEGORY_TO_SEGMENT,
    GENERIC_EMAIL_PREFIXES,
    fit_score_for,
    is_generic_email,
    is_plausible_first_name,
    is_plausible_last_name,
    looks_like_business,
    resolve_outreach_tier,
    segment_for_category,
)

DEFAULT_SOURCE = ROOT / "leads" / "all-leads-with-email.csv"
DEFAULT_CSV_OUT = ROOT / "leads" / "all-leads-with-email-normalized.csv"
DEFAULT_JSON_OUT = ROOT / "campaigns" / "mix-leads-normalized.json"


def count_named_path(stem: str, count: int, label: str, directory: Path) -> Path:
    return directory / f"{stem}-{count}-{label}.csv"


def campaign_stem(stem: str) -> str:
    s = stem.lower().replace("-38k", "")
    parts = s.split("-")
    alpha: list[str] = []
    for part in parts:
        if part.isdigit():
            break
        if part in {"cleaned", "verified", "valid", "normalized"}:
            break
        alpha.append(part)
    return "-".join(alpha) or "mixed"


def strip_count_suffix(stem: str) -> str:
    return campaign_stem(stem)


def normalized_output_path(source: Path, row_count: int) -> Path:
    base = campaign_stem(source.stem)
    return count_named_path(base, row_count, "normalized", source.parent)

TITLE_AT_PATTERN = re.compile(r"\s+at\s+", re.I)
TITLE_DASH_PATTERN = re.compile(r"\s+[-–|]\s+")
PERSON_NAME_PATTERN = re.compile(
    r"^([A-Z][a-zA-Z.'-]+(?:\s+[A-Z][a-zA-Z.'-]+)?)\s+([A-Z][a-zA-Z.'-]+(?:\s+[A-Z][a-zA-Z.'-]+)?)$"
)


def split_emails(raw: str) -> list[str]:
    parts = [p.strip() for p in (raw or "").split("|")]
    return [p for p in parts if p and "@" in p]


def pick_primary_email(emails: list[str]) -> str:
    if not emails:
        return ""
    personal = [e for e in emails if not is_generic_email(e)]
    return personal[0] if personal else emails[0]


def domain_company(website: str) -> str:
    if not website:
        return ""
    try:
        host = urlparse(website.strip()).netloc.lower()
        host = host.removeprefix("www.")
        if not host:
            return ""
        base = host.split(".")[0]
        return base.replace("-", " ").title()
    except Exception:
        return ""


def parse_name_field(name: str, website: str) -> dict:
    raw = (name or "").strip()
    result = {
        "first_name": "",
        "last_name": "",
        "title": "",
        "company_name": "",
    }
    if not raw:
        result["company_name"] = domain_company(website)
        return result

    if TITLE_AT_PATTERN.search(raw):
        person_part, rest = TITLE_AT_PATTERN.split(raw, maxsplit=1)
        person_part = person_part.strip()
        rest = rest.strip()
        match = PERSON_NAME_PATTERN.match(person_part)
        if match:
            result["first_name"] = match.group(1)
            result["last_name"] = match.group(2)
        else:
            parts = person_part.split()
            if len(parts) >= 2:
                result["first_name"] = parts[0]
                result["last_name"] = " ".join(parts[1:])
            else:
                result["company_name"] = person_part
        result["title"] = rest
        result["company_name"] = result["company_name"] or rest
        return result

    if TITLE_DASH_PATTERN.search(raw):
        left, right = TITLE_DASH_PATTERN.split(raw, maxsplit=1)
        left, right = left.strip(), right.strip()
        match = PERSON_NAME_PATTERN.match(left)
        if match and not looks_like_business(left):
            result["first_name"] = match.group(1)
            result["last_name"] = match.group(2)
            result["title"] = right
            result["company_name"] = right
        else:
            result["company_name"] = raw
        return result

    if looks_like_business(raw):
        result["company_name"] = raw
        return result

    match = PERSON_NAME_PATTERN.match(raw)
    if match:
        result["first_name"] = match.group(1)
        result["last_name"] = match.group(2)
        result["company_name"] = domain_company(website) or raw
        return result

    parts = raw.split()
    if len(parts) == 2 and parts[0][0].isupper() and not looks_like_business(raw):
        fn, ln = parts[0], parts[1]
        if is_plausible_first_name(fn) and is_plausible_last_name(ln):
            result["first_name"] = fn
            result["last_name"] = ln
            result["company_name"] = domain_company(website) or raw
        else:
            result["company_name"] = raw
    else:
        result["company_name"] = raw

    return result


def outreach_tier(first_name: str, last_name: str, primary_email: str, raw_name: str = "") -> str:
    return resolve_outreach_tier(first_name, last_name, primary_email, raw_name)


def research_urls(row: dict) -> list[str]:
    urls = []
    for key in ("Website", "Linkedin_URL", "Instagram_URL", "Facebook_URL", "Twitter_URL"):
        val = (row.get(key) or "").strip()
        if val and val not in urls:
            urls.append(val)
    return urls


def normalize_row(index: int, row: dict) -> dict:
    emails = split_emails(row.get("Email", ""))
    primary_email = pick_primary_email(emails)
    parsed = parse_name_field(row.get("Name", ""), row.get("Website", ""))
    company = parsed["company_name"] or domain_company(row.get("Website", "")) or (row.get("Name") or "").strip()
    category = (row.get("First_category") or "").strip()
    segment = segment_for_category(category)

    out = dict(row)
    out.update(
        {
            "row_index": str(index),
            "primary_email": primary_email,
            "all_emails": " | ".join(emails),
            "company_name": company,
            "first_name": parsed["first_name"],
            "last_name": parsed["last_name"],
            "title": parsed["title"],
            "outreach_tier": outreach_tier(
                parsed["first_name"],
                parsed["last_name"],
                primary_email,
                (row.get("Name") or "").strip(),
            ),
            "aevora_segment": segment,
            "fit_score": fit_score_for(segment, category),
            "research_urls": " | ".join(research_urls(row)),
        }
    )
    return out


def normalize_leads(
    source: Path = DEFAULT_SOURCE,
    csv_out: Path = DEFAULT_CSV_OUT,
    json_out: Path = DEFAULT_JSON_OUT,
) -> list[dict]:
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    extra_fields = [
        "row_index", "primary_email", "all_emails", "company_name",
        "first_name", "last_name", "title", "outreach_tier",
        "aevora_segment", "fit_score", "research_urls",
    ]
    out_fieldnames = fieldnames + [f for f in extra_fields if f not in fieldnames]
    normalized = [normalize_row(i, row) for i, row in enumerate(rows)]

    if source != DEFAULT_SOURCE:
        csv_out = normalized_output_path(source, len(normalized))

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
            "  Add them to scripts/personalization/segments.py CATEGORY_TO_SEGMENT "
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
