"""Signal-aware cold email subject lines — specific, lowercase, spam-safe."""

from __future__ import annotations

import re

from personalization.qa import subject_has_spam

# Segment × step templates. {city} {hook} {category} filled from lead + research.
SUBJECT_TEMPLATES: dict[str, dict[int, list[str]]] = {
    "home_design": {
        1: ["{city} portfolio reel", "{hook}", "site walkthrough pacing"],
        2: ["reels vs long walkthroughs", "portfolio clip pacing", "{city} project reels"],
        3: ["post-build video workflow", "project video backlog", "after the build wraps"],
    },
    "real_estate": {
        1: ["{city} listing media", "{hook}", "property tour pacing"],
        2: ["agent reel variants", "listing clip pacing", "partner-facing reels"],
        3: ["listing video workflow", "walkthrough backlog", "who finishes tours"],
    },
    "creative_marketing": {
        1: ["client reel finish", "{hook}", "deliverable pacing"],
        2: ["hook variants for ads", "client cut turnaround", "paid social clips"],
        3: ["overflow edit workflow", "white-label finishing", "client video backlog"],
    },
    "professional_services": {
        1: ["{city} authority clips", "{hook}", "seminar video finish"],
        2: ["webinar clip pacing", "education reel cuts", "talking-head finish"],
        3: ["content backlog question", "who edits seminars", "partner-facing video"],
    },
    "medical_aesthetic": {
        1: ["procedure video finish", "{hook}", "patient education clips"],
        2: ["education reel pacing", "before/after clip cuts", "provider video finish"],
        3: ["patient video workflow", "in-house vs outsourced", "education clip backlog"],
    },
    "software_tech": {
        1: ["product demo pacing", "{hook}", "ui walkthrough finish"],
        2: ["demo hook variants", "screen recording finish", "feature clip cuts"],
        3: ["demo video workflow", "who finishes ui clips", "launch video backlog"],
    },
    "luxury_retail": {
        1: ["{city} product reels", "{hook}", "catalog vs crave video"],
        2: ["dtc ad variants", "product clip pacing", "social reel finish"],
        3: ["product video workflow", "seasonal clip backlog", "who finishes reels"],
    },
    "marine_auto_lifestyle": {
        1: ["{city} showcase reel", "{hook}", "inventory walkthrough"],
        2: ["walkaround clip pacing", "showroom reel cuts", "inventory ad hooks"],
        3: ["inventory video workflow", "lot footage backlog", "who finishes tours"],
    },
    "auto_services": {
        1: ["before/after reels", "{hook}", "{city} transformation reels"],
        2: ["reveal clip pacing", "detail reel cuts", "wrap reveal reels"],
        3: ["shop video workflow", "before/after backlog", "who edits your reels"],
    },
    "hospitality_events": {
        1: ["{city} event recaps", "{hook}", "venue highlight reels"],
        2: ["recap vs raw clips", "social highlight cuts", "event reel pacing"],
        3: ["event video workflow", "recap backlog", "who finishes highlights"],
    },
    "low_fit": {
        1: ["{city} video finish", "{hook}", "site clip pacing"],
        2: ["short-form variants", "second angle on clips", "platform-native cuts"],
        3: ["video workflow question", "footage backlog", "who handles finishing"],
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
) -> str:
    """Build a specific, spam-safe subject (target ≤50 chars, prefer ≤33)."""
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
        subj = subj[:50]
        if not subject_has_spam(subj):
            used_subjects.add(subj)
            return subj

    safe = _clean(hook or category or "your project clips", 40).lower()
    used_subjects.add(safe)
    return safe[:50]
