#!/usr/bin/env python3
"""Hand-tuned research + copy generator for batches 16-22 (CSV indices 307-445).

Replaces the templatey bulk_generate_remaining.py output with lead-specific signals
and varied role templates pulled from live company research (May 2026).

Run: python3 scripts/draft_remaining_batches.py
Then: python3 scripts/build_pilot_batch.py --batch N  (for N in 16..22)
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "leads" / "Real-Estate-USA-500.csv"
START_INDEX = 307
FIRST_BATCH = 16
BATCH_SIZE = 20

# Batch 23 backfills the 7 leads at source indices 20-26 that the original
# batch 2 design dropped (kept owner-only contacts at multi-contact firms).
BATCH23_INDICES = [20, 21, 22, 23, 24, 25, 26]
BATCH23_NUMBER = 23

BANNED = [
    "hope this email finds you well",
    "impressive linkedin",
    "pick your brain",
    "circle back",
    "touch base",
    "deep dive",
    "\u2014",
]

# ---------------------------------------------------------------------------
# Company research (sourced live from kvstitle.com, libtitle.com, advocus.com,
# premiermove.com, vaneatonromero.com, texastitle.com, lawfirmsuites.com,
# horizonresolutions.com plus public press May 2026).
# ---------------------------------------------------------------------------
COMPANIES = {
    "KVS TITLE": {
        "site": "kvstitle.com",
        "shorthand": "KVS",
        "facts": [
            "KVS attorneys average 14+ years of settlement work across 70,000+ closings",
            "KVS staffs processors at roughly half competitor caseloads so each file gets more attention",
            "KVS pushes proactive client comms from intake to recordation across MD, DC, and VA",
            "Hans Wydler (500M career sales) calls KVS his go-to settlement partner for over a decade",
            "Seven KVS offices span Baltimore, Kensington, Rockville, Bethesda, DC, Chevy Chase, Gaithersburg",
        ],
        "blog_keywords": [
            "wire fraud", "timeline transparency", "settlement explainers", "first-time buyer education",
        ],
    },
    "Liberty Title & Escrow": {
        "site": "libtitle.com",
        "shorthand": "Liberty",
        "facts": [
            "Liberty Title runs a multistate footprint across AR, IL, IN, ME, MD, NH, RI, TX, VA, LA, UT with regional Account Reps",
            "libtitle.com pushes recent blog posts on wire fraud, title theft, 1031 exchanges, and remote closings",
            "Liberty pairs national settlement capacity with single-point-of-contact closings for lenders and realtors",
            "Liberty stacks marketing tools (Prospect Now, Real Geeks, CINC, Reach 150, TRID Calendar) for partner enablement",
            "Liberty positions as a neighborhood provider doing national volume, not a faceless underwriter",
        ],
        "blog_keywords": ["wire fraud", "title theft", "1031 exchanges", "remote closings", "realtor enablement"],
    },
    "Advocus National Title Insurance Company": {
        "site": "advocus.com",
        "shorthand": "Advocus",
        "facts": [
            "Advocus (formerly ATG, 60-year history) advocates for the attorney's role in real estate closings",
            "Demotech A' (A Prime) Financial Stability Rating since 1995, plus Kroll A- and Lloyd's reinsurance backing",
            "Advocus tracks impact in capitol visits: 154 state house trips, 46 to DC, 31 calls to action",
            "Advocus supports its lawyer-agents instead of competing with them, with CLE and TRID-aware tooling",
            "Advocus operations stretch from Chicago HQ to Texas, Wisconsin, Arizona, and Minnesota satellite work",
        ],
        "blog_keywords": ["attorney advocacy", "wire fraud", "title insurance", "TRID compliance", "CLE"],
    },
    "Coldwell Banker Professional REALTORS\u00ae": {
        "site": "cbnow.com",
        "shorthand": "Coldwell Banker Now",
        "facts": [
            "Coldwell Banker Now (rebranding into Coldwell Banker Premier) combined $600M Hampton Roads volume in 2023",
            "Five offices cover Chesapeake, Franklin, Newport News, Virginia Beach, and Williamsburg",
            "Founder Dorcas Helfant-Browning was the first female NAR president (1992); Tim Gifford and Rick West co-own the shop",
            "Coldwell Banker Premier brings in-house relocation, mortgage, commercial, auction, and settlement services",
            "Hampton Roads agents work the REIN MLS where listing-video quality drives showings and offers",
        ],
        "blog_keywords": ["Hampton Roads listings", "relocation buyers", "merger transition", "REIN MLS"],
    },
    "Van Eaton & Romero Realtors": {
        "site": "vaneatonromero.com",
        "shorthand": "Van Eaton & Romero",
        "facts": [
            "Van Eaton & Romero holds roughly 34 percent share of the Lafayette residential market since founding in 1977",
            "98 percent customer approval rating and a REALTrends top firm placement for 10+ straight years",
            "Latter & Blum parent network plugs Lafayette listings into a 32-office Gulf South distribution chain",
            "Acadiana lifestyle (River Ranch, Youngsville, Maurice rural acreage) sells visually before it sells on paper",
            "Relocation department is nationally awarded; out-of-market buyers decide off photo and video first",
        ],
        "blog_keywords": ["Acadiana lifestyle", "relocation", "River Ranch listings", "Lafayette buyer video"],
    },
    "Texas Title": {
        "site": "texastitle.com",
        "shorthand": "Texas Title",
        "facts": [
            "Texas Title was founded in 2013 by attorneys Robert Karlseng and Claude Rich, licensed in 48 counties (90% of state population)",
            "Frisco-based title plant runs centralized order processing with branches across the state and fee attorney closings",
            "Texas Title One App surfaces seller net sheets, title quotes, and buyer estimates for partner agents",
            "Education and training calendars are run out of branch offices and the marketing team for realtor partners",
            "50-plus years of executive leadership weight on the residential title insurance side",
        ],
        "blog_keywords": ["seller net sheet education", "wire fraud", "Texas realtor enablement"],
    },
    "Lawyers Title": {
        "site": "ltic.com",
        "shorthand": "Lawyers Title",
        "facts": [
            "Lawyers Title is a national Fidelity-backed title insurance and escrow network spanning major US metros",
            "Branch offices balance commercial and residential closings with attorney-led service",
            "Amarillo, Houston, San Antonio, LA Bay Area, and Cincinnati offices each maintain local-market positioning",
        ],
        "blog_keywords": ["commercial closings", "wire fraud", "branch enablement"],
    },
    "LandAmerica Lawyers Title": {
        "site": "ltic.com",
        "shorthand": "Lawyers Title",
        "facts": [
            "LandAmerica Lawyers Title sits inside the broader Fidelity Lawyers Title network",
            "Branch-level escrow officers anchor relationship continuity with lender and realtor partners",
        ],
        "blog_keywords": ["wire fraud", "branch enablement"],
    },
    "Law Firm Suites": {
        "site": "lawfirmsuites.com",
        "shorthand": "Law Firm Suites",
        "facts": [
            "Law Firm Suites runs Manhattan shared offices and virtual law office rentals exclusively for attorneys",
            "The community is built on attorney referrals between members, not sterile coworking",
            "Conference rooms host trial prep, closings, and depositions for solo and small-firm members",
            "Founders practice law themselves, so the offering is built around attorney confidentiality and professionalism",
        ],
        "blog_keywords": ["attorney referrals", "solo law marketing", "office tour video"],
    },
    "HORIZON REAL ESTATE SOLUTIONS": {
        "site": "horizonresolutions.com",
        "shorthand": "Horizon",
        "facts": [
            "Vernell V. Roberts runs Horizon Real Estate Solutions out of Fort Lauderdale with waterfront, golf course, and foreclosure-rescue specialty",
            "Site testimonials lean heavy on rescue-from-foreclosure stories and over-asking offers in weeks",
            "Horizon brand mixes professional service with a hand-held client experience for sellers under pressure",
        ],
        "blog_keywords": ["foreclosure rescue", "waterfront listings", "South Florida video"],
    },
    # ---- Batch 23 firms (leftovers from batch 2 selection) ----
    "Lawyers Abstract Company of Westmoreland County": {
        "site": "lacwest.com",
        "shorthand": "Lawyers Abstract",
        "facts": [
            "Lawyers Abstract Company of Westmoreland County (lacwest.com) runs title insurance and real estate settlements out of Greensburg PA",
            "A six-person team covers Westmoreland County settlements with attorney-led title search work",
            "Pittsburgh-area realtor and lender partners route settlements through the Greensburg desk",
        ],
        "blog_keywords": ["Westmoreland County closings", "PA settlement explainers"],
    },
    "Progressive Title": {
        "site": "progtitle.com",
        "shorthand": "Progressive Title",
        "facts": [
            "Progressive Title (progtitle.com) is an independent Maryland/DC/Virginia title shop run out of Arnold MD with in-house abstractors",
            "Site emphasizes fast settlements, competitive rates, a title quote calculator, and conflict-free representation",
            "An eight-person team handles purchases, refinances, and title insurance across MD, DC, and VA",
            "Branch reach into West Palm Beach FL stretches the Arnold MD HQ into a multi-market footprint",
        ],
        "blog_keywords": ["wire fraud", "title quote calculator", "MD/DC/VA settlement explainers"],
    },
    "Able Title Agency": {
        "site": "able-title.com",
        "shorthand": "Able Title",
        "facts": [
            "Able Title Agency (able-title.com) is a full-service New Jersey title shop covering residential and commercial closings out of Hoboken",
            "Site stresses smooth real estate closings on purchases and refinances, plus a transfer fee calculator and attorney-recommended workflow",
            "A six-person Hoboken team handles title underwriting, closings, and online client resources for NJ realtors and lenders",
        ],
        "blog_keywords": ["NJ closings", "transfer fee calculator", "real estate closing explainers"],
    },
    "Digs Realty Group": {
        "site": "digsrealtynyc.com",
        "shorthand": "Digs Realty",
        "facts": [
            "Digs Realty Group (digsrealtynyc.com) gives buyers up to 67% commission rebate and has paid out $4MM+ in client rebates since launch",
            "NYC, Westchester, and Long Island residential focus with co-op board package, buyer rep, and seller rep workflows",
            "A six-person Upper West Side team positions itself as a discount-yet-full-service brokerage versus traditional NYC firms",
        ],
        "blog_keywords": ["NYC rebate brokerage", "co-op board package", "Westchester listings"],
    },
    "J&A Abstract": {
        "site": "jaabstract.com",
        "shorthand": "J&A Abstract",
        "facts": [
            "J&A Abstract (jaabstract.com) covers PA residential and commercial title work with in-house attorney review out of Feasterville-Trevose",
            "Service list includes deed transfers, escrow disbursement, recording, lien searches, and after-hour closings for partner agents",
            "A five-person bench handles conveyancing, bringdown searches, and lender/owner title insurance",
        ],
        "blog_keywords": ["PA closings", "conveyancing", "after-hour closing video"],
    },
}

DEFAULT_COMPANY = {
    "site": "",
    "shorthand": "the firm",
    "facts": ["listed across residential and closing-adjacent services"],
    "blog_keywords": ["partner enablement"],
}

# Per-batch counter for cycling through facts so neighboring leads at the
# same company see different angles.
_fact_index: dict[str, int] = {}


def next_fact(co: str, facts_list: list[str]) -> str:
    i = _fact_index.get(co, 0)
    _fact_index[co] = i + 1
    return facts_list[i % len(facts_list)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def first_name(row: dict) -> str:
    return (row.get("First Name") or row.get("\ufeffFirst Name") or "").strip()


def company(row: dict) -> str:
    return row.get("Company Name for Emails") or row.get("Company") or ""


def role_bucket(title: str) -> str:
    t = (title or "").lower()
    if any(x in t for x in ("attorney", "lawyer", "paralegal")):
        return "attorney"
    if any(
        x in t
        for x in (
            "escrow", "processor", "coordinator", "closer", "post closing",
            "settlement", "title specialist", "title officer", "closing agent",
            "closing officer", "underwriter", "intake", "production specialist",
            "staff closer", "office administrator", "executive assistant",
            "administrative assistant", "settlement assistant", "settlement agent",
        )
    ):
        return "escrow"
    if any(
        x in t
        for x in (
            "ceo", "chief executive", "president", "vp", "vice president",
            "director", "managing partner", "managing", "broker in charge",
            "broker owner", "general manager", "owner", "principal", "deputy director",
            "operations manager", "branch manager", "assistant director", "manager training",
        )
    ):
        return "leader"
    if any(
        x in t
        for x in (
            "business development", "marketing", "account executive", "account rep",
            "sales", "sales manager", "associate sale manager", "senior member representative",
            "member representative",
        )
    ):
        return "sales"
    if any(
        x in t
        for x in (
            "data engineer", "information security", "system admin", "information technology",
            "data ", "engineer", "developer", "security officer",
        )
    ):
        return "ops"
    if any(x in t for x in ("hr", "human resources")):
        return "hr"
    if any(x in t for x in ("accountant", "finance", "controller", "auditor", "bookkeeper")):
        return "finance"
    if any(x in t for x in ("realtor", "agent", "broker", "salesperson", "consultant", "isa", "real estate")):
        return "agent"
    return "general"


def location(city: str, state: str) -> str:
    c, s = (city or "").strip(), (state or "").strip()
    if c and s:
        return f"{c}, {s}"
    return c or s or ""


def safe_title(t: str) -> str:
    t = " ".join((t or "").split())
    if not t:
        return "team member"
    # Normalize all-caps or all-lowercase titles so the opener reads cleanly.
    if t == t.upper() or t == t.lower():
        return " ".join(w.capitalize() if not w.isupper() or len(w) > 4 else w.title() for w in t.split())
    return t


def fact_line(fact: str) -> str:
    fact = fact.strip().rstrip(".")
    return fact[0].upper() + fact[1:]


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def qa(subject: str, body: str) -> list[str]:
    issues = []
    if word_count(body) > 100:
        issues.append(f"words>{word_count(body)}")
    if len(subject) > 60:
        issues.append(f"subj>{len(subject)}")
    low = (subject + body).lower()
    for b in BANNED:
        if b in low:
            issues.append(b)
    return issues


def truncate(text: str, max_words: int = 100) -> str:
    words = re.findall(r"\S+", text)
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])


# ---------------------------------------------------------------------------
# Email writing per role bucket
# ---------------------------------------------------------------------------
def write_emails(lead: dict, co_meta: dict, bucket: str, peer: dict | None) -> list[tuple[str, str]]:
    fn = lead["first_name"]
    tit = safe_title(lead["title"])
    co = lead["company"]
    short = co_meta.get("shorthand", co.split()[0])
    city = lead["city"] or ""
    state = lead["state"] or ""
    loc = location(city, state)
    loc_suffix = f" in {loc}" if loc else ""
    city_tag = city or (loc.split(",")[0] if loc else "")

    fact_a = fact_line(next_fact(co, co_meta["facts"]))
    fact_b = fact_line(next_fact(co + "_b", co_meta["facts"]))
    # Ensure email 2's fact differs from email 1's so each lead sees two angles
    tries = 0
    while fact_b == fact_a and tries < len(co_meta["facts"]):
        fact_b = fact_line(next_fact(co + "_b", co_meta["facts"]))
        tries += 1

    peer_clause = ""
    if peer:
        peer_clause = f"{peer['first_name']} {peer['last_name']} at {short} may catch a parallel note"

    role_line = _role_line(tit, co, loc_suffix)

    if bucket == "escrow":
        return _escrow_emails(fn, role_line, short, city_tag, fact_a, fact_b, peer_clause, co)
    if bucket == "attorney":
        return _attorney_emails(fn, role_line, short, city_tag, fact_a, fact_b, peer_clause, co)
    if bucket == "leader":
        return _leader_emails(fn, role_line, short, city_tag, fact_a, fact_b, peer_clause, co)
    if bucket == "sales":
        return _sales_emails(fn, role_line, short, city_tag, fact_a, fact_b, peer_clause, co)
    if bucket == "ops":
        return _ops_emails(fn, role_line, short, city_tag, fact_a, fact_b, peer_clause, co)
    if bucket == "hr":
        return _hr_emails(fn, role_line, short, city_tag, fact_a, fact_b, peer_clause, co)
    if bucket == "finance":
        return _finance_emails(fn, role_line, short, city_tag, fact_a, fact_b, peer_clause, co)
    if bucket == "agent":
        return _agent_emails(fn, role_line, short, city_tag, fact_a, fact_b, peer_clause, co)
    return _general_emails(fn, role_line, short, city_tag, fact_a, fact_b, peer_clause, co)


def _role_line(title: str, co: str, loc_suffix: str) -> str:
    bare = title.lower().replace("\u00ae", "").strip()
    article = "an" if bare and bare[0] in "aeiou" else "a"
    if bare in ("realtor", "broker", "agent"):
        return f"You work as {article} {bare} at {co}{loc_suffix}."
    return f"You work as {title} at {co}{loc_suffix}."


def _peer_line(peer_clause: str, fn: str, hook: str) -> str:
    if peer_clause:
        return f"{peer_clause}; this one is {fn}-specific: {hook}"
    return f"Quick lane just for you: {hook}"


# ---------- role-specific templates -----------------------------------------
def _escrow_emails(fn, role, short, city, f1, f2, peer, co):
    e1 = (
        f"Hi {fn},\n\n"
        f"{role}\n\n"
        f"{f1}. The settlement desks that scale fastest cut repeat questions by turning timeline and wire steps into mobile-first explainer reels.\n\n"
        f"We finish supplied screen recordings or branch footage so the look stays consistent across files.\n\n"
        f"Worth a sample cut?"
    )
    e2 = (
        f"Hi {fn},\n\n"
        f"One more angle. {f2}. Buyers retain seven-second mobile cuts on wire fraud and closing day far better than PDFs.\n\n"
        f"We engineer pacing and captions on footage you supply, post-production only.\n\n"
        f"Curious to see a 30-second style ref?"
    )
    hook = "wire-safety and what-happens-at-the-table explainer reels from supplied desk recordings"
    e3 = (
        f"Hi {fn},\n\n"
        f"{_peer_line(peer, fn, hook)}.\n\n"
        f"Happy to send a one-page outline. Want it?"
    )
    subs = (
        f"Closings {city}" if city else f"{short} closings",
        f"Wire safety {city}" if city else f"Wire safety",
        f"Reel outline for {fn}",
    )
    return [(_clip(subs[0]), e1), (_clip(subs[1]), e2), (_clip(subs[2]), e3)]


def _attorney_emails(fn, role, short, city, f1, f2, peer, co):
    e1 = (
        f"Hi {fn},\n\n"
        f"{role}\n\n"
        f"{f1}. Settlement counsel cut day-of friction when buyers see a clear visual read on what happens at the table before they arrive.\n\n"
        f"We finish attorney-supplied explainer footage and Q&A clips, post-production only.\n\n"
        f"Worth a sample?"
    )
    e2 = (
        f"Hi {fn},\n\n"
        f"One more angle. {f2}. A two-minute counsel intro can stand in for half the repeat client calls each week.\n\n"
        f"We pace and grade footage you supply, no filming on our side.\n\n"
        f"Relevant?"
    )
    hook = "counsel-led closing walkthroughs cut into mobile pieces for client prep"
    e3 = (
        f"Hi {fn},\n\n"
        f"{_peer_line(peer, fn, hook)}.\n\n"
        f"Open to a one-page spec?"
    )
    subs = (
        f"Counsel reel {short}",
        f"Table walkthrough {city}" if city else f"Closing-table walkthrough",
        f"Counsel spec for {fn}",
    )
    return [(_clip(subs[0]), e1), (_clip(subs[1]), e2), (_clip(subs[2]), e3)]


def _leader_emails(fn, role, short, city, f1, f2, peer, co):
    e1 = (
        f"Hi {fn},\n\n"
        f"{role}\n\n"
        f"{f1}. Leadership clips and training videos land harder when every branch's finish quality matches the brand promise.\n\n"
        f"We standardize on supplied leadership and partner footage, post-production only.\n\n"
        f"Worth a sample?"
    )
    e2 = (
        f"Hi {fn},\n\n"
        f"One more angle. {f2}. A single edit standard beats ten styles when you're scaling enablement across desks.\n\n"
        f"We build the look on footage you supply, with motion graphics tuned to the brand kit.\n\n"
        f"On your radar?"
    )
    hook = "a firm-wide reel standard so every desk's training and partner clips read the same"
    e3 = (
        f"Hi {fn},\n\n"
        f"{_peer_line(peer, fn, hook)}.\n\n"
        f"Want a 90-second style reel as the reference?"
    )
    subs = (
        f"Leadership reel {short}",
        f"Brand standard {short}",
        f"Firm-wide spec {fn}",
    )
    return [(_clip(subs[0]), e1), (_clip(subs[1]), e2), (_clip(subs[2]), e3)]


def _sales_emails(fn, role, short, city, f1, f2, peer, co):
    e1 = (
        f"Hi {fn},\n\n"
        f"{role}\n\n"
        f"{f1}. Partner-facing reels close lender and realtor conversations faster than slide decks do.\n\n"
        f"We polish supplied partner, event, and CE footage, post-production only.\n\n"
        f"Worth a sample?"
    )
    e2 = (
        f"Hi {fn},\n\n"
        f"One more angle. {f2}. One filmed interview becomes lender- and agent-specific hook variants with captions for follow-ups.\n\n"
        f"We batch the variants from footage you supply.\n\n"
        f"Curious?"
    )
    hook = "referral-grade hook variants and enablement reels from supplied partner footage"
    e3 = (
        f"Hi {fn},\n\n"
        f"{_peer_line(peer, fn, hook)}.\n\n"
        f"Happy to outline a partner reel plan; want it?"
    )
    subs = (
        f"Partner reel {short}",
        f"Referral hooks {city}" if city else f"Referral hook variants",
        f"AE plan for {fn}",
    )
    return [(_clip(subs[0]), e1), (_clip(subs[1]), e2), (_clip(subs[2]), e3)]


def _ops_emails(fn, role, short, city, f1, f2, peer, co):
    e1 = (
        f"Hi {fn},\n\n"
        f"{role}\n\n"
        f"{f1}. Async screen walkthroughs adopt faster when they look like product launch videos, not raw screen captures.\n\n"
        f"We finish supplied recordings for internal rollouts, post-production only.\n\n"
        f"Worth a sample?"
    )
    e2 = (
        f"Hi {fn},\n\n"
        f"One more angle. {f2}. System or policy changes ship cleaner when the explainer pacing matches the audience.\n\n"
        f"We add motion and captions to footage you supply.\n\n"
        f"Useful?"
    )
    hook = "internal rollout reels and onboarding cuts from supplied screen recordings"
    e3 = (
        f"Hi {fn},\n\n"
        f"{_peer_line(peer, fn, hook)}.\n\n"
        f"Open to a tight outline?"
    )
    subs = (
        f"Ops video {short}",
        f"Rollout reel {short}",
        f"Walkthrough cuts {fn}",
    )
    return [(_clip(subs[0]), e1), (_clip(subs[1]), e2), (_clip(subs[2]), e3)]


def _hr_emails(fn, role, short, city, f1, f2, peer, co):
    e1 = (
        f"Hi {fn},\n\n"
        f"{role}\n\n"
        f"{f1}. Recruiting and onboarding reels carry the brand promise into hiring before a candidate sees the office.\n\n"
        f"We finish leadership and team-supplied footage, post-production only.\n\n"
        f"Worth a sample?"
    )
    e2 = (
        f"Hi {fn},\n\n"
        f"One more angle. {f2}. Onboarding videos that match the brand kit shave hours of repeat orientation each cycle.\n\n"
        f"We pace and caption supplied recordings.\n\n"
        f"Curious?"
    )
    hook = "recruiting and onboarding video reels engineered from supplied team footage"
    e3 = (
        f"Hi {fn},\n\n"
        f"{_peer_line(peer, fn, hook)}.\n\n"
        f"Open to a one-page outline?"
    )
    subs = (
        f"People videos {short}",
        f"Onboarding reel {short}",
        f"Recruiting plan {fn}",
    )
    return [(_clip(subs[0]), e1), (_clip(subs[1]), e2), (_clip(subs[2]), e3)]


def _finance_emails(fn, role, short, city, f1, f2, peer, co):
    e1 = (
        f"Hi {fn},\n\n"
        f"{role}\n\n"
        f"{f1}. Finance and audit-grade explainers retain better when motion graphics walk the viewer through numbers, not bullet text.\n\n"
        f"We engineer supplied financial decks and walkthrough footage into clean visual edits.\n\n"
        f"Worth a sample?"
    )
    e2 = (
        f"Hi {fn},\n\n"
        f"One more angle. {f2}. Quarterly or board reels lift comprehension when every number tracks with motion.\n\n"
        f"We finish on footage and slides you supply.\n\n"
        f"Relevant?"
    )
    hook = "finance and audit explainer reels built from supplied decks and walkthroughs"
    e3 = (
        f"Hi {fn},\n\n"
        f"{_peer_line(peer, fn, hook)}.\n\n"
        f"Want the one-page outline?"
    )
    subs = (
        f"Finance reels {short}",
        f"Board cut {short}",
        f"Numbers reel {fn}",
    )
    return [(_clip(subs[0]), e1), (_clip(subs[1]), e2), (_clip(subs[2]), e3)]


def _agent_emails(fn, role, short, city, f1, f2, peer, co):
    e1 = (
        f"Hi {fn},\n\n"
        f"{role}\n\n"
        f"{f1}. Tours close faster when 45-second hooks open with the neighborhood read buyers care about first.\n\n"
        f"We polish supplied walkthrough footage into mobile-native cuts.\n\n"
        f"Worth a sample?"
    )
    e2 = (
        f"Hi {fn},\n\n"
        f"One more angle. {f2}. One shoot day can become a buyer hook, a neighborhood hook, and a referral hook from the same footage.\n\n"
        f"We batch variants you can post weekly.\n\n"
        f"Curious?"
    )
    hook = "listing hooks tuned to your market, cut from supplied tour footage"
    e3 = (
        f"Hi {fn},\n\n"
        f"{_peer_line(peer, fn, hook)}.\n\n"
        f"Want me to map one listing into a mini reel kit?"
    )
    subs = (
        f"Listings {city}" if city else f"{short} listings",
        f"Tour hooks {city}" if city else f"Tour hook variants",
        f"Reel kit for {fn}",
    )
    return [(_clip(subs[0]), e1), (_clip(subs[1]), e2), (_clip(subs[2]), e3)]


def _general_emails(fn, role, short, city, f1, f2, peer, co):
    e1 = (
        f"Hi {fn},\n\n"
        f"{role}\n\n"
        f"{f1}. Explainer reels save hours when one short answers the questions that keep returning to your inbox.\n\n"
        f"We finish supplied footage, post-production only.\n\n"
        f"Worth a sample?"
    )
    e2 = (
        f"Hi {fn},\n\n"
        f"One more angle. {f2}. Tight pacing and motion graphics make explainers easier to forward than slideshows.\n\n"
        f"We finish on footage you supply.\n\n"
        f"Useful?"
    )
    hook = "explainer reels grounded in supplied desk and team footage"
    e3 = (
        f"Hi {fn},\n\n"
        f"{_peer_line(peer, fn, hook)}.\n\n"
        f"Open to a one-page outline?"
    )
    subs = (
        f"{short} reel {fn}",
        f"Second angle {short}",
        f"Quick outline {fn}",
    )
    return [(_clip(subs[0]), e1), (_clip(subs[1]), e2), (_clip(subs[2]), e3)]


def _clip(s: str) -> str:
    if len(s) <= 60:
        return s
    return s[:57].rstrip() + "..."


# ---------------------------------------------------------------------------
# Build research per lead
# ---------------------------------------------------------------------------
def build_research(lead: dict, co_meta: dict, bucket: str, peers: list[dict]) -> dict:
    co = lead["company"]
    fact = fact_line(next_fact(co + "_signal", co_meta["facts"]))
    loc = location(lead["city"], lead["state"])
    site = co_meta.get("site") or (lead["website"].replace("https://", "").replace("http://", "").rstrip("/") if lead["website"] else "")
    role_label = safe_title(lead["title"])

    signal_pieces = [f"{role_label} at {co}"]
    if loc:
        signal_pieces.append(f"based in {loc}")
    if site:
        signal_pieces.append(f"site context: {site}")
    signal_pieces.append(f"firm note: {fact}")
    signal = "; ".join(signal_pieces) + "."

    peer_names = [f"{p['first_name']} {p['last_name']}" for p in peers if p["email"] != lead["email"]]
    notes_parts = [f"Role bucket: {bucket}"]
    if peer_names:
        notes_parts.append(f"Same-firm peers in this batch: {', '.join(peer_names[:4])}")
    notes_parts.append("Spot-check city + role nuance before ESP upload.")
    return {
        "csv_index": lead["csv_index"],
        "row": lead["csv_index"] + 1,
        "first_name": lead["first_name"],
        "last_name": lead["last_name"],
        "title": lead["title"],
        "company": co,
        "email": lead["email"],
        "website": lead["website"],
        "linkedin": lead["linkedin"],
        "twitter": lead["twitter"],
        "facebook": lead["facebook"],
        "city": lead["city"],
        "state": lead["state"],
        "research_signal": signal,
        "research_notes": " ".join(notes_parts),
    }


def row_to_lead(row: dict, idx: int) -> dict:
    return {
        "csv_index": idx,
        "first_name": first_name(row),
        "last_name": row["Last Name"],
        "title": row["Title"],
        "company": company(row),
        "email": row["Email"],
        "website": row.get("Website", ""),
        "linkedin": row.get("Person Linkedin Url", ""),
        "twitter": row.get("Twitter Url", ""),
        "facebook": row.get("Facebook Url", ""),
        "city": row.get("City", ""),
        "state": row.get("State", ""),
    }


# ---------------------------------------------------------------------------
def main() -> None:
    with CSV_PATH.open(newline="", encoding="utf-8-sig") as f:
        all_rows = list(csv.DictReader(f))

    remaining = [(i, all_rows[i]) for i in range(START_INDEX, len(all_rows))]
    print(f"Drafting {len(remaining)} leads from index {START_INDEX}")

    batch_num = FIRST_BATCH
    offset = 0
    total_fail = 0
    total_pass = 0

    while offset < len(remaining):
        chunk = remaining[offset : offset + BATCH_SIZE]
        leads = [row_to_lead(r, idx) for idx, r in chunk]

        # peers per company inside this batch
        company_groups: dict[str, list[dict]] = {}
        for L in leads:
            company_groups.setdefault(L["company"], []).append(L)

        research_out = []
        copy_out: dict[str, list[list[str]]] = {}

        for L in leads:
            co_meta = COMPANIES.get(L["company"], DEFAULT_COMPANY)
            bucket = role_bucket(L["title"])
            peers = company_groups.get(L["company"], [])
            peer_for_email3 = None
            if len(peers) > 1:
                idx_in_co = peers.index(L)
                peer_for_email3 = peers[(idx_in_co + 1) % len(peers)]

            research_out.append(build_research(L, co_meta, bucket, peers))
            seq = write_emails(L, co_meta, bucket, peer_for_email3)

            for subj, body in seq:
                issues = qa(subj, body)
                if issues:
                    print(f"  QA FAIL batch {batch_num} {L['email']}: {issues}")
                    total_fail += 1
                else:
                    total_pass += 1
            copy_out[L["email"].lower()] = [[s, b] for s, b in seq]

        r_path = ROOT / "campaigns" / f"pilot-20-batch{batch_num}-research.json"
        c_path = ROOT / "campaigns" / f"pilot-20-batch{batch_num}-copy.json"
        r_path.write_text(json.dumps(research_out, indent=2) + "\n", encoding="utf-8")
        c_path.write_text(json.dumps(copy_out, indent=2) + "\n", encoding="utf-8")
        print(f"  batch {batch_num}: wrote {len(leads)} leads (idx {chunk[0][0]}-{chunk[-1][0]})")
        batch_num += 1
        offset += BATCH_SIZE

    # ---- Backfill batch 23 (leftover indices) ----
    chunk = [(i, all_rows[i]) for i in BATCH23_INDICES]
    leads = [row_to_lead(r, idx) for idx, r in chunk]
    company_groups: dict[str, list[dict]] = {}
    for L in leads:
        company_groups.setdefault(L["company"], []).append(L)

    research_out = []
    copy_out: dict[str, list[list[str]]] = {}
    for L in leads:
        co_meta = COMPANIES.get(L["company"], DEFAULT_COMPANY)
        bucket = role_bucket(L["title"])
        peers = company_groups.get(L["company"], [])
        peer_for_email3 = None
        if len(peers) > 1:
            idx_in_co = peers.index(L)
            peer_for_email3 = peers[(idx_in_co + 1) % len(peers)]

        research_out.append(build_research(L, co_meta, bucket, peers))
        seq = write_emails(L, co_meta, bucket, peer_for_email3)
        for subj, body in seq:
            issues = qa(subj, body)
            if issues:
                print(f"  QA FAIL batch {BATCH23_NUMBER} {L['email']}: {issues}")
                total_fail += 1
            else:
                total_pass += 1
        copy_out[L["email"].lower()] = [[s, b] for s, b in seq]

    r_path = ROOT / "campaigns" / f"pilot-20-batch{BATCH23_NUMBER}-research.json"
    c_path = ROOT / "campaigns" / f"pilot-20-batch{BATCH23_NUMBER}-copy.json"
    r_path.write_text(json.dumps(research_out, indent=2) + "\n", encoding="utf-8")
    c_path.write_text(json.dumps(copy_out, indent=2) + "\n", encoding="utf-8")
    print(f"  batch {BATCH23_NUMBER}: wrote {len(leads)} leftover leads (idx {BATCH23_INDICES})")

    total_emails = total_pass + total_fail
    print(f"\nDone. QA: {total_pass}/{total_emails} passed")
    if total_fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
