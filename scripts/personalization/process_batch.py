#!/usr/bin/env python3
"""Research leads and generate evidence-based, variant-driven copy for one batch.

Copy contract (GMB / company-tier lists):
- Greeting is always "Hi," — no person name, no company name anywhere in the body.
- Email structure: observed issue -> our solution -> soft CTA.
- Openers, solutions, and CTAs are drawn from variant pools selected
  deterministically per lead (stable re-runs, campaign-wide variety).
- Leads with fit_score == "skip" are excluded from copy entirely.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from personalization import artifacts, linkedin_apify  # noqa: E402
from personalization.build_enriched import build_batch  # noqa: E402
from personalization.manifest_lock import update_batch_status  # noqa: E402
from personalization.merge_enriched import merge_enriched  # noqa: E402
from personalization.qa import (  # noqa: E402
    HARD_CTA_PATTERNS,
    contains_forbidden,
    qa,
    subject_has_spam,
)
from personalization.sanitize import sanitize_email  # noqa: E402
from personalization.subjects import build_subject  # noqa: E402

USER_AGENT = "Mozilla/5.0 (compatible; AevoraLeadResearch/1.0)"
FETCH_TIMEOUT = 12

# Headless-render fallback for JS-built sites (Wix, Squarespace, React).
# Disable with --no-render if node/playwright is unavailable.
RENDER_FALLBACK = True
RENDER_SCRIPT = Path(__file__).with_name("render_page.js")
RENDER_TIMEOUT_S = 45

# LinkedIn recent-post enrichment via Apify. Disable with --no-linkedin.
LINKEDIN_ENRICH = True
LINKEDIN_MAX_POSTS = 2

VIDEO_EVIDENCE = re.compile(
    r"youtube\.com/embed|youtube-nocookie\.com|player\.vimeo\.com|fast\.wistia"
    r"|<video\b|\.mp4\b|loom\.com/embed",
    re.I,
)

GENERIC_TITLE_PARTS = {
    "home", "homepage", "welcome", "about", "about us", "contact", "contact us",
    "official site", "official website", "index",
}

# ---------------------------------------------------------------------------
# Variant pools. All copy must stay clean of banned/spam/brand-forbidden terms
# and em dashes (qa.py enforces). Never mention the company name.
# ---------------------------------------------------------------------------

OPENERS = {
    "linkedin_posts": [
        "Saw your recent LinkedIn post (\"{snippet}\"), so video is clearly "
        "already part of how you show up. The lever from here is usually the "
        "finish, not more posting.",
        "Your recent LinkedIn post (\"{snippet}\") caught my eye. Teams posting "
        "that consistently usually gain the most from sharper finishing on the "
        "video side.",
    ],
    "site_video": [
        "Noticed your site already runs video, which puts you ahead of most "
        "{peer} in {loc}. The gap is usually the finish: pacing, hooks, and "
        "captions built for each platform.",
        "Your site embeds video, and that is rarer than it should be for {peer} "
        "in {loc}. What separates a view from an inquiry is almost always the "
        "finishing, not the footage.",
    ],
    "social_video": [
        "Saw the {channel} link on your listing, but the site itself does not "
        "lead with video, and that is usually the first place buyers look.",
        "You are set up on {channel}, yet the website carries no video. For "
        "{peer}, that is often the gap between a visit and an inquiry.",
    ],
    "positioning": [
        "Your site leads with \"{snippet}\", which is clear positioning that "
        "most {peer} never back up with finished video.",
        "\"{snippet}\" is a strong promise on your homepage. Video is the "
        "fastest way to make it feel real, and most {peer} skip that step.",
    ],
    "weak": [
        "Most {peer} in {loc} sit on usable footage already: walkthroughs, "
        "events, phone clips that never become finished video.",
        "Few {peer} in {loc} publish finished video, which makes it one of the "
        "cheapest ways to stand out right now.",
    ],
}

SEGMENT_COPY = {
    "creative_marketing": {
        "solutions": [
            "We plug in as a white-label finishing bench: retention edits, motion "
            "graphics, and hook variants on your clients' footage, delivered "
            "under your name.",
            "We handle overflow post-production on client footage, retention "
            "pacing, motion graphics, and A/B hook variants, so deliverables "
            "ship without adding headcount.",
        ],
        "second_angle": [
            "From one client master we typically deliver ten platform-native "
            "shorts plus twenty hook variations for paid testing.",
            "Agencies use us to turn one master edit into a full short-form "
            "package: paced cuts, captions, and test-ready hooks.",
        ],
    },
    "real_estate": {
        "solutions": [
            "We finish walkthrough and event footage you already shoot: pacing, "
            "captions, and short reels cut from one master. No new shoot needed.",
            "We turn existing walkthrough footage into listing reels and "
            "partner-facing cuts that match a premium market position.",
        ],
        "second_angle": [
            "One walkthrough typically becomes a hero tour plus a set of 15-30 "
            "second reels sized for Instagram and YouTube.",
            "Listings with paced, hook-led reels tend to earn attention long "
            "before the floor plan gets read.",
        ],
    },
    "professional_services": {
        "solutions": [
            "We turn seminars, webinars, and partner events you already record "
            "into polished authority clips: clean cuts, captions, and motion "
            "graphics.",
            "We take recorded talks and client education sessions and finish "
            "them into short, credible clips referral partners actually watch.",
        ],
        "second_angle": [
            "One recorded seminar usually yields a month of short authority "
            "clips without anyone on your team touching an editor.",
            "Polished educational clips tend to do the trust-building that case "
            "results alone cannot.",
        ],
    },
    "medical_aesthetic": {
        "solutions": [
            "We finish provider and education footage you already capture: "
            "retention pacing, clean motion graphics, and platform-ready cuts.",
            "We turn treatment-room and education footage into clear, "
            "professional explainers that help patients decide.",
        ],
        "second_angle": [
            "Clear procedure explainers tend to convert consult inquiries better "
            "than stock photos or static galleries.",
            "One filming session usually becomes a full month of education clips "
            "once the finishing is handled.",
        ],
    },
    "software_tech": {
        "solutions": [
            "We turn screen recordings into motion-led product explainers with "
            "hook variants for paid and organic tests.",
            "We finish demo captures into tight explainers where the UI motion "
            "makes the value obvious in the first ten seconds.",
        ],
        "second_angle": [
            "One demo capture typically becomes a launch explainer plus a set of "
            "feature clips for every channel.",
            "Demos convert when the first ten seconds show the outcome, not the "
            "onboarding.",
        ],
    },
    "home_design": {
        "solutions": [
            "We finish site and portfolio footage you already have: cinematic "
            "pacing, color grade, and hook-led reels cut from one master.",
            "We turn raw project footage into reels that look as considered as "
            "the finished build.",
        ],
        "second_angle": [
            "One site capture usually becomes a hero reveal plus platform-native "
            "reels for the same project.",
            "High-ticket clients often judge the build quality by the reel "
            "quality before they ever call.",
        ],
    },
    "luxury_retail": {
        "solutions": [
            "We finish product footage into retention-first reels and ad "
            "variants built for testing, not catalog slideshows.",
            "We turn supplied product footage into short, crave-led cuts sized "
            "for social and paid placements.",
        ],
        "second_angle": [
            "One product shoot typically becomes a season of reels plus ad "
            "variants for A/B testing.",
            "Product video sells when it creates want in the first three "
            "seconds; slideshows rarely do.",
        ],
    },
    "marine_auto_lifestyle": {
        "solutions": [
            "We finish walkaround and showroom footage into cinematic reels that "
            "match the price point of the inventory.",
            "We turn existing inventory footage into showcase cuts and ad hooks "
            "buyers at that ticket size expect.",
        ],
        "second_angle": [
            "One walkaround usually becomes a hero showcase plus short cuts for "
            "every listing channel.",
            "High-ticket inventory moves faster when the video matches the "
            "sticker.",
        ],
    },
    "auto_services": {
        "solutions": [
            "We turn the before/after footage you already shoot into paced "
            "transformation reels: clean cuts, captions, and hooks built for "
            "each platform.",
            "We finish shop footage into short before/after reels that show the "
            "transformation clearly, the format that pulls the most saves and "
            "shares.",
        ],
        "second_angle": [
            "One detail or wrap job usually becomes a reveal reel plus a set of "
            "short cuts sized for Instagram and TikTok.",
            "Transformation reels tend to book more jobs than static gallery "
            "photos because the result lands in the first two seconds.",
        ],
    },
    "hospitality_events": {
        "solutions": [
            "We finish event footage into highlight reels and platform-native "
            "shorts while the moment still matters.",
            "We turn raw event coverage into recap films and social cuts that "
            "extend an event's reach for weeks.",
        ],
        "second_angle": [
            "One event capture usually becomes a recap film plus a set of shorts "
            "for every channel.",
            "Recap video finished within the week tends to outperform raw clips "
            "posted late.",
        ],
    },
    "low_fit": {
        "solutions": [
            "We finish footage you already have, phone clips, events, "
            "walkthroughs, with retention pacing and clean graphics.",
            "We handle the edit and finishing on media you provide, so "
            "publishing video stops depending on spare time.",
        ],
        "second_angle": [
            "Most teams sit on more usable footage than they think; finishing is "
            "the missing step.",
            "One batch of existing clips is usually enough for a month of "
            "finished posts.",
        ],
    },
}

CTA_POOLS = {
    1: [
        "Interested in a sample edit from one clip you already have?",
        "Worth a short sample cut from your existing footage?",
        "Want a sample edit matched to your style of work?",
    ],
    2: [
        "Want an example of how we'd structure that?",
        "Open to one before/after example?",
        "Useful if I send a short example matched to your niche?",
    ],
    3: [
        "When footage gets shot on your side, who finishes it, or does it wait?",
        "Open to a ten-minute call to see if this maps to how you work?",
        "Want one sample cut so you can judge the finish directly?",
    ],
}

CLOSERS = [
    "Last note from me: most teams we work with didn't lack footage, they "
    "lacked finishing time.",
    "Closing the loop here. Publishing finished video consistently is nearly "
    "always a bandwidth problem, not a content problem.",
]

SUPPORT_LINES = [
    "If it's backlog, we run as a quiet post-production bench on footage you "
    "supply.",
    "If it's bandwidth, that's exactly the gap we fill: post-production only, "
    "on your media.",
]


def _pick(pool: list[str], key: str, salt: str) -> tuple[str, int]:
    digest = int(hashlib.md5(f"{salt}:{key}".encode()).hexdigest(), 16)
    idx = digest % len(pool)
    return pool[idx], idx


# ---------------------------------------------------------------------------
# Research
# ---------------------------------------------------------------------------


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


def render_page_signals(url: str) -> dict:
    """Render the page with headless Chromium (node + playwright) and parse signals."""
    result = {
        "title": "", "description": "", "h1": "",
        "has_video": False, "fetched": False, "error": "", "rendered": True,
    }
    if not url or not url.startswith("http") or not RENDER_SCRIPT.is_file():
        result["error"] = "render unavailable"
        return result
    try:
        proc = subprocess.run(
            ["node", str(RENDER_SCRIPT), url],
            capture_output=True,
            text=True,
            timeout=RENDER_TIMEOUT_S,
            cwd=ROOT,
        )
        data = json.loads(proc.stdout.strip() or "{}")
        for key in ("title", "description", "h1", "has_video", "fetched", "error"):
            if key in data:
                result[key] = data[key]
    except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError) as exc:
        result["error"] = f"render failed: {str(exc)[:100]}"
    return result


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
        # Meta descriptions run long; consider sentence by sentence.
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
            if company_norm and (
                company_norm in part_norm or part_norm in company_norm
            ):
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
    """Confirm the scraped LinkedIn profile plausibly belongs to this lead.

    Source lists sometimes attach the wrong LinkedIn URL to a business. Require
    a distinctive company token (>=4 chars, not a generic org word) to appear in
    the LinkedIn handle or the post author's name; otherwise treat as untrusted.
    """
    if not posts:
        return False
    distinctive = {
        t for t in _norm_tokens(company)
        if len(t) >= 4 and t not in _ORG_STOPWORDS
    }
    if not distinctive:
        # Company name too generic to verify; only trust an exact handle echo.
        return False
    handle_norm = re.sub(r"[^a-z0-9]", "", linkedin_apify.li_handle(linkedin_url))
    author_norm = re.sub(r"[^a-z0-9]", "", (posts[0].get("author_name") or "").lower())
    haystack = handle_norm + " " + author_norm
    return any(tok in haystack for tok in distinctive)


def linkedin_topic(posts: list[dict], company: str = "") -> str:
    """Best clean topic phrase from the most recent posts (safe for copy).

    Rejects topics that carry the company's own name (would trip the
    company-name-in-body rule and read like mail merge).
    """
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
    """Return (research_signal, research_notes, signal_strength).

    research_signal is an internal CSV field, never pasted into copy.
    signal_strength mirrors what the copy can actually use: strong only when
    a verifiable opener exists (LinkedIn post, site video, social gap, quote).
    """
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
    linkedin = (row.get("Linkedin_URL") or "").strip()
    if linkedin:
        notes_parts.append(f"LinkedIn in CSV: {linkedin}")

    return signal, "; ".join(notes_parts), strength


def research_lead(row: dict, li_scraped: dict | None = None) -> dict:
    website = (row.get("Website") or "").strip()
    page = fetch_page_signals(website)
    if RENDER_FALLBACK and website and needs_render(page):
        rendered = render_page_signals(website)
        if rendered.get("fetched"):
            page = rendered
    company = row.get("company_name") or row.get("Name", "")
    snippet = positioning_snippet(company, page)

    linkedin_url = (row.get("Linkedin_URL") or "").strip()
    li_posts = []
    li_mismatch = False
    if li_scraped is not None and linkedin_url:
        li_posts = linkedin_apify.posts_for_url(linkedin_url, li_scraped)
        if li_posts and not linkedin_profile_matches(linkedin_url, li_posts, company):
            # Wrong LinkedIn attached in the source list — don't use its posts.
            li_mismatch = True
            li_posts = []
    li_topic = linkedin_topic(li_posts, company)

    evidence = classify_evidence(row, page, snippet, li_topic)
    signal, notes, strength = build_signal(
        row, page, snippet, evidence, li_posts, li_topic
    )
    if li_mismatch:
        notes += "; LinkedIn in CSV did not match company name (posts ignored)"
    time.sleep(0.15)
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


# ---------------------------------------------------------------------------
# Copy
# ---------------------------------------------------------------------------


def peer_phrase(category: str) -> str:
    cat = (category or "").strip().lower()
    return f"{cat} teams" if cat else "teams in your space"


def generate_sequence(row: dict, research: dict) -> tuple[list[tuple[str, str]], str]:
    """Build the 3-email sequence. Returns (sequence, copy_variant)."""
    email = research.get("email") or row.get("primary_email", "")
    segment = row.get("aevora_segment", "low_fit")
    seg_copy = SEGMENT_COPY.get(segment, SEGMENT_COPY["low_fit"])
    evidence = research.get("evidence", "weak")
    snippet = research.get("snippet", "")
    li_topic = research.get("linkedin_topic", "")
    channel = research.get("social_channel", "") or "social"
    company = (row.get("company_name") or research.get("company") or "").strip()
    city = (row.get("City") or "").strip()
    state = (row.get("State") or "").strip()
    loc = city or state or "your market"
    # If the company name was parsed as its city, injecting that location would
    # leak the company name into the body — use the state or a neutral phrase.
    if company and loc and loc.lower() in company.lower():
        loc = state if (state and state.lower() not in company.lower()) else "your area"
    peer = peer_phrase(row.get("First_category", ""))

    greeting = "Hi,"

    opener_tmpl, o_idx = _pick(OPENERS[evidence], email, "opener")
    opener = opener_tmpl.format(
        peer=peer, loc=loc, snippet=(li_topic if evidence == "linkedin_posts" else snippet),
        channel=channel,
    )

    solution, s_idx = _pick(seg_copy["solutions"], email, "solution")
    alt_solution = seg_copy["solutions"][(s_idx + 1) % len(seg_copy["solutions"])]
    angle2, a_idx = _pick(seg_copy["second_angle"], email, "angle2")
    closer, cl_idx = _pick(CLOSERS, email, "closer")
    support, su_idx = _pick(SUPPORT_LINES, email, "support")
    cta1, c1 = _pick(CTA_POOLS[1], email, "cta1")
    cta2, c2 = _pick(CTA_POOLS[2], email, "cta2")
    cta3, c3 = _pick(CTA_POOLS[3], email, "cta3")

    plans = [
        [opener, solution, cta1],
        [angle2, alt_solution, cta2],
        [closer, support, cta3],
    ]

    variant = f"{evidence}.o{o_idx}s{s_idx}a{a_idx}cl{cl_idx}su{su_idx}c{c1}{c2}{c3}"

    hook = (li_topic if evidence == "linkedin_posts" else snippet) or ""
    sequence: list[tuple[str, str]] = []
    used_subjects: set[str] = set()
    for step, parts in enumerate(plans, start=1):
        body = trim_body(greeting, parts[:-1], parts[-1])
        subj = build_subject(
            row,
            research.get("research_signal", ""),
            segment,
            step,
            used_subjects=used_subjects,
            hook=hook,
            key=email,
        )
        sequence.append((subj, body))

    return sequence, variant


def trim_body(greeting: str, parts: list[str], cta: str, max_words: int = 100) -> str:
    body_parts = parts[:]
    while body_parts:
        body = "\n\n".join([greeting] + body_parts + [cta])
        if len(re.findall(r"\b\w+\b", body)) <= max_words:
            return body
        if len(body_parts) > 1:
            body_parts = body_parts[:-1]
        else:
            short = body_parts[0]
            words = short.split()
            body_parts[0] = " ".join(words[: max(8, len(words) - 5)])
    return "\n\n".join([greeting, cta])


def fix_sequence(
    sequence: list[tuple[str, str]],
    row: dict,
    research: dict,
) -> list[tuple[str, str]]:
    segment = row.get("aevora_segment", "low_fit")
    company = research.get("company", "")
    signal = research.get("research_signal", "")
    key = research.get("email") or row.get("primary_email", "")
    fixed = []
    used_subjects: set[str] = set()
    for step, (subj, body) in enumerate(sequence, start=1):
        if subject_has_spam(subj) or len(subj) > 60 or subj in used_subjects:
            subj = build_subject(
                row, signal, segment, step, used_subjects=used_subjects, key=key
            )
        if len(subj) > 60:
            cut = subj[:60]
            subj = cut[: cut.rfind(" ")] if " " in cut else cut
        body = body.replace("—", "-").replace("\u2026", "")
        subj, body = sanitize_email(subj, body)
        q = qa(subj, body, company)
        if not q["pass"] and q["word_count"] > 100:
            lines = body.split("\n\n")
            while len(lines) > 2 and qa(subj, "\n\n".join(lines), company)["word_count"] > 100:
                lines.pop(-2)
            body = "\n\n".join(lines)
        used_subjects.add(subj)
        fixed.append((subj, body))
    return fixed


# ---------------------------------------------------------------------------
# Batch driver
# ---------------------------------------------------------------------------


def merged_output_path(source: Path, prefix: str | None = None) -> Path:
    """Stable single merged file per run: leads/<prefix>-enriched.csv.

    With a prefix this is one file per list. Without one it falls back to the
    old source-stem derivation, which truncates at the first digit — so
    ``july-6-delta-normalized``, ``july-7-...`` and ``july-8-...`` all resolved
    to ``leads/july-enriched.csv``. Callers that know their prefix should pass
    it; the pipeline does.
    """
    if prefix:
        return artifacts.merged_csv(prefix)
    stem = source.stem.lower().replace("-38k", "")
    for suffix in ("-with-email", "-cleaned", "-verified", "-valid", "-normalized"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    parts = []
    for part in stem.split("-"):
        if part.isdigit() or part in {"cleaned", "verified", "valid", "normalized", "with", "email"}:
            break
        parts.append(part)
    campaign = "-".join(parts) or "mixed"
    return ROOT / "leads" / f"{campaign}-enriched.csv"


def process_batch(
    batch_id: str,
    source: Path,
    manifest_path: Path,
    campaigns_dir: Path | None = None,
    skip_build: bool = False,
    auto_merge: bool = True,
) -> dict:
    campaigns_dir = campaigns_dir or ROOT / "campaigns"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    batch = next((b for b in manifest["batches"] if b["id"] == batch_id), None)
    if not batch:
        raise SystemExit(f"Batch {batch_id} not found in manifest")

    # Everything this run writes is named after the manifest's prefix, so two
    # lists processing at once never touch the same file.
    prefix = artifacts.clean_prefix(
        manifest.get("prefix") or artifacts.prefix_from_manifest_name(manifest_path)
    )

    with source.open(newline="", encoding="utf-8") as handle:
        all_rows = list(csv.DictReader(handle))

    # Every lead in the list gets copy — no fit-based exclusion.
    batch_rows = [all_rows[i] for i in batch["rows"]]

    # Pre-scrape LinkedIn posts for every lead that has a LinkedIn URL (one
    # batched Apify call, cached per handle so re-runs never re-pay).
    li_scraped: dict = {}
    if LINKEDIN_ENRICH:
        li_urls = [
            (r.get("Linkedin_URL") or "").strip()
            for r in batch_rows
            if (r.get("Linkedin_URL") or "").strip()
        ]
        if li_urls:
            try:
                li_scraped = linkedin_apify.scrape_profiles(
                    li_urls, max_posts=LINKEDIN_MAX_POSTS
                )
                found = sum(1 for v in li_scraped.values() if v)
                print(
                    f"Batch {batch_id}: LinkedIn URLs {len(li_urls)}, "
                    f"profiles with posts {found}"
                )
            except SystemExit as exc:
                print(f"Batch {batch_id}: LinkedIn enrichment skipped ({exc})")
                li_scraped = {}

    research_out = []
    copy_out = {}

    for row in batch_rows:
        item = research_lead(row, li_scraped)
        seq, variant = generate_sequence(row, item)
        seq = fix_sequence(seq, row, item)
        item["copy_variant"] = variant
        research_out.append(item)
        copy_out[item["email"]] = [[s, b] for s, b in seq]

    research_path = artifacts.research_json(prefix, batch_id, campaigns_dir)
    copy_path = artifacts.copy_json(prefix, batch_id, campaigns_dir)
    campaigns_dir.mkdir(parents=True, exist_ok=True)
    research_path.write_text(json.dumps(research_out, indent=2), encoding="utf-8")
    copy_path.write_text(json.dumps(copy_out, indent=2), encoding="utf-8")

    update_batch_status(manifest_path, batch_id, "copy_done")

    result = {
        "batch_id": batch_id,
        "leads": len(batch_rows),
        "research": str(research_path),
        "copy": str(copy_path),
    }

    if not batch_rows:
        update_batch_status(manifest_path, batch_id, "exported")
        result["note"] = "batch has no rows; nothing exported"
        return result

    if not skip_build:
        build_result = build_batch(source, research_path, copy_path, batch_id, prefix=prefix)
        update_batch_status(manifest_path, batch_id, "exported")
        result.update(build_result)

        if auto_merge:
            merged_path = merged_output_path(source, prefix)
            merged_rows = merge_enriched(output_path=merged_path, manifest_path=manifest_path)
            result["merged"] = str(merged_path)
            result["merged_rows"] = merged_rows

    return result


def main() -> None:
    global RENDER_FALLBACK, LINKEDIN_ENRICH
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--source", default="leads/all-leads-with-email-normalized.csv")
    parser.add_argument("--manifest", default=str(artifacts.manifest_path().relative_to(ROOT)))
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument(
        "--no-render",
        action="store_true",
        help="Disable the headless-browser fallback for JS-rendered sites",
    )
    parser.add_argument(
        "--no-linkedin",
        action="store_true",
        help="Disable Apify LinkedIn recent-post enrichment",
    )
    args = parser.parse_args()

    if args.no_render:
        RENDER_FALLBACK = False
    if args.no_linkedin:
        LINKEDIN_ENRICH = False

    source = Path(args.source)
    manifest = Path(args.manifest)
    if not source.is_absolute():
        source = ROOT / source
    if not manifest.is_absolute():
        manifest = ROOT / manifest

    result = process_batch(args.batch_id, source, manifest, skip_build=args.skip_build)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
