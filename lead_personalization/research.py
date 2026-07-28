"""Lead research: signal discovery from websites and LinkedIn.

Tier 1 is a plain HTTP fetch; when that yields nothing usable a ``PageRenderer``
(tier 2/3) is tried. The result is classified into an evidence bucket that
drives which opener pool the copywriter uses. No prospect text ever reaches the
copy unless it passes the usability guards here.
"""

from __future__ import annotations

import html
import re
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

from lead_personalization import linkedin
from lead_personalization.qa import HARD_CTA_PATTERNS, contains_forbidden
from lead_personalization.renderers import VIDEO_EVIDENCE, PageRenderer

USER_AGENT = "Mozilla/5.0 (compatible; AevoraLeadResearch/1.0)"
FETCH_TIMEOUT = 12

GENERIC_TITLE_PARTS = {
    "home", "homepage", "welcome", "about", "about us", "contact", "contact us",
    "official site", "official website", "index",
}


def fetch_page_signals(url: str) -> dict:
    result = {
        "title": "", "description": "", "h1": "",
        "has_video": False, "fetched": False, "error": "",
    }
    if not url or not url.startswith("http"):
        return result
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=FETCH_TIMEOUT) as resp:
            raw = resp.read(200_000).decode("utf-8", errors="ignore")
        result["fetched"] = True
        result["has_video"] = bool(VIDEO_EVIDENCE.search(raw))
        title_match = re.search(r"<title[^>]*>([^<]+)</title>", raw, re.I)
        if title_match:
            result["title"] = html.unescape(title_match.group(1)).strip()
        desc_match = re.search(
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
            raw,
            re.I,
        )
        if not desc_match:
            desc_match = re.search(
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']',
                raw,
                re.I,
            )
        if desc_match:
            result["description"] = html.unescape(desc_match.group(1)).strip()
        h1_match = re.search(r"<h1[^>]*>([^<]+)</h1>", raw, re.I)
        if h1_match:
            result["h1"] = re.sub(r"<[^>]+>", "", h1_match.group(1)).strip()
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        result["error"] = str(exc)[:120]
    return result


def needs_render(page: dict) -> bool:
    """True when the plain fetch produced nothing a copy opener could use."""
    if not page.get("fetched"):
        return True
    return not (
        page.get("title") or page.get("description") or page.get("h1")
        or page.get("has_video")
    )


def _norm_tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(t) > 3}


def positioning_snippet(company: str, page: dict) -> str:
    """Extract a short positioning phrase safe to quote in copy.

    Rejects parts that repeat the company name (the body must never carry it),
    generic nav labels, over-long text, and anything with forbidden terms.
    """
    company_tokens = _norm_tokens(company)
    company_norm = re.sub(r"[^a-z0-9]", "", (company or "").lower())

    sources: list[str] = []
    for text in (page.get("h1"), page.get("title")):
        if text:
            sources.append(text)
    if page.get("description"):
        sources.extend(re.split(r"(?<=[.!?])\s+", page["description"]))

    for text in sources:
        text = re.sub(r"\s+", " ", text).strip()
        for part in re.split(r"\s*\|\s*|\s+[–—-]\s+|\s*•\s*|\s*::\s*", text):
            part = part.strip(" .,:;!-\"'")
            if not part:
                continue
            words = part.split()
            if not (3 <= len(words) <= 12):
                continue
            low = part.lower()
            if low in GENERIC_TITLE_PARTS:
                continue
            if "\u2026" in part or "..." in part:
                continue
            part_norm = re.sub(r"[^a-z0-9]", "", low)
            if company_norm and (company_norm in part_norm or part_norm in company_norm):
                continue
            if len(company_tokens & _norm_tokens(part)) >= 2:
                continue
            if not snippet_is_usable(part):
                continue
            return part[0].upper() + part[1:]
    return ""


def social_channel(row: dict) -> str:
    if (row.get("Youtube_URL") or "").strip():
        return "YouTube"
    if (row.get("Instagram_URL") or "").strip():
        return "Instagram"
    return ""


def snippet_is_usable(text: str) -> bool:
    """Reject prospect text that would poison our copy (banned / hard CTA)."""
    if not text or "..." in text or "\u2026" in text:
        return False
    if contains_forbidden(text):
        return False
    low = text.lower()
    return not any(p in low for p in HARD_CTA_PATTERNS)


# Generic org/venue words that are not distinctive enough to confirm a match.
_ORG_STOPWORDS = frozenset({
    "the", "and", "of", "for", "inc", "llc", "ltd", "co", "company", "corp",
    "group", "services", "service", "club", "center", "centre", "studio",
    "shop", "store", "spa", "salon", "boat", "auto", "motors", "team",
    "clinic", "agency", "solutions", "media", "usa", "international",
})


def linkedin_profile_matches(linkedin_url: str, posts: list[dict], company: str) -> bool:
    """Confirm the scraped LinkedIn profile plausibly belongs to this lead."""
    if not posts:
        return False
    distinctive = {
        t for t in _norm_tokens(company)
        if len(t) >= 4 and t not in _ORG_STOPWORDS
    }
    if not distinctive:
        return False
    handle_norm = re.sub(r"[^a-z0-9]", "", linkedin.li_handle(linkedin_url))
    author_norm = re.sub(r"[^a-z0-9]", "", (posts[0].get("author_name") or "").lower())
    haystack = handle_norm + " " + author_norm
    return any(tok in haystack for tok in distinctive)


def linkedin_topic(posts: list[dict], company: str = "") -> str:
    """Best clean topic phrase from the most recent posts (safe for copy)."""
    company_norm = re.sub(r"[^a-z0-9]", "", (company or "").lower())
    company_tokens = _norm_tokens(company)
    for post in posts:
        topic = (post.get("topic") or "").strip()
        if not snippet_is_usable(topic):
            continue
        topic_norm = re.sub(r"[^a-z0-9]", "", topic.lower())
        if company_norm and company_norm in topic_norm:
            continue
        if len(company_tokens & _norm_tokens(topic)) >= 2:
            continue
        return topic
    return ""


def classify_evidence(row: dict, page: dict, snippet: str, li_topic: str = "") -> str:
    if li_topic:
        return "linkedin_posts"
    if page.get("fetched") and page.get("has_video"):
        return "site_video"
    if page.get("fetched") and not page.get("has_video") and social_channel(row):
        return "social_video"
    if snippet:
        return "positioning"
    return "weak"


def build_signal(
    row: dict,
    page: dict,
    snippet: str,
    evidence: str,
    li_posts: list[dict] | None = None,
    li_topic: str = "",
) -> tuple[str, str, str]:
    """Return (research_signal, research_notes, signal_strength)."""
    li_posts = li_posts or []
    city = (row.get("City") or "").strip()
    state = (row.get("State") or "").strip()
    location = ", ".join(p for p in [city, state] if p)
    segment = row.get("aevora_segment", "low_fit")
    channel = social_channel(row)

    parts = []
    if li_topic:
        parts.append(f'recent LinkedIn post: "{li_topic}"')
    if snippet:
        parts.append(f'site positioning: "{snippet}"')
    if page.get("fetched"):
        parts.append(f"video on site: {'yes' if page.get('has_video') else 'no'}")
    else:
        parts.append("video on site: unknown (fetch failed)")
    if channel:
        parts.append(f"{channel} linked")
    if location:
        parts.append(location)
    signal = "; ".join(parts)

    strength = "strong" if evidence != "weak" else "weak"

    fetched_note = f"Website fetched: {page.get('fetched', False)}"
    if page.get("rendered"):
        fetched_note += " (headless render)"
    notes_parts = [
        f"Segment: {segment}",
        fetched_note,
        f"Signal strength: {strength}",
    ]
    if li_posts:
        last = li_posts[0]
        notes_parts.append(
            f"LinkedIn posts scraped: {len(li_posts)} "
            f"(latest {last.get('posted_ago', '?')}, "
            f"{last.get('likes', 0)} likes)"
        )
    if page.get("description"):
        meta = re.sub(r"\s+", " ", page["description"]).strip()
        notes_parts.append(f"Meta: {meta[:120]}")
    if page.get("error"):
        notes_parts.append(f"Fetch error: {page['error']}")
    linkedin_url = (row.get("Linkedin_URL") or "").strip()
    if linkedin_url:
        notes_parts.append(f"LinkedIn in CSV: {linkedin_url}")

    return signal, "; ".join(notes_parts), strength


def research_lead(
    row: dict,
    li_scraped: dict | None = None,
    *,
    renderer: PageRenderer | None = None,
    render_fallback: bool = True,
    throttle_s: float = 0.15,
) -> dict:
    website = (row.get("Website") or "").strip()
    page = fetch_page_signals(website)
    if render_fallback and renderer is not None and website and needs_render(page):
        rendered = renderer.render(website)
        if rendered.get("fetched"):
            page = rendered
    company = row.get("company_name") or row.get("Name", "")
    snippet = positioning_snippet(company, page)

    linkedin_url = (row.get("Linkedin_URL") or "").strip()
    li_posts = []
    li_mismatch = False
    if li_scraped is not None and linkedin_url:
        li_posts = linkedin.posts_for_url(linkedin_url, li_scraped)
        if li_posts and not linkedin_profile_matches(linkedin_url, li_posts, company):
            li_mismatch = True
            li_posts = []
    li_topic = linkedin_topic(li_posts, company)

    evidence = classify_evidence(row, page, snippet, li_topic)
    signal, notes, strength = build_signal(row, page, snippet, evidence, li_posts, li_topic)
    if li_mismatch:
        notes += "; LinkedIn in CSV did not match company name (posts ignored)"
    if throttle_s:
        time.sleep(throttle_s)
    return {
        "row_index": int(row.get("row_index", 0)),
        "first_name": row.get("first_name", ""),
        "last_name": row.get("last_name", ""),
        "title": row.get("title", ""),
        "company": company,
        "email": row.get("primary_email", ""),
        "website": website,
        "linkedin": (row.get("Linkedin_URL") or "").strip(),
        "twitter": (row.get("Twitter_URL") or "").strip(),
        "facebook": (row.get("Facebook_URL") or "").strip(),
        "outreach_tier": "company",
        "aevora_segment": row.get("aevora_segment", ""),
        "fit_score": row.get("fit_score", ""),
        "research_signal": signal,
        "research_notes": notes,
        "signal_strength": strength,
        "evidence": evidence,
        "snippet": snippet,
        "has_video_on_site": bool(page.get("has_video")),
        "social_channel": social_channel(row),
        "linkedin_topic": li_topic,
        "linkedin_posts_count": len(li_posts),
        "linkedin_last_post": li_posts[0].get("date", "") if li_posts else "",
        "linkedin_posts": li_posts,
    }
