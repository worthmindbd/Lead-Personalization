"""High-level pipeline: normalize rows and personalize them end to end.

These are in-memory primitives (lists of dict rows in, structured results out)
so the web app can drive research + copy against a database without the
manifest/file orchestration the CLI uses. The copy is fully deterministic.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urlparse

from lead_personalization.config import Config
from lead_personalization.copywriter import fix_sequence, generate_sequence
from lead_personalization.offer_pack import OfferPack
from lead_personalization.renderers import NodePlaywrightRenderer, PageRenderer
from lead_personalization.research import research_lead
from lead_personalization import linkedin
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
    except Exception:
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
        "aevora_segment": segment,
        "research_urls": " | ".join(research_urls(row)),
    })
    return out


def normalize_rows(rows: list[dict]) -> list[dict]:
    """Normalize raw lead dicts into the research-ready schema."""
    return [normalize_row(i, row) for i, row in enumerate(rows)]


def normalized_fieldnames(source_fields: list[str]) -> list[str]:
    return list(source_fields) + [f for f in DERIVED_FIELDS if f not in source_fields]


# ---------------------------------------------------------------------------
# Personalization (research + copy)
# ---------------------------------------------------------------------------


def default_renderer(config: Config) -> PageRenderer | None:
    """Tier-2 renderer if render fallback is on and the script exists."""
    if not config.render_fallback:
        return None
    renderer = NodePlaywrightRenderer(
        script_path=config.render_script,
        cwd=config.root,
        timeout_s=config.render_timeout_s,
    )
    return renderer if renderer.available else None


def warm_linkedin(rows: list[dict], config: Config) -> dict:
    """Pre-scrape LinkedIn posts for all rows in one batched, cached call."""
    if not config.linkedin_enrich:
        return {}
    urls = [
        (r.get("Linkedin_URL") or "").strip()
        for r in rows
        if (r.get("Linkedin_URL") or "").strip()
    ]
    if not urls:
        return {}
    try:
        return linkedin.scrape_profiles(
            urls,
            cache_file=config.apify_cache_file,
            token=config.apify_token,
            max_posts=config.linkedin_max_posts,
        )
    except Exception as exc:  # noqa: BLE001 - degrade gracefully, copy still works
        print(f"LinkedIn enrichment skipped: {exc}")
        return {}


def write_copy(
    row: dict,
    research: dict,
    offer_pack: OfferPack,
    *,
    key_salt: str = "",
) -> tuple[list[dict], str]:
    """Generate + QA-fix a sequence from existing research (no re-research)."""
    seq, variant = generate_sequence(row, research, offer_pack, key_salt=key_salt)
    seq = fix_sequence(seq, row, research, offer_pack)
    return [{"subject": s, "body": b} for s, b in seq], variant


def personalize_row(
    row: dict,
    offer_pack: OfferPack,
    config: Config,
    *,
    li_scraped: dict | None = None,
    renderer: PageRenderer | None = None,
    key_salt: str = "",
) -> dict:
    """Research one row and generate its 3-email sequence."""
    item = research_lead(
        row,
        li_scraped or {},
        renderer=renderer,
        render_fallback=config.render_fallback,
    )
    sequence, variant = write_copy(row, item, offer_pack, key_salt=key_salt)
    item["copy_variant"] = variant
    return {
        "research": item,
        "sequence": sequence,
        "variant": variant,
    }


def personalize_rows(
    rows: list[dict],
    offer_pack: OfferPack,
    config: Config,
    *,
    renderer: PageRenderer | None = None,
    warm: bool = True,
    on_progress: Callable[[int, int, dict], None] | None = None,
) -> list[dict]:
    """Research + write copy for a list of normalized rows."""
    if renderer is None:
        renderer = default_renderer(config)
    li_scraped = warm_linkedin(rows, config) if warm else {}

    results: list[dict] = []
    total = len(rows)
    for i, row in enumerate(rows, start=1):
        result = personalize_row(
            row, offer_pack, config, li_scraped=li_scraped, renderer=renderer
        )
        results.append(result)
        if on_progress:
            on_progress(i, total, result["research"])
    return results


# ---------------------------------------------------------------------------
# Thin file helpers (used by CLI wrappers / smoke tests)
# ---------------------------------------------------------------------------


def read_csv_rows(path: str | Path) -> tuple[list[dict], list[str]]:
    import csv

    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        return list(reader), fields
