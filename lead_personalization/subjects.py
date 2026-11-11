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
    company_name_in_subject,
    hook_start_is_filler,
    is_probably_not_english,
    junk_hook_reasons,
    subject_has_spam,
    subject_is_fragment,
)
from lead_personalization.segments import canonical_segment

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
        text = cut
    # Always, not only when truncating: prospect text that is already short
    # enough still arrives as "video production," or "event video &".
    return _strip_trailing(text)


def _strip_trailing(text: str) -> str:
    """Drop dangling list punctuation and connectors from a phrase's end."""
    prev = None
    while text and text != prev:
        prev = text
        text = text.rstrip(" ,;:-&+/(.'\"")
        words = text.split()
        if words and words[-1] in {"&", "+", "and", "or", "&amp;"}:
            text = " ".join(words[:-1])
    return text


def _trim_to_content_word(text: str, max_len: int = 36, min_words: int = 2) -> str:
    """Fit prospect text into ``max_len`` chars without cutting mid-phrase.

    Prospect hooks are raw site copy. A blind word-boundary cut still lands
    mid-thought ("record something worth", "jillian nielsen is a langley"),
    so the text is used whole when it fits, else cut at the first natural
    clause boundary (sentence end, comma, dash, ampersand, pipe) that fits.
    When neither works it returns "" and the caller uses a literal template:
    a stock subject beats a broken one.
    """
    text = re.sub(r"\s+", " ", (text or "")).strip()
    if not text:
        return ""
    # "Sussex Wedding Photographer. A ..." -> "Sussex Wedding Photographer".
    # Only the FIRST sentence-level break counts: a comma or a later break
    # cuts mid-thought ("neuen films creates emotional"), and a hook carrying
    # two sentences ("your entire event. one team") reads as a pasted tagline.
    first_break = re.search(r"[.;:!?|]\s|\s[-–|/]\s", text)
    candidates = [text[: first_break.start()]] if first_break else [text]
    for cand in candidates:
        cand = _strip_trailing(cand.strip())
        if not cand or len(cand) > max_len:
            continue
        words = cand.split()
        while words and words[-1].lower().strip(".,;:&+") in FUNCTION_WORDS:
            words.pop()
        content_words = [w for w in words if w.lower().strip(".,;:&+") not in FUNCTION_WORDS]
        if len(content_words) < min_words:
            continue
        return _clean(" ".join(words), max_len).lower()
    return ""


def _usable_hook(hook: str) -> str:
    """Reject a hook that reads as unfiltered data, not a phrase.

    The raw GMB Meta_Description is the last hook source and it is unfiltered:
    it has shipped "wordpress error", "call (561) 368-0770", "2401 pga blvd.,
    suite 270" and the company's own name as subject lines. Rejecting here means
    the caller falls through to a literal template instead.
    """
    hook = (hook or "").strip()
    if not hook or junk_hook_reasons(hook) or hook_start_is_filler(hook):
        return ""
    if is_probably_not_english(hook):
        return ""
    if re.search(r"[#*_<>{}\[\]=]", hook):
        return ""
    return hook


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
    return _usable_hook(_trim_to_content_word(clause))


def _hook_from_signal(signal: str) -> str:
    if not signal:
        return ""
    # The exact phrasings build_signal emits; research.py owns the other half
    # of this contract (tests pin the round trip).
    m = re.search(r'recent LinkedIn post: "(.+?)"', signal, re.I)
    if m:
        return _usable_hook(_trim_to_content_word(m.group(1)))
    m = re.search(r'site positioning: "(.+?)"', signal, re.I)
    if m:
        return _usable_hook(_trim_to_content_word(m.group(1)))
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
    company = (row.get("company_name") or "").strip()
    city = (row.get("City") or "").strip()
    category = (row.get("First_category") or "").strip()
    meta = (row.get("Meta_Description") or "").strip()
    if hook:
        # A caller-supplied hook is the same kind of prospect text the
        # extractors below pull from meta/signal, so trim and vet it the same
        # way: a whole clause or nothing, and never junk or filler.
        hook = _usable_hook(_trim_to_content_word(hook))
    hook = hook or _hook_from_signal(signal) or _hook_from_meta(meta)

    fallback = subject_templates["general"]
    templates = subject_templates.get(canonical_segment(segment), fallback).get(step) or fallback.get(step)
    if not templates:
        raise ValueError(f"no subject templates for segment={segment!r} step={step}")
    templates = _order_templates(list(templates), has_hook=bool(hook), key=key, step=step)

    candidates: list[str] = []
    for tmpl in templates:
        if "{city}" in tmpl and not city:
            # "your market studio edits" reads as an unfilled mail merge.
            continue
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
        # Reject fragments ("a wide selection of") and unfiltered data (a phone
        # number, a street address, a CMS error page). Literal templates never
        # trip either, so a clean fallback candidate always remains.
        if (
            subj
            and not subject_has_spam(subj)
            and not subject_is_fragment(subj)
            and not junk_hook_reasons(subj)
            and not (company and company_name_in_subject(subj, company))
        ):
            used_subjects.add(subj)
            return subj

    safe = _clean(hook or category or "your project clips", 40).lower()
    if (
        subject_is_fragment(safe)
        or subject_has_spam(safe)
        or junk_hook_reasons(safe)
        or (company and company_name_in_subject(safe, company))
    ):
        # The raw hook landed on a function word, carries a spam trigger, or
        # leaks the company name; prefer the category or generic phrase.
        safe = _clean(category or "your project clips", 40).lower()
    if (
        subject_has_spam(safe)
        or subject_is_fragment(safe)
        or junk_hook_reasons(safe)
        or (company and company_name_in_subject(safe, company))
    ):
        safe = "video workflow question"
    used_subjects.add(safe)
    return safe[:50]
