#!/usr/bin/env python3
"""Shared QA checks for personalized email copy."""

from __future__ import annotations

import re
from collections import Counter

from lead_personalization.segments import GIVEN_NAMES, is_plausible_first_name

BANNED = [
    "hope this email finds you well",
    "hope this finds you well",
    "i came across your profile",
    "i noticed your business online",
    "impressive linkedin",
    "pick your brain",
    "just following up",
    "just bumping",
    "circling back",
    "circle back",
    "touch base",
    "deep dive",
    "we help companies like yours",
    "leading post-production",
    "would love to connect",
    "just wanted to follow up",
    "just wanted to check in",
    "just checking in",
    "hope you're having a great week",
    "hope you are doing well",
    "reaching out to see if",
    "wanted to reach out",
    "quick follow up",
    "quick follow-up",
    "bump this to the top of your inbox",
    "as per my previous email",
    "allow me to introduce myself",
    "not sure who needs to hear this",
    "don't hesitate to reach out",
    "feel free to reach out",
    "looking forward to hearing from you",
    "—",
]

# User-voted AI slop phrases & telltale buzzwords that scream machine generation
AI_SLOP_PHRASES = [
    # Verbs and action buzzwords
    "delve",
    "delving",
    "delves",
    "delve into",
    "unleash",
    "unleashing",
    "supercharge",
    "supercharging",
    "revolutionize",
    "revolutionizing",
    "spearhead",
    "spearheading",
    "skyrocket",
    "skyrocketing",
    "harness",
    "harnessing",
    "bolster",
    "bolstering",
    "foster",
    "fostering",
    "elevate",
    "elevating",
    "empower",
    "empowering",
    "demystify",
    "demystifying",
    "streamline",
    "streamlining",
    "leverage",
    "leveraging",
    "underscore",
    "underscoring",
    "underscores",
    "transcend",
    "transcending",
    "propel your",
    "propelling your",
    "unlock the power of",
    "unlocking the power of",
    # Flowery nouns, adjectives, and buzzwords
    "tapestry",
    "rich tapestry",
    "testament to",
    "a testament",
    "game-changer",
    "game changer",
    "transformative",
    "seamless",
    "seamlessly",
    "cutting-edge",
    "cutting edge",
    "state-of-the-art",
    "state of the art",
    "bespoke",
    "paramount",
    "multifaceted",
    "plethora",
    "paradigm shift",
    "synergy",
    "synergistic",
    "synergies",
    "beacon of",
    "beacon",
    "pivotal",
    "robust",
    "groundbreaking",
    "unparalleled",
    "burgeoning",
    "interplay",
    "ever-evolving",
    "meticulous",
    "panacea",
    "realm of",
    "cornerstone of",
    "linchpin of",
    "kaleidoscope of",
    "holistic approach",
    # Formulaic AI email openers, transitions, and clichés
    "in today's fast-paced",
    "in today's fast paced",
    "in today's digital landscape",
    "in today's competitive landscape",
    "in today's world",
    "in this digital age",
    "in an era where",
    "at its core",
    "at the heart of",
    "look no further",
    "take your business to the next level",
    "take your brand to the next level",
    "unlock your potential",
    "stand out from the crowd",
    "it is important to note",
    "it's important to note",
    "it is important to remember",
    "it's important to remember",
    "it is worth noting",
    "it's worth noting",
    "without further ado",
    "needless to say",
    "navigating the complexities",
    "as we navigate",
    "it goes without saying",
    "dive deep into",
    "move the needle",
    "drive impactful results",
    "drive real impact",
    "unlock tangible value",
    "embark on a journey",
    "picture this",
    "hope this helps",
    "let's explore",
    "it's not just about",
    "it is not just about",
    "shed light on",
    "chart the course",
]

BRAND_FORBIDDEN = [
    "cheap",
    "affordable",
    "freelancer",
    "quick edit",
    "basic video",
    " gig",
    "broadcast",
]

SPAM_TRIGGERS = [
    # Urgent / Artificial Pressure
    "act now",
    "act fast",
    "limited time",
    "urgent action required",
    "immediate action required",
    "last chance",
    "expires today",
    "ending soon",
    "don't delay",
    "don't miss out",
    "time-sensitive",
    "time sensitive",
    "once in a lifetime",
    "instant access",
    "apply now",
    "call now",
    "order now",
    "final notice",

    # Financial / Too-Good-To-Be-True / Get-Rich Promises
    "100% free",
    "make money fast",
    "double your income",
    "double your money",
    "extra income",
    "financial freedom",
    "earn cash",
    "get rich",
    "cash bonus",
    "free money",
    "passive income",
    "fast cash",
    "billion dollars",
    "million dollars",
    "money-back guarantee",
    "money back guarantee",
    "pure profit",
    "unsecured debt",
    "consolidate debt",
    "get out of debt",
    "earn extra cash",
    "crypto giveaway",
    "lowest price guarantee",
    "best price guarantee",

    # Exaggerated Claims & Low-Trust Guarantees
    "guarantee",
    "100% guaranteed",
    "guaranteed results",
    "satisfaction guaranteed",
    "risk-free",
    "no catch",
    "no strings attached",
    "no risk",
    "no obligation",
    "no hidden fees",
    "secret hack",
    "secret trick",
    "amazing offer",
    "incredible results",
    "unbelievable results",
    "life-changing results",
    "claim your prize",
    "you have been selected",
    "prize winner",

    # Phishing & Account Mimicry
    "verify your account",
    "confirm your identity",
    "suspended account",
    "account suspended",
    "security alert",
    "update your billing",
    "password reset",
    "unauthorized login",
    "billing issue",
    "immediate response required",

    # Spam CTA & Link Triggers
    "click here",
    "click below",
    "click the link",
    "click this link",
    "buy now",
    "open immediately",
]

# Subject-only spam triggers (filters + skim filter)
SUBJECT_SPAM_WORDS = [
    # Core spam triggers
    "free",
    "guaranteed",
    "guarantee",
    "urgent",
    "act now",
    "act fast",
    "limited time",
    "click here",
    "buy now",
    "winner",
    "congratulations",
    "100%",
    "100% free",
    "no obligation",
    "no catch",
    "exclusive offer",
    "special promotion",
    "deal of the day",
    "save big",
    "lowest price",
    "reminder",
    "last chance",
    "final notice",
    "urgent notice",
    "action required",
    "time-sensitive",
    "time sensitive",
    "don't miss out",
    "urgent action required",
    "immediate action required",
    "open immediately",
    "instant access",
    "amazing",
    "incredible",
    "discount",
    "risk-free",
    "risk free",
    "pure profit",
    "make money",
    "earn cash",
    "cash bonus",
    "secret trick",
    "claim your",
    "once in a lifetime",
    "order confirmation",
    "invoice attached",
    "satisfaction guaranteed",
    "!!!",
    "$$$",
    "quick question",  # too generic unless email 3 asks one specific Q
    "re:",
    "fwd:",
    "fw:",
]

HARD_CTA_PATTERNS = [
    "calendly",
    "book 15",
    "book a call",
    "free tuesday",
    "schedule a call",
    "grab 30 minutes",
    "ten-minute call",
    "ten minute call",
    "quick call",
]

# Truncation artifacts from snippet clipping must never reach a prospect.
ELLIPSIS_MARKS = ("...", "\u2026")

# Closed-class words a prospect-supplied subject hook can never end on. When the
# hook is truncated to the length cap, landing on one of these reads as a
# broken send ("a wide selection of"). See build_subject / _hook_from_meta.
FUNCTION_WORDS = {
    "the", "a", "an", "of", "for", "and", "or", "nor", "but", "to", "in", "on",
    "at", "by", "with", "from", "into", "onto", "upon", "over", "under", "as",
    "that", "this", "is", "are", "was", "were", "be", "been", "being", "our",
    "your", "their", "his", "her", "its", "we", "us", "they", "them", "i", "me",
    "my", "so", "if", "than", "then",
    # Hyphenated adjective that reads as an incomplete noun phrase on its own
    # ("this is your go-to" — go-to what?). Not a state code, so safe to include.
    "go-to",
}


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def contains_forbidden(text: str) -> bool:
    """True when text carries banned, brand-forbidden, spam-trigger, or AI slop content."""
    low = (text or "").lower()
    return (
        any(b in low for b in BANNED)
        or any(s in low for s in AI_SLOP_PHRASES)
        or any(w in low for w in BRAND_FORBIDDEN)
        or any(t in low for t in SPAM_TRIGGERS)
    )


def subject_has_spam(subject: str) -> bool:
    low = (subject or "").lower().strip()
    words = low.split()
    if sum(1 for w in words if w.isupper() and len(w) > 2) >= 2:
        return True
    if "!" in (subject or ""):
        return True
    for trigger in SUBJECT_SPAM_WORDS:
        if trigger in low:
            return True
    for word in BRAND_FORBIDDEN:
        if word.strip() in low:
            return True
    return False


def subject_is_fragment(subject: str) -> bool:
    """True when a subject truncates onto a function word.

    A hook cut at a word boundary can still cut mid-phrase, landing on a
    closed-class word like "of", "the", or "is" — "a wide selection of",
    "able company ltd is the". Reads as a broken send, so it must never ship.
    """
    stripped = (subject or "").strip()
    if stripped and stripped[-1] in TRAILING_FRAGMENT_CHARS:
        return True
    words = stripped.lower().split()
    return bool(words) and words[-1] in FUNCTION_WORDS


def greeting_line(body: str) -> str:
    return (body.split("\n\n")[0] if body else "").strip()


GREETING_WORDS = ("Hi", "Hey", "Hello")


def greeting_is_valid(body: str, email: str = "") -> bool:
    """Accept the rotated greetings: "Hi," / "Hey," / "Hello," for company tier,
    and "{Hi|Hey|Hello} {name}," or bare "{name}," for a verified person."""
    line = greeting_line(body)
    if line in {f"{w}," for w in GREETING_WORDS}:
        return True
    match = re.match(r"^(?:(?:Hi|Hey|Hello) )?([A-Za-z]+),$", line)
    if not match:
        return False
    return is_plausible_first_name(match.group(1), email)


# The opener is the client's line: it must be about them, never the sender.
_SENDER_CENTRIC_START = re.compile(r"^(?:i|i'm|i've|i'd|we|we're|we've|my|our|us)\b", re.I)
SENDER_CENTRIC_PHRASES = (
    "caught my eye",
    "i noticed",
    "i saw",
    "i came across",
    "i was looking",
    "i wanted",
    "i am reaching out",
    "i'm reaching out",
    "my name is",
    "we help",
)


def opener_is_client_centric(body: str) -> bool:
    """True when the first line after the greeting is about the client.

    The solution line may say "we": that is just what the sender does. The
    first line may not, and no line may use the stock sender-centric phrases.
    """
    paragraphs = [p.strip() for p in (body or "").split("\n\n")]
    if len(paragraphs) < 2:
        return True
    if _SENDER_CENTRIC_START.match(paragraphs[1]):
        return False
    low = (body or "").lower()
    return not any(p in low for p in SENDER_CENTRIC_PHRASES)


# Site copy that opens like this is the middle of a sentence or filler, not a
# phrase worth quoting: "With over a decade of experience", "There may be
# numerous things", "Based in Dubai".
FILLER_START = re.compile(
    r"^(?:with|there|from|for|as|when|if|whether|to|based|over|and|or|but|so|"
    r"because|since|all|this|that|these|those|here|it|its|it's|whatever|lately|"
    r"sorry|hello|hi|hey|thanks|thank|yes|no|"
    r"whether|providing|offering|serving|specializing|specialising)\b",
    re.I,
)


def hook_start_is_filler(text: str) -> bool:
    return bool(FILLER_START.match((text or "").strip()))


# The copy is English. A German/French/Spanish/Swedish tagline quoted back
# ("créez vos podcasts uniques avec nous") reads as a broken merge.
_FOREIGN_WORDS = frozenset({
    "und", "der", "die", "das", "für", "mit", "wir", "ihre", "agentur", "avec",
    "pour", "nous", "vos", "votre", "les", "des", "une", "et", "para", "con",
    "los", "las", "del", "nuestro", "su", "di", "per", "il", "della", "och",
    "på", "för", "med", "het", "een", "voor", "van", "en", "uw", "og", "af",
})


def is_probably_not_english(text: str) -> bool:
    low = (text or "").lower()
    if re.search(r"[^\x00-\x7f\u2018\u2019\u201c\u201d\u2013]", low):
        return True
    return bool(set(re.findall(r"[a-zäöüåéèàç]+", low)) & _FOREIGN_WORDS)


def snippet_reject_reasons(text: str) -> list[str]:
    """Reasons a prospect snippet must never be quoted back in a body.

    The body quotes positioning text verbatim ("Your site leads with X"), so it
    needs at least the subject's junk filter (error pages, addresses, phone
    numbers, nav labels) plus shape checks: a question, a bare place name, or
    a list cut mid-way is not positioning.
    """
    raw = (text or "").strip()
    reasons = junk_hook_reasons(raw)
    if not raw:
        return ["empty"]
    if "?" in raw:
        reasons.append("question")
    if raw[-1] in TRAILING_FRAGMENT_CHARS:
        reasons.append("trailing_fragment")
    alpha_words = [w for w in re.findall(r"[A-Za-z][A-Za-z'-]*", raw)]
    if len(alpha_words) < 3:
        reasons.append("too_short")
    if alpha_words and alpha_words[-1].lower() in FUNCTION_WORDS:
        reasons.append("fragment")
    if sum(1 for ch in raw if ch.isdigit()) >= 4:
        reasons.append("digits")
    if hook_start_is_filler(raw):
        reasons.append("filler_start")
    if is_probably_not_english(raw):
        reasons.append("not_english")
    if re.search(r"[#*_<>{}\[\]=]", raw):
        reasons.append("markup")
    return reasons


def company_name_in_subject(subject: str, company: str) -> bool:
    """True when the subject carries the recipient's own business name.

    The body is already checked for this (company name never appears in copy,
    per the dual-tier contract), but the subject was never checked and has
    shipped real cases: "genrietta arakelova, d.d.s", "at luxe dental dallas".
    """
    company_clean = (company or "").strip()
    subject_low = (subject or "").lower()
    # A distinctive brand word alone also leaks the name: "neuen films
    # creates" for "Neuen Films". Category and generic words do not count.
    subject_tokens = set(re.findall(r"[a-z0-9]+", subject_low))
    brand_tokens = {
        t for t in re.findall(r"[a-z0-9]+", company_clean.lower())
        if len(t) >= 5 and t not in _CATEGORY_NOUNS and t not in _GENERIC_ORG_WORDS
    }
    if brand_tokens & subject_tokens:
        return True
    if len(company_clean) < 4 or company_clean.lower() not in subject_low:
        return False
    # "at simply dentistry" is the company. "your trusted paradise valley" is
    # the company's own tagline pasted back. Compare on alnum only so a stray
    # period in "d.d.s" cannot hide a match.
    return re.sub(r"[^a-z0-9]", "", company_clean.lower()) in re.sub(r"[^a-z0-9]", "", subject_low)


# Shapes that mean the hook came from a phone number, a street address, a URL,
# a CMS error page, or raw marketing copy rather than from a readable phrase.
_JUNK_SUBJECT_PATTERNS: tuple[tuple[str, str], ...] = (
    ("phone", r"\(?\b\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    ("url", r"\b(?:https?://|www\.|\.com\b|\.net\b|\.org\b|\.io\b)"),
    ("email", r"\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b"),
    ("address", r"\b\d{2,6}\s+[a-z]+\s+(?:blvd|blvd\.|st|street|ave|avenue|rd|road|dr|drive|ln|lane|way|suite|ste|hwy|pkwy|ct|court)\b"),
    ("zip", r"\b\d{5}(?:-\d{4})?\b"),
    (
        "error_page",
        r"\b(?:wordpress|40[0-9]|50[0-9]|error|access denied|forbidden|not found|"
        r"page not found|server error|index of|bad gateway|service unavailable|"
        r"gateway timeout|under construction|coming soon|maintenance mode|"
        r"account suspended|domain (?:is )?for sale|just another wordpress site|"
        r"attention required|cloudflare|captcha|enable javascript|"
        r"you have been blocked|access to this page|are you a robot)\b",
    ),
    ("business_suffix", r"\b(?:llc|inc|corp|corporation|ltd|plc|dba)\b"),
    # Bare "do"/"np"/"pa" are ordinary words ("as hard as you do"); only count
    # them as credentials when dotted or after a name comma ("smith, do").
    (
        "credential",
        r"\b(?:d\.?d\.?s\.?|d\.?m\.?d\.?|m\.?d\.?|ph\.?d\.?|r\.?n\.?)(?![a-z])"
        r"|\b(?:d\.o\.|n\.p\.|p\.a\.)|,\s*(?:do|np|pa)\b",
    ),
    ("price", r"\$\s?\d|\b(?:rates|pricing|prices|price list|packages from)\b"),
    # "#1 rated…", "No. 1 in…": a ranking claim pasted back reads as their ad.
    ("ranking", r"(?:#\s?\d|\bno\.\s?1\b|\bnumber one\b)"),
    # The business talking about itself ("we are locally owned").
    ("self_reference", r"^(?:we|we're|our|i|i'm|my|us)\b"),
)

# Prospect-side phrases that are grammatical but make a poor subject line
# because they are the business talking about itself.
_META_MARKER_PATTERNS = (
    "dentist near",
    "looking for a",
    "your trusted",
    "do you need",
    "call us",
    "contact us",
    "schedule",
    "insurance accepted",
    "we serve",
    "call today",
    "free consultation",
    "book online",
    "book now",
    "book today",
    "order online",
    "buy now",
    "sign up",
    "get a quote",
    "request a quote",
    "services we",
    "hours of operation",
    "open mon",
    "located in",
    "proudly serving",
    "family owned",
    "since 19",
    "thanks for visiting",
    "thank you for visiting",
    "welcome to",
    "get in touch",
    "how to get in touch",
    "enquire",
    "inquire",
    "tailored quote",
    "free quote",
    "call for",
    "click",
    "learn more",
    "read more",
    "home page",
    "homepage",
    "official site",
    "official website",
    "privacy policy",
    "cookie",
    "all rights reserved",
    "copyright",
    "trying to find",
    "book a ",
    "book your",
    "hire us",
    "call or text",
    "get started",
    "searching for",
)

# Closed-class words that may END a subject or snippet without making it a
# fragment are covered by FUNCTION_WORDS; these are trailing characters that
# always mean a phrase was cut mid-list ("video production,", "event video &").
TRAILING_FRAGMENT_CHARS = ",;:&+/-(.'\""


# Given names that are far more often a place or a plain word at the start of
# site copy ("Austin Wedding Films", "Grace Church") than a person.
_NAME_LIKE_PLACES = frozenset({
    "austin", "dallas", "victoria", "sierra", "jordan", "dale", "glen", "june",
    "april", "august", "hope", "grace", "joy", "faith", "will", "mark", "rose",
    "ray", "dawn", "max", "hunter", "jack",
})
# Second words that make "<Name> <Word>" a business or category phrase, not a
# person ("Austin Video", "Rose Wedding").
_CATEGORY_NOUNS = frozenset({
    "video", "videos", "videography", "photo", "photos", "photography", "film",
    "films", "media", "studio", "studios", "wedding", "weddings", "real",
    "estate", "home", "homes", "design", "creative", "productions", "production",
    "events", "event", "drone", "aerial", "dental", "law", "group", "agency",
    "and", "&",
})


# Words too common in business names to identify one on their own.
_GENERIC_ORG_WORDS = frozenset({
    "studio", "studios", "services", "service", "group", "company", "agency",
    "solutions", "photography", "videography", "productions", "creative",
    "media", "films", "pictures", "digital", "global", "international",
    "visual", "visuals", "content", "marketing", "design", "designs",
    "wedding", "weddings", "events", "event", "video", "aerial", "drone",
    "drones", "audio", "sound", "music", "recording", "records", "house",
    "homes", "realty", "estate", "properties", "property", "photographer",
    "photographers", "videographer", "cinema", "cinematic", "cinematography",
    "story", "stories", "moments", "memories", "light", "image", "images",
    "frame", "frames", "motion", "lens", "focus", "pixel", "brand", "brands",
    "concepts", "partners", "associates", "consulting", "network", "online",
    "local", "first", "great", "better", "premier", "elite", "royal", "golden",
    "united", "american", "national", "north", "south", "east", "west",
    "london", "dubai", "houston", "austin", "dallas", "miami", "orlando",
    "atlanta", "brisbane", "sydney", "melbourne", "toronto", "vancouver",
})


def starts_with_person_name(text: str) -> bool:
    """True when text opens with "<Given> <Surname>" ("Bill Miller Photography",
    "jillian nielsen is a langley ..."): a person, never positioning."""
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", text or "")
    if len(words) < 2:
        return False
    first, second = words[0].lower(), words[1].lower()
    if first not in GIVEN_NAMES or first in _NAME_LIKE_PLACES:
        return False
    return second not in _CATEGORY_NOUNS and second not in FUNCTION_WORDS


def junk_hook_reasons(subject: str) -> list[str]:
    """Return the reasons a subject reads as unfiltered data, not a phrase.

    The subject hook falls back to the raw GMB Meta_Description, which is
    unfiltered marketing copy. That has shipped phone numbers, street
    addresses, WordPress error pages, and a company name straight into the
    subject line of live sends. Every hit here is a hard fail.
    """
    low = (subject or "").lower()
    if not low:
        return []
    reasons = [name for name, pattern in _JUNK_SUBJECT_PATTERNS if re.search(pattern, low)]
    if any(marker in low for marker in _META_MARKER_PATTERNS):
        reasons.append("marketing_copy")
    if starts_with_person_name(low):
        reasons.append("person_name")
    return reasons


def company_name_in_body_check(body: str, company: str) -> bool:
    company_clean = (company or "").strip()
    return len(company_clean) >= 4 and company_clean.lower() in (body or "").lower()


def qa(subject: str, body: str, company: str = "", email: str = "") -> dict:
    issues = []
    wc = word_count(body)
    if wc > 100:
        issues.append(f"word count {wc}>100")
    if len(subject) > 60:
        issues.append(f"subject len {len(subject)}>60")
    if subject_has_spam(subject):
        issues.append("subject_spam_or_generic")
    if subject_is_fragment(subject):
        issues.append("subject_fragment")
    if not greeting_is_valid(body, email):
        issues.append("bad_greeting")
    if not opener_is_client_centric(body):
        issues.append("sender_centric_opener")
    if company_name_in_subject(subject, company):
        issues.append("company_name_in_subject")
    for junk in junk_hook_reasons(subject):
        issues.append(f"subject_junk:{junk}")
    for mark in ELLIPSIS_MARKS:
        if mark in subject or mark in body:
            issues.append("truncation_artifact")
            break
    company_clean = (company or "").strip()
    if company_name_in_body_check(body, company_clean):
        issues.append("company_name_in_body")
    low = (subject + " " + body).lower()
    for banned in BANNED:
        if banned in low:
            issues.append(f"banned:{banned}")
    for slop in AI_SLOP_PHRASES:
        if slop in low:
            issues.append(f"ai_slop:{slop}")
    for word in BRAND_FORBIDDEN:
        if word in low:
            issues.append(f"brand_forbidden:{word.strip()}")
    for trigger in SPAM_TRIGGERS:
        if trigger in low:
            issues.append(f"spam_trigger:{trigger}")
    for pattern in HARD_CTA_PATTERNS:
        if pattern in low:
            issues.append(f"hard CTA:{pattern}")
    return {
        "word_count": wc,
        "subject_len": len(subject),
        "pass": len(issues) == 0,
        "issues": issues,
    }


def campaign_repetition(sequences: list[list[tuple[str, str]]]) -> dict:
    """Measure how much copy is shared across a whole campaign.

    ``sequence_issues`` only ever compares one lead's three emails to each other,
    so a campaign can pass every per-lead check while thousands of leads receive
    the same handful of subjects and breakups. That is exactly what happened: a
    2-entry closer pool meant every email 3 in the list was one of four texts,
    and nothing reported it.

    Returns per-step subject concentration and the most-repeated bodies, so a
    review can see pool exhaustion instead of inferring it from a reply rate.
    """
    total = len(sequences)
    if not total:
        return {"leads": 0, "subjects": {}, "bodies": [], "repeat_rate": 0.0}

    subjects_by_step: dict[int, list[str]] = {}
    for seq in sequences:
        for step, (subject, _) in enumerate(seq, start=1):
            subjects_by_step.setdefault(step, []).append(subject.strip().lower())

    subjects: dict[str, dict] = {}
    for step, values in sorted(subjects_by_step.items()):
        counts = Counter(values)
        top, top_n = (counts.most_common(1)[0] if counts else ("", 0))
        subjects[f"step_{step}"] = {
            "sent": len(values),
            "distinct": len(counts),
            "top_subject": top,
            "top_count": top_n,
            "top_share": round(top_n / len(values), 4) if values else 0.0,
        }

    # Paragraph-level bodies, ignoring the greeting, which is a fixed shape.
    bodies: Counter[str] = Counter()
    for seq in sequences:
        for _, body in seq:
            for paragraph in body.split("\n\n")[1:]:
                key = re.sub(r"\W+", " ", paragraph.lower()).strip()
                if len(key.split()) >= 4:
                    bodies[key] += 1
    total_leads = total
    return {
        "leads": total_leads,
        "subjects": subjects,
        "bodies": [
            {"text": text[:120], "count": count, "share": round(count / total_leads, 4)}
            for text, count in bodies.most_common(10)
        ],
        "repeat_rate": round(
            sum(count for _, count in bodies.most_common()) / max(1, sum(bodies.values())), 4
        ),
    }


def repetition_warnings(
    report: dict,
    *,
    max_subject_share: float = 0.10,
    max_followup_subject_share: float = 0.15,
    max_paragraph_share: float = 0.25,
    min_leads: int = 40,
) -> list[str]:
    """Human-readable warnings from a ``campaign_repetition`` report.

    Small lists are skipped: with 20 leads one repeat is already 5%. Step 1 is
    held tighter because it usually carries the lead's own hook; follow-up
    subjects come from fixed pools (8-14 per segment), so ~10% is by design.
    Paragraph shares count once per email, so a 5-entry CTA pool sits near 20%;
    the 25% default flags pools that have collapsed below that.
    """
    leads = report.get("leads", 0)
    if leads < min_leads:
        return []
    warnings = []
    for step, info in report.get("subjects", {}).items():
        limit = max_subject_share if step == "step_1" else max_followup_subject_share
        if info["top_share"] > limit:
            warnings.append(
                f"{step}: subject {info['top_subject']!r} goes to "
                f"{info['top_share']:.0%} of leads ({info['distinct']} distinct subjects)"
            )
    for body in report.get("bodies", []):
        if body["share"] > max_paragraph_share:
            warnings.append(
                f"paragraph repeated in {body['share']:.0%} of leads: {body['text'][:70]!r}"
            )
    return warnings


def qa_sequence(sequence: list[tuple[str, str]], company: str = "", email: str = "") -> list[dict]:
    return [qa(subject, body, company, email) for subject, body in sequence]


def sequence_issues(sequence: list[tuple[str, str]]) -> list[str]:
    """Cross-step checks: no duplicate paragraphs, redundant paragraphs, or subjects across the sequence."""
    issues: list[str] = []
    seen: dict[str, int] = {}
    step_paras: list[tuple[int, set[str]]] = []
    for step, (_, body) in enumerate(sequence, start=1):
        for paragraph in body.split("\n\n")[1:]:
            key = re.sub(r"\W+", " ", paragraph.lower()).strip()
            if len(key.split()) < 4:
                continue
            if key in seen and seen[key] != step:
                issues.append(f"duplicate_paragraph:steps_{seen[key]}_and_{step}")
            else:
                seen.setdefault(key, step)
            words = set(re.findall(r"\b[a-z]{3,}\b", paragraph.lower()))
            if len(words) >= 6:
                for prev_step, prev_words in step_paras:
                    if prev_step != step:
                        overlap = len(words & prev_words) / max(len(words), len(prev_words))
                        if overlap >= 0.75:
                            issues.append(f"redundant_paragraph:steps_{prev_step}_and_{step}")
                step_paras.append((step, words))
    subjects = [subject.lower().strip() for subject, _ in sequence]
    if len(set(subjects)) < len(subjects):
        issues.append("duplicate_subject")
    return issues

