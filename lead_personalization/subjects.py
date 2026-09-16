"""Signal-aware cold email subject lines — specific, lowercase, spam-safe.

Subject templates now live in the offer pack (see offer_pack.py); ``build_subject``
takes the ``subject_templates`` mapping as an argument instead of reading a
module-level constant.
"""

from __future__ import annotations

import hashlib
import re

from lead_personalization.qa import (  # noqa: F401 — FUNCTION_WORDS re-exported below
    FUNCTION_WORDS,
    subject_has_spam,
    subject_is_fragment,
)

# The step whose subject should lead with the lead's own research hook. The
# first touch is the one that has to earn an open from a cold inbox, so a
# specific line beats a segment stock phrase there; later steps rotate through
# the pool so the campaign as a whole stays varied.
HOOK_PREFERRED_STEP = 1


def _clean(text: str, max_len: int = 32) -> str:
    """Trim to max_len at a word boundary — never emit '...' artifacts."""
    text = re.sub(r"\s+", " ", (text or "")).strip()
    text = text.replace("—", "-").replace("|", " ").replace("\u2026", "")
    text = text.replace("...", " ")
    text = re.sub(r"\s{2,}", " ", text).strip()
    if len(text) > max_len:
        cut = text[:max_len]
        if " " in cut:
            cut = cut[: cut.rfind(" ")]
        text = cut.rstrip(" ,;:-")
    return text


def _trim_to_content_word(text: str, max_len: int = 28, min_words: int = 2) -> str:
    """Trim ``text`` to at most ``max_len`` chars ending on a content word.

    Prospect-supplied hooks are raw site copy; cutting them at a word boundary
    (``_clean``) can still land mid-phrase on a function word — "a wide
    selection of". This walks the words, then trims back past any trailing
    closed-class words. Returns "" when fewer than ``min_words`` content words
    remain, so the caller falls back to a literal template rather than ship a
    fragment.
    """
    words = (text or "").strip().split()
    out: list[str] = []
    length = 0
    for w in words:
        add = (length + len(w) + (1 if out else 0))
        if add > max_len:
            break
        out.append(w)
        length = add
    while out and out[-1].lower().strip(".,;:") in FUNCTION_WORDS:
        out.pop()
    if len(out) < min_words:
        return ""
    return _clean(" ".join(out), max_len).lower()


def _hook_from_meta(meta: str) -> str:
    if not meta:
        return ""
    meta = _clean(meta, 80)
    # Drop boilerplate openers
    for prefix in ("Discover ", "Welcome to ", "We are ", "We offer "):
        if meta.startswith(prefix):
            meta = meta[len(prefix) :]
    # First clause is often the best anchor; trim it to a coherent phrase.
    clause = re.split(r"[.;]", meta)[0].strip()
    return _trim_to_content_word(clause)


def _hook_from_signal(signal: str) -> str:
    if not signal:
        return ""
    # The exact phrasings build_signal emits; research.py owns the other half
    # of this contract (tests pin the round trip).
    m = re.search(r'recent LinkedIn post: "(.+?)"', signal, re.I)
    if m:
        return _trim_to_content_word(m.group(1))
    m = re.search(r'site positioning: "(.+?)"', signal, re.I)
    if m:
        return _trim_to_content_word(m.group(1))
    m = re.search(r"leads with (.+?) from ", signal, re.I)
    if m:
        hook = m.group(1).strip()
        if "|" in hook:
            parts = [p.strip() for p in hook.split("|") if p.strip()]
            hook = parts[-1] if parts else hook
        hook = re.sub(r"^(Home|About|Contact)\s*\|\s*", "", hook, flags=re.I)
        if hook.lower() not in {"home", "about", "contact", "welcome"}:
            return _trim_to_content_word(hook)
    m = re.search(r"lists (.+?) and", signal, re.I)
    if m:
        return _trim_to_content_word(m.group(1))
    return ""


def _rotate(items: list[str], key: str, salt: str) -> list[str]:
    """Deterministically rotate ``items`` for one lead.

    Same md5 scheme the copy pools use (``copywriter._pick``), so a lead's
    subject choice is stable across re-runs while different leads in the same
    segment get different lines. Without a key the order is left alone.
    """
    if len(items) < 2 or not key:
        return list(items)
    digest = int(hashlib.md5(f"{salt}:{key}".encode(), usedforsecurity=False).hexdigest(), 16)
    offset = digest % len(items)
    return items[offset:] + items[:offset]


def _order_templates(templates: list[str], *, has_hook: bool, key: str, step: int) -> list[str]:
    """Order one step's templates: hook first when it can carry the line.

    Templates are tried in order and the first spam-free candidate wins, so
    position is the whole decision. A ``{hook}`` template placed after a
    literal is unreachable — which is why the hook used to never ship.
    """
    hooked = [t for t in templates if "{hook}" in t]
    literals = [t for t in templates if "{hook}" not in t]
    if has_hook and step == HOOK_PREFERRED_STEP:
        return hooked + _rotate(literals, key, f"subject{step}")
    if has_hook:
        # Later steps: the hook is one option among the literals, not the default.
        return _rotate(hooked + literals, key, f"subject{step}")
    # No hook to fill it with — ``_fill`` would substitute the category, which
    # the literals already say better.
    return _rotate(literals, key, f"subject{step}") + hooked


def _fill(template: str, city: str, hook: str, category: str) -> str:
    city = _clean(city, 18).title() if city else ""
    category = _clean(category, 20).lower() if category else ""
    hook = hook or category or "your site clips"
    out = (
        template.replace("{city}", city or "your market")
        .replace("{hook}", hook)
        .replace("{category}", category)
    )
    return out.strip().lower()


def build_subject(
    row: dict,
    signal: str,
    segment: str,
    step: int,
    subject_templates: dict[str, dict[int, list[str]]],
    *,
    used_subjects: set[str] | None = None,
    hook: str = "",
    key: str = "",
) -> str:
    """Build a specific, spam-safe subject (target ≤50 chars, prefer ≤33).

    ``key`` is the lead's stable identity (its email, as used for the copy
    pools). It only selects *which* template is tried first; every candidate
    still has to clear ``subject_has_spam`` and the length cap.
    """
    used_subjects = used_subjects or set()
    city = (row.get("City") or "").strip()
    category = (row.get("First_category") or "").strip()
    meta = (row.get("Meta_Description") or "").strip()
    if hook:
        # A caller-supplied hook is the same kind of prospect text the
        # extractors below pull from meta/signal, so trim it the same coherent
        # way — to a prefix that ends on a content word, not a blind word slice.
        hook = _trim_to_content_word(hook)
    hook = hook or _hook_from_signal(signal) or _hook_from_meta(meta)

    fallback = subject_templates["low_fit"]
    templates = subject_templates.get(segment, fallback).get(step) or fallback.get(step)
    if not templates:
        raise ValueError(f"no subject templates for segment={segment!r} step={step}")
    templates = _order_templates(list(templates), has_hook=bool(hook), key=key, step=step)

    candidates: list[str] = []
    for tmpl in templates:
        subj = _fill(tmpl, city, hook, category)
        if subj and subj not in used_subjects:
            candidates.append(subj)

    # Fallback: city + segment keyword
    fallbacks = {
        1: f"{city} {category.split()[0].lower()} reel" if city and category else "",
        2: f"second angle / {category.split()[0].lower()}" if category else "",
        3: "video workflow question",
    }
    fb = (fallbacks.get(step) or "").strip().lower()
    if fb and fb not in candidates:
        candidates.append(fb)

    for subj in candidates:
        # Word-boundary trim: a hook is prospect-supplied text and can be long,
        # and a subject cut mid-word reads like a broken send.
        subj = _clean(subj, 50)
        # Reject fragments: a hook that lands on a function word ("a wide
        # selection of") is a broken send too. Literal templates never end on a
        # function word, so a clean fallback candidate always remains.
        if subj and not subject_has_spam(subj) and not subject_is_fragment(subj):
            used_subjects.add(subj)
            return subj

    safe = _clean(hook or category or "your project clips", 40).lower()
    if subject_is_fragment(safe) or subject_has_spam(safe):
        # The raw hook landed on a function word or carries a spam trigger;
        # prefer the category or a generic phrase over a broken send.
        safe = _clean(category or "your project clips", 40).lower()
    if subject_has_spam(safe) or subject_is_fragment(safe):
        safe = "video workflow question"
    used_subjects.add(safe)
    return safe[:50]
