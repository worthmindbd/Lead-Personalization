#!/usr/bin/env python3
"""Clean Google Maps lead exports.

A lead with a real email is kept. The only removals are addresses that cannot
be mailed — missing, placeholder, or already present on another row — plus the
per-domain cap, so one firm does not receive five copies of the same sequence.
Open/closed status is reported, never filtered on.

Optional flags apply secondary filters (business-rich countries, geo mismatch).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lead_personalization.naming import campaign_stem  # noqa: E402
from lead_personalization.segments import is_generic_email as is_generic  # noqa: E402

LEADS_DIR = ROOT / "leads"


def count_named_path(stem: str, count: int, label: str, directory: Path = LEADS_DIR) -> Path:
    return directory / f"{stem}-{count}-{label}.csv"


BUSINESS_RICH_COUNTRIES = {
    "US", "CA", "GB", "AU", "NZ", "IE",
    "CH", "DE", "FR", "IT", "ES", "PT", "NL", "BE", "AT", "NO", "SE", "DK", "FI",
    "MC", "LI", "LU", "GR",
    "SG", "HK", "JP", "KR",
    "AE", "QA", "BH", "BS", "IL",
}

TZ_TO_COUNTRY: dict[str, str] = {
    "America/Vancouver": "CA", "America/Toronto": "CA", "America/Edmonton": "CA",
    "America/Winnipeg": "CA", "America/Halifax": "CA", "America/St_Johns": "CA",
    "America/Blanc-Sablon": "CA", "America/Creston": "CA",
    "Europe/London": "GB", "Europe/Gibraltar": "GB",
    "Australia/Sydney": "AU", "Australia/Melbourne": "AU", "Australia/Brisbane": "AU",
    "Australia/Perth": "AU", "Australia/Adelaide": "AU", "Australia/Hobart": "AU",
    "Australia/Darwin": "AU", "Pacific/Auckland": "NZ",
    "Europe/Madrid": "ES", "Atlantic/Canary": "ES", "Europe/Rome": "IT",
    "Europe/Zurich": "CH", "Europe/Oslo": "NO", "Europe/Lisbon": "PT",
    "Europe/Athens": "GR", "Europe/Paris": "FR", "Europe/Berlin": "DE",
    "Europe/Monaco": "MC", "Europe/Stockholm": "SE", "Europe/Amsterdam": "NL",
    "Asia/Dubai": "AE", "Asia/Qatar": "QA", "Asia/Hong_Kong": "HK",
    "Asia/Singapore": "SG", "Asia/Tokyo": "JP", "Asia/Seoul": "KR",
    "Asia/Jerusalem": "IL", "America/Nassau": "BS", "America/Puerto_Rico": "US",
    "Pacific/Honolulu": "US", "America/Anchorage": "US",
}

KEEP_COLUMNS = [
    "Name",
    "Email",
    "Website",
    "First_category",
    "Second_category",
    "City",
    "State",
    "Country",
    "Phone_1",
    "Linkedin_URL",
    "Facebook_URL",
    "Instagram_URL",
    "Twitter_URL",
    "Youtube_URL",
    "GMB_URL",
    "Meta_Description",
    # GMB self-written business blurb — strong research signal when present.
    "Description",
    # Review signals are cheap, verifiable personalization hooks — keep when present.
    "Average_rating",
    "Reviews_count",
    "Rating",
    "Review_count",
    "Reviews",
]

# Free mailbox providers: never apply the per-domain cap to these — many
# unrelated businesses share them.
FREE_MAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
    "icloud.com", "msn.com", "live.com", "me.com", "mac.com", "ymail.com",
    "comcast.net", "att.net", "sbcglobal.net", "verizon.net", "protonmail.com",
    "proton.me", "mail.com", "gmx.com", "zoho.com",
}

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PLACEHOLDER_DOMAINS = {
    "example.com", "test.com", "mysite.com", "domain.com", "email.com",
    "yoursite.com", "website.com", "company.com",
}
CLOSED_STATUSES = {"closed permanently", "permanently closed", "closed"}


def extract_emails(raw: str) -> list[str]:
    if not raw or (isinstance(raw, float) and pd.isna(raw)):
        return []
    return [e.lower() for e in EMAIL_RE.findall(str(raw).replace(";", "|"))]


def is_placeholder(email: str) -> bool:
    domain = email.split("@", 1)[-1].lower()
    return domain in PLACEHOLDER_DOMAINS or domain.endswith(".example")


def infer_country(row: pd.Series) -> str:
    country = str(row.get("Country") or "").strip()
    if country and country != "nan":
        return country.upper()
    tz = str(row.get("Timezone") or "").strip()
    if tz in TZ_TO_COUNTRY:
        return TZ_TO_COUNTRY[tz]
    if tz.startswith("America/"):
        return "US"
    return ""


def pick_primary_email(emails: list[str]) -> str:
    if not emails:
        return ""
    personal = [e for e in emails if not is_generic(e)]
    return personal[0] if personal else emails[0]


def keyword_geo_mismatch(keyword: str, country: str) -> bool:
    if not keyword or country in {"", "US", "CA"}:
        return False
    if "UAE" in keyword or "Singapore" in keyword or "Dubai" in keyword:
        return False
    return bool(re.search(r",\s*[A-Z]{2}\b", keyword))


def clean_gmb_leads(
    source: Path,
    output: Path,
    *,
    business_rich_only: bool = False,
    drop_geo_mismatch: bool = False,
    require_website: bool = False,
    max_per_domain: int = 2,
) -> pd.DataFrame:
    df = pd.read_excel(source) if source.suffix.lower() in {".xlsx", ".xls"} else pd.read_csv(source)
    stats: dict[str, int] = {"input_rows": len(df)}

    df["Country_inferred"] = df.apply(infer_country, axis=1)
    df["Email"] = df["Email_From_WEBSITE"].apply(
        lambda v: pick_primary_email(extract_emails(v))
    )

    before = len(df)
    df = df[df["Email"].astype(bool)].copy()
    stats["removed_no_email"] = before - len(df)

    before = len(df)
    df = df[~df["Email"].apply(is_placeholder)].copy()
    stats["removed_placeholder_email"] = before - len(df)

    if require_website:
        before = len(df)
        df = df[df["Website"].fillna("").astype(str).str.strip().astype(bool)].copy()
        stats["removed_no_website"] = before - len(df)

    if business_rich_only:
        before = len(df)
        df = df[df["Country_inferred"].isin(BUSINESS_RICH_COUNTRIES)].copy()
        stats["removed_non_business_rich_country"] = before - len(df)

    if drop_geo_mismatch:
        before = len(df)
        df = df[~df.apply(
            lambda r: keyword_geo_mismatch(str(r.get("Keyword") or ""), r["Country_inferred"]),
            axis=1,
        )].copy()
        stats["removed_geo_mismatch"] = before - len(df)

    before = len(df)
    df = df.drop_duplicates(subset=["Email"], keep="first")
    stats["removed_duplicate_email"] = before - len(df)

    if max_per_domain > 0:
        before = len(df)
        counts: dict[str, int] = {}
        keep_mask = []
        for email in df["Email"]:
            domain = str(email).split("@", 1)[-1].lower()
            if domain in FREE_MAIL_DOMAINS:
                keep_mask.append(True)
                continue
            counts[domain] = counts.get(domain, 0) + 1
            keep_mask.append(counts[domain] <= max_per_domain)
        df = df[pd.Series(keep_mask, index=df.index)].copy()
        stats["removed_domain_cap"] = before - len(df)

    df["Country"] = df["Country_inferred"]
    out = df[[c for c in KEEP_COLUMNS if c in df.columns or c == "Email"]].copy()

    filtered = business_rich_only or drop_geo_mismatch or require_website
    label = "cleaned" if filtered else "with-email"
    base = campaign_stem(output.stem)
    output = count_named_path(base, len(out), label, output.parent)
    output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output, index=False, encoding="utf-8")

    stats["output_rows"] = len(out)
    stats["countries"] = df["Country"].value_counts().to_dict()

    print(f"Cleaned {stats['input_rows']:,} -> {stats['output_rows']:,} rows ({label})")
    for key, val in stats.items():
        if key.startswith("removed_"):
            print(f"  {key}: {val:,}")
    if "Business_Status" in df.columns:
        # Reported, never filtered on: a closed listing with a working inbox is
        # still a person who can reply.
        closed_kept = df["Business_Status"].fillna("").str.lower().isin(CLOSED_STATUSES).sum()
        print(f"  closed_businesses_kept: {closed_kept:,}")
    print(f"Output: {output}")
    print("Top countries:")
    for country, count in sorted(stats["countries"].items(), key=lambda x: -x[1])[:12]:
        print(f"  {country}: {count:,}")

    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean Google Maps lead export")
    parser.add_argument("source", nargs="?", default=str(ROOT / "leads" / "Mixed-38k.xlsx"))
    parser.add_argument("-o", "--output", default=str(ROOT / "leads" / "mixed-with-email.csv"))
    parser.add_argument(
        "--business-rich", action="store_true",
        help="Secondary filter: keep business-rich countries only",
    )
    parser.add_argument(
        "--max-per-domain", type=int, default=2,
        help="Max leads per business email domain (default: 2; 0 disables)",
    )
    parser.add_argument(
        "--drop-geo-mismatch", action="store_true",
        help="Secondary filter: remove US-keyword/geo mismatches (e.g. Dhaka scrape noise)",
    )
    parser.add_argument(
        "--require-website", action="store_true",
        help="Secondary filter: require Website column",
    )
    args = parser.parse_args()

    source = Path(args.source)
    if not source.is_absolute():
        source = ROOT / source

    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output

    clean_gmb_leads(
        source,
        output,
        business_rich_only=args.business_rich,
        drop_geo_mismatch=args.drop_geo_mismatch,
        require_website=args.require_website,
        max_per_domain=args.max_per_domain,
    )


if __name__ == "__main__":
    main()
