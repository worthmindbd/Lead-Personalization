"""Signal-aware cold email subject lines — specific, lowercase, spam-safe.

Subject templates now live in the offer pack (see offer_pack.py); ``build_subject``
takes the ``subject_templates`` mapping as an argument instead of reading a
module-level constant.
"""

from __future__ import annotations

import re

from lead_personalization.qa import subject_has_spam


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
    subject_templates: dict[str, dict[int, list[str]]],
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

    fallback = subject_templates["low_fit"]
    templates = subject_templates.get(segment, fallback).get(step, fallback[step])

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
