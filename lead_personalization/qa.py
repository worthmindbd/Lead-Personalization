#!/usr/bin/env python3
"""Shared QA checks for personalized email copy."""

from __future__ import annotations

import re

from lead_personalization.segments import is_plausible_first_name

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
    "—",
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
    "act now",
    "limited time",
    "guarantee",
    "100% free",
    "click here",
    "buy now",
    "no obligation",
    "risk-free",
    "amazing offer",
    "incredible results",
]

# Subject-only spam triggers (filters + skim filter)
SUBJECT_SPAM_WORDS = [
    "free",
    "guaranteed",
    "guarantee",
    "urgent",
    "act now",
    "limited time",
    "click here",
    "buy now",
    "winner",
    "congratulations",
    "100%",
    "no obligation",
    "exclusive offer",
    "save big",
    "reminder",
    "last chance",
    "amazing",
    "incredible",
    "discount",
    "!!!",
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
]

# Truncation artifacts from snippet clipping must never reach a prospect.
ELLIPSIS_MARKS = ("...", "\u2026")


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def contains_forbidden(text: str) -> bool:
    """True when text carries banned, brand-forbidden, or spam-trigger content."""
    low = (text or "").lower()
    return (
        any(b in low for b in BANNED)
        or any(w in low for w in BRAND_FORBIDDEN)
        or any(t in low for t in SPAM_TRIGGERS)
    )


def subject_has_spam(subject: str) -> bool:
    low = subject.lower().strip()
    words = subject.split()
    if sum(1 for w in words if w.isupper() and len(w) > 2) >= 2:
        return True
    if "!" in subject:
        return True
    for trigger in SUBJECT_SPAM_WORDS:
        if trigger in low:
            return True
    for word in BRAND_FORBIDDEN:
        if word.strip() in low:
            return True
    return False


def greeting_line(body: str) -> str:
    return (body.split("\n\n")[0] if body else "").strip()


def greeting_is_valid(body: str) -> bool:
    line = greeting_line(body)
    if line == "Hi,":
        return True
    match = re.match(r"^Hi (.+),$", line)
    if not match:
        return False
    return is_plausible_first_name(match.group(1))


def qa(subject: str, body: str, company: str = "") -> dict:
    issues = []
    wc = word_count(body)
    if wc > 100:
        issues.append(f"word count {wc}>100")
    if len(subject) > 60:
        issues.append(f"subject len {len(subject)}>60")
    if subject_has_spam(subject):
        issues.append("subject_spam_or_generic")
    if not greeting_is_valid(body):
        issues.append("bad_greeting")
    for mark in ELLIPSIS_MARKS:
        if mark in subject or mark in body:
            issues.append("truncation_artifact")
            break
    company_clean = (company or "").strip()
    if len(company_clean) >= 4 and company_clean.lower() in body.lower():
        issues.append("company_name_in_body")
    low = (subject + " " + body).lower()
    for banned in BANNED:
        if banned in low:
            issues.append(f"banned:{banned}")
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


def qa_sequence(sequence: list[tuple[str, str]], company: str = "") -> list[dict]:
    return [qa(subject, body, company) for subject, body in sequence]


def sequence_issues(sequence: list[tuple[str, str]]) -> list[str]:
    """Cross-step checks: no duplicate paragraphs or subjects across the sequence."""
    issues: list[str] = []
    seen: dict[str, int] = {}
    for step, (_, body) in enumerate(sequence, start=1):
        for paragraph in body.split("\n\n")[1:]:
            key = re.sub(r"\W+", " ", paragraph.lower()).strip()
            if len(key.split()) < 4:
                continue
            if key in seen and seen[key] != step:
                issues.append(f"duplicate_paragraph:steps_{seen[key]}_and_{step}")
            else:
                seen.setdefault(key, step)
    subjects = [subject.lower().strip() for subject, _ in sequence]
    if len(set(subjects)) < len(subjects):
        issues.append("duplicate_subject")
    return issues
