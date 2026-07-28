"""Deterministic copy engine: assemble 3-email sequences from an offer pack.

Copy contract (GMB / company-tier lists):
- Greeting is always "Hi," — no person name, no company name anywhere in body.
- Email structure: observed issue -> our solution -> soft CTA.
- Openers, solutions, and CTAs are drawn from the offer pack's variant pools,
  selected deterministically per lead (stable re-runs, campaign-wide variety).

No LLM is involved: ``_pick`` hashes the lead email to choose a pool index, so
the same lead always gets the same variant and reply rates stay comparable.
"""

from __future__ import annotations

import hashlib
import re

from lead_personalization.offer_pack import OfferPack
from lead_personalization.qa import qa, subject_has_spam
from lead_personalization.sanitize import sanitize_email
from lead_personalization.subjects import build_subject


def _pick(pool: list[str], key: str, salt: str) -> tuple[str, int]:
    digest = int(hashlib.md5(f"{salt}:{key}".encode()).hexdigest(), 16)
    idx = digest % len(pool)
    return pool[idx], idx


def peer_phrase(category: str) -> str:
    cat = (category or "").strip().lower()
    return f"{cat} teams" if cat else "teams in your space"


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


def generate_sequence(
    row: dict,
    research: dict,
    offer_pack: OfferPack,
    *,
    key_salt: str = "",
) -> tuple[list[tuple[str, str]], str]:
    """Build the 3-email sequence. Returns (sequence, copy_variant).

    ``key_salt`` perturbs the deterministic variant selection; leaving it empty
    reproduces the canonical per-lead copy, while a non-empty value (used by the
    app's "regenerate" action) rotates to a different, still-stable combination.
    """
    email = (research.get("email") or row.get("primary_email", "")) + key_salt
    segment = row.get("aevora_segment", "low_fit")
    seg_copy = offer_pack.segment_solutions(segment)
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

    greeting = offer_pack.greeting

    opener_tmpl, o_idx = _pick(offer_pack.openers[evidence], email, "opener")
    opener = opener_tmpl.format(
        peer=peer,
        loc=loc,
        snippet=(li_topic if evidence == "linkedin_posts" else snippet),
        channel=channel,
    )

    solution, s_idx = _pick(seg_copy["solutions"], email, "solution")
    alt_solution = seg_copy["solutions"][(s_idx + 1) % len(seg_copy["solutions"])]
    angle2, a_idx = _pick(seg_copy["second_angle"], email, "angle2")
    closer, cl_idx = _pick(offer_pack.closers, email, "closer")
    support, su_idx = _pick(offer_pack.support_lines, email, "support")
    cta1, c1 = _pick(offer_pack.cta_pools[1], email, "cta1")
    cta2, c2 = _pick(offer_pack.cta_pools[2], email, "cta2")
    cta3, c3 = _pick(offer_pack.cta_pools[3], email, "cta3")

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
            offer_pack.subject_templates,
            used_subjects=used_subjects,
            hook=hook,
        )
        sequence.append((subj, body))

    return sequence, variant


def fix_sequence(
    sequence: list[tuple[str, str]],
    row: dict,
    research: dict,
    offer_pack: OfferPack,
) -> list[tuple[str, str]]:
    segment = row.get("aevora_segment", "low_fit")
    company = research.get("company", "")
    signal = research.get("research_signal", "")
    fixed = []
    used_subjects: set[str] = set()
    for step, (subj, body) in enumerate(sequence, start=1):
        if subject_has_spam(subj) or len(subj) > 60 or subj in used_subjects:
            subj = build_subject(
                row, signal, segment, step, offer_pack.subject_templates,
                used_subjects=used_subjects,
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
