#!/usr/bin/env python3
"""Guard email copy against forbidden content leaked from prospect sources.

Strategy: never word-strip a prospect's own text (that mangles grammar).
If a harvested snippet or paragraph carries a forbidden term, drop the whole
snippet/paragraph and let the copy engine fall back to a clean variant.
"""

from __future__ import annotations

import re

from personalization.qa import BRAND_FORBIDDEN, SPAM_TRIGGERS, contains_forbidden

# Longer phrases first so partial strips do not leave junk.
_FORBIDDEN = sorted(
    {w.strip() for w in BRAND_FORBIDDEN + SPAM_TRIGGERS if w.strip()},
    key=len,
    reverse=True,
)
_GIG_PATTERN = re.compile(r" gig", re.I)


def sanitize_text(text: str) -> str:
    """Remove brand-forbidden and spam-trigger tokens from short free text.

    Only intended for generated fragments (e.g. subject hooks), never for
    prose paragraphs — use paragraph dropping for those.
    """
    if not text:
        return text
    result = text
    result = _GIG_PATTERN.sub("", result)
    for word in _FORBIDDEN:
        if word == "gig":
            continue
        result = re.compile(re.escape(word), re.I).sub("", result)
    result = re.sub(r"\s+", " ", result)
    result = re.sub(r"\s+([,.;:])", r"\1", result)
    result = re.sub(r"\s{2,}", " ", result)
    return result.strip(" ,;.-")


def sanitize_signal(signal: str) -> str:
    """research_signal is internal (never pasted into copy); pass through."""
    return signal or ""


def sanitize_email(subject: str, body: str) -> tuple[str, str]:
    """Final guard: drop any non-greeting paragraph with forbidden content.

    The copy engine vets snippets up front, so this should be a no-op in
    practice. When it does fire, QA still validates the remaining copy.
    """
    subj = sanitize_text(subject) if contains_forbidden(subject) else subject
    paragraphs = body.split("\n\n")
    if len(paragraphs) <= 1:
        return subj, body
    greeting, rest = paragraphs[0], paragraphs[1:]
    kept = [p for p in rest if not contains_forbidden(p)]
    if not kept:
        kept = rest[-1:]  # keep the CTA rather than sending a bare greeting
    return subj, "\n\n".join([greeting] + kept)
