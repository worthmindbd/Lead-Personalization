"""Row normalization: raw GMB export rows in, research-ready rows out.

Pure in-memory primitives (lists of dict rows in, structured rows out); the
CSV/JSON file orchestration lives in ``scripts/personalization/normalize_leads.py``.
The copy path (research -> sequence) is driven by ``scripts/personalization/process_batch.py``
using ``lead_personalization.research`` + ``copywriter`` directly.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from lead_personalization.segments import (
    is_generic_email,
    is_plausible_first_name,
    is_plausible_last_name,
    looks_like_business,
    resolve_outreach_tier,
    segment_for_category,
)

# Columns normalize_rows derives on top of the source columns.
DERIVED_FIELDS = [
    "row_index", "primary_email", "all_emails", "company_name",
    "first_name", "last_name", "title", "outreach_tier",
    "aevora_segment", "research_urls",
]

_TITLE_AT_PATTERN = re.compile(r"\s+at\s+", re.I)
_TITLE_DASH_PATTERN = re.compile(r"\s+[-–|]\s+")
_PERSON_NAME_PATTERN = re.compile(
    r"^([A-Z][a-zA-Z.'-]+(?:\s+[A-Z][a-zA-Z.'-]+)?)\s+([A-Z][a-zA-Z.'-]+(?:\s+[A-Z][a-zA-Z.'-]+)?)$"
)


# ---------------------------------------------------------------------------
# Normalization (ported from normalize_leads.py, made file-free)
# ---------------------------------------------------------------------------


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
    except (ValueError, AttributeError):
        return ""


def parse_name_field(name: str, website: str) -> dict:
    raw = (name or "").strip()
    result = {"first_name": "", "last_name": "", "title": "", "company_name": ""}
    if not raw:
        result["company_name"] = domain_company(website)
        return result

    if _TITLE_AT_PATTERN.search(raw):
        person_part, rest = _TITLE_AT_PATTERN.split(raw, maxsplit=1)
        person_part = person_part.strip()
        rest = rest.strip()
        match = _PERSON_NAME_PATTERN.match(person_part)
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

    if _TITLE_DASH_PATTERN.search(raw):
        left, right = _TITLE_DASH_PATTERN.split(raw, maxsplit=1)
        left, right = left.strip(), right.strip()
        match = _PERSON_NAME_PATTERN.match(left)
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

    match = _PERSON_NAME_PATTERN.match(raw)
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
    company = (
        parsed["company_name"]
        or domain_company(row.get("Website", ""))
        or (row.get("Name") or "").strip()
    )
    category = (row.get("First_category") or "").strip()
    segment = segment_for_category(category)

    out = dict(row)
    out.update({
        "row_index": str(index),
        "primary_email": primary_email,
        "all_emails": " | ".join(emails),
        "company_name": company,
        "first_name": parsed["first_name"],
        "last_name": parsed["last_name"],
        "title": parsed["title"],
        "outreach_tier": resolve_outreach_tier(
            parsed["first_name"], parsed["last_name"], primary_email,
            (row.get("Name") or "").strip(),
        ),
        # Chooses the copy angle and subject templates. It is not a filter:
        # every lead with a mailable address gets a sequence, whatever its
        # segment. There used to be a `fit_score` here too, scoring leads as
        # skip/low/medium/high — nothing ever read it.
        "aevora_segment": segment,
        "research_urls": " | ".join(research_urls(row)),
    })
    return out


def normalize_rows(rows: list[dict]) -> list[dict]:
    """Normalize raw lead dicts into the research-ready schema."""
    return [normalize_row(i, row) for i, row in enumerate(rows)]


def normalized_fieldnames(source_fields: list[str]) -> list[str]:
    return list(source_fields) + [f for f in DERIVED_FIELDS if f not in source_fields]
