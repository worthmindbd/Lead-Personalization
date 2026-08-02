"""Signal-aware cold email subject lines — specific, lowercase, spam-safe."""

from __future__ import annotations

import hashlib
import re

from personalization.qa import subject_has_spam

# The step whose subject should lead with the lead's own research hook. The
# first touch is the one that has to earn an open from a cold inbox, so a
# specific line beats a segment stock phrase there; later steps rotate through
# the pool so the campaign as a whole stays varied.
HOOK_PREFERRED_STEP = 1

# Segment × step templates. {city} {hook} {category} filled from lead + research.
SUBJECT_TEMPLATES: dict[str, dict[int, list[str]]] = {
    "home_design": {
        1: ["{city} portfolio reel", "{hook}", "site walkthrough pacing"],
        2: [
            "reels vs long walkthroughs",
            "portfolio clip pacing",
            "{city} project reels",
            "second angle on {hook}",
        ],
        3: [
            "post-build video workflow",
            "project video backlog",
            "after the build wraps",
            "closing the loop on {hook}",
        ],
    },
    "real_estate": {
        1: ["{city} listing media", "{hook}", "property tour pacing"],
        2: [
            "agent reel variants",
            "listing clip pacing",
            "partner-facing reels",
            "second angle on {hook}",
        ],
        3: [
            "listing video workflow",
            "walkthrough backlog",
            "who finishes tours",
            "closing the loop on {hook}",
        ],
    },
    "creative_marketing": {
        1: ["client reel finish", "{hook}", "deliverable pacing"],
        2: [
            "hook variants for ads",
            "client cut turnaround",
            "paid social clips",
            "second angle on {hook}",
        ],
        3: [
            "overflow edit workflow",
            "white-label finishing",
            "client video backlog",
            "closing the loop on {hook}",
        ],
    },
    "professional_services": {
        1: ["{city} authority clips", "{hook}", "seminar video finish"],
        2: [
            "webinar clip pacing",
            "education reel cuts",
            "talking-head finish",
            "second angle on {hook}",
        ],
        3: [
            "content backlog question",
            "who edits seminars",
            "partner-facing video",
            "closing the loop on {hook}",
        ],
    },
    "medical_aesthetic": {
        1: ["procedure video finish", "{hook}", "patient education clips"],
        2: [
            "education reel pacing",
            "before/after clip cuts",
            "provider video finish",
            "second angle on {hook}",
        ],
        3: [
            "patient video workflow",
            "in-house vs outsourced",
            "education clip backlog",
            "closing the loop on {hook}",
        ],
    },
    "software_tech": {
        1: ["product demo pacing", "{hook}", "ui walkthrough finish"],
        2: [
            "demo hook variants",
            "screen recording finish",
            "feature clip cuts",
            "second angle on {hook}",
        ],
        3: [
            "demo video workflow",
            "who finishes ui clips",
            "launch video backlog",
            "closing the loop on {hook}",
        ],
    },
    "luxury_retail": {
        1: ["{city} product reels", "{hook}", "catalog vs crave video"],
        2: [
            "dtc ad variants",
            "product clip pacing",
            "social reel finish",
            "second angle on {hook}",
        ],
        3: [
            "product video workflow",
            "seasonal clip backlog",
            "who finishes reels",
            "closing the loop on {hook}",
        ],
    },
    "marine_auto_lifestyle": {
        1: ["{city} showcase reel", "{hook}", "inventory walkthrough"],
        2: [
            "walkaround clip pacing",
            "showroom reel cuts",
            "inventory ad hooks",
            "second angle on {hook}",
        ],
        3: [
            "inventory video workflow",
            "lot footage backlog",
            "who finishes tours",
            "closing the loop on {hook}",
        ],
    },
    "auto_services": {
        1: ["before/after reels", "{hook}", "{city} transformation reels"],
        2: [
            "reveal clip pacing",
            "detail reel cuts",
            "wrap reveal reels",
            "second angle on {hook}",
        ],
        3: [
            "shop video workflow",
            "before/after backlog",
            "who edits your reels",
            "closing the loop on {hook}",
        ],
    },
    "hospitality_events": {
        1: ["{city} event recaps", "{hook}", "venue highlight reels"],
        2: [
            "recap vs raw clips",
            "social highlight cuts",
            "event reel pacing",
            "second angle on {hook}",
        ],
        3: [
            "event video workflow",
            "recap backlog",
            "who finishes highlights",
            "closing the loop on {hook}",
        ],
    },
    "low_fit": {
        1: ["{city} video finish", "{hook}", "site clip pacing"],
        2: [
            "short-form variants",
            "second angle on clips",
            "platform-native cuts",
            "second angle on {hook}",
        ],
        3: [
            "video workflow question",
            "footage backlog",
            "who handles finishing",
            "closing the loop on {hook}",
        ],
    },
}


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


def _hook_from_meta(meta: str) -> str:
    if not meta:
        return ""
    meta = _clean(meta, 80)
    # Drop boilerplate openers
    for prefix in ("Discover ", "Welcome to ", "We are ", "We offer "):
        if meta.startswith(prefix):
            meta = meta[len(prefix) :]
    # First clause often best anchor
    clause = re.split(r"[.;]", meta)[0].strip()
    words = clause.split()
    if len(words) > 5:
        clause = " ".join(words[:5])
    return _clean(clause, 28).lower()


def _hook_from_signal(signal: str) -> str:
    if not signal:
        return ""
    m = re.search(r'site positioning: "(.+?)"', signal, re.I)
    if m:
        return _clean(m.group(1), 28).lower()
    m = re.search(r"leads with (.+?) from ", signal, re.I)
    if m:
        hook = m.group(1).strip()
        if "|" in hook:
            parts = [p.strip() for p in hook.split("|") if p.strip()]
            hook = parts[-1] if parts else hook
        hook = re.sub(r"^(Home|About|Contact)\s*\|\s*", "", hook, flags=re.I)
        if hook.lower() not in {"home", "about", "contact", "welcome"}:
            return _clean(hook, 28).lower()
    m = re.search(r"lists (.+?) and", signal, re.I)
    if m:
        return _clean(m.group(1), 28).lower()
    return ""


def _rotate(items: list[str], key: str, salt: str) -> list[str]:
    """Deterministically rotate ``items`` for one lead.

    Same md5 scheme the copy pools use (``process_batch._pick``), so a lead's
    subject choice is stable across re-runs while different leads in the same
    segment get different lines. Without a key the order is left alone.
    """
    if len(items) < 2 or not key:
        return list(items)
    digest = int(hashlib.md5(f"{salt}:{key}".encode()).hexdigest(), 16)
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
        hook = _clean(hook, 28).lower()
    hook = hook or _hook_from_signal(signal) or _hook_from_meta(meta)

    templates = SUBJECT_TEMPLATES.get(segment, SUBJECT_TEMPLATES["low_fit"]).get(
        step, SUBJECT_TEMPLATES["low_fit"][step]
    )
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
        if subj and not subject_has_spam(subj):
            used_subjects.add(subj)
            return subj

    safe = _clean(hook or category or "your project clips", 40).lower()
    used_subjects.add(safe)
    return safe[:50]
