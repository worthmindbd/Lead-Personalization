"""Deterministic copy engine: assemble 3-email sequences from an offer pack.

Copy contract (dual-tier):
- Greeting is "Hi {first_name}," for person-tier leads (named contact with a
  non-generic address) and "Hi," for company-tier leads — and the company name
  never appears in the body either way.
- Emails 1-2 follow observed issue -> our solution -> soft CTA. Email 3 is the
  breakup (closer + support line + question) and carries no new observation.
- Openers, solutions, and CTAs are drawn from the offer pack's variant pools,
  selected deterministically per lead (stable re-runs, campaign-wide variety).

No LLM is involved: ``_pick`` hashes the lead email to choose a pool index, so
the same lead always gets the same variant and reply rates stay comparable.
"""

from __future__ import annotations

import hashlib
import re
import sys

from lead_personalization.offer_pack import FALLBACK_SEGMENT, OfferPack
from lead_personalization.qa import qa, sequence_issues, subject_has_spam, subject_is_fragment
from lead_personalization.sanitize import sanitize_email
from lead_personalization.segments import greeting_template
from lead_personalization.subjects import build_subject


def _pick(pool: list[str], key: str, salt: str) -> tuple[str, int]:
    digest = int(hashlib.md5(f"{salt}:{key}".encode(), usedforsecurity=False).hexdigest(), 16)
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
            trimmed = " ".join(words[: max(8, len(words) - 5)])
            if trimmed == short:
                # Already at the floor (greeting + CTA alone can exceed the
                # budget); stop instead of spinning forever.
                break
            body_parts[0] = trimmed
    return "\n\n".join([greeting, cta])


def sequence_hook(research: dict) -> str:
    """The prospect text subjects prefer: the LinkedIn topic when that is the
    evidence, else the positioning snippet."""
    if research.get("evidence") == "linkedin_posts" and research.get("linkedin_topic"):
        return research["linkedin_topic"]
    return research.get("snippet") or ""


def _company_ref(row: dict, research: dict) -> str:
    return (row.get("company_name") or research.get("company") or "").strip()


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
    raw_segment = row.get("aevora_segment", FALLBACK_SEGMENT)
    if raw_segment not in offer_pack.segment_copy:
        print(
            f"Warning: unknown aevora_segment {raw_segment!r}; "
            f"falling back to '{FALLBACK_SEGMENT}' copy.",
            file=sys.stderr,
        )
        raw_segment = FALLBACK_SEGMENT
    segment = raw_segment
    seg_copy = offer_pack.segment_solutions(segment)
    evidence = research.get("evidence", "weak")
    if evidence not in offer_pack.openers:
        print(
            f"Warning: unknown evidence {evidence!r}; falling back to 'weak' openers.",
            file=sys.stderr,
        )
        evidence = "weak"
    snippet = research.get("snippet", "")
    li_topic = research.get("linkedin_topic", "")
    channel = research.get("social_channel", "") or "social"
    company = _company_ref(row, research)
    city = (row.get("City") or "").strip()
    state = (row.get("State") or "").strip()
    loc = city or state or "your market"
    # If the company name was parsed as its city, injecting that location would
    # leak the company name into the body — use the state or a neutral phrase.
    # Either direction leaks: "Austin" in "Austin Homes" and "Austin Homes"
    # in "Austin Homes, Texas".
    loc_norm = re.sub(r"[^a-z0-9]", "", loc.lower())
    company_norm = re.sub(r"[^a-z0-9]", "", (company or "").lower())
    if company and loc and (loc_norm in company_norm or company_norm in loc_norm):
        loc = state if (state and re.sub(r"[^a-z0-9]", "", state.lower()) not in company_norm) else "your area"
    peer = peer_phrase(row.get("First_category", ""))

    # Dual-tier greeting: person tier greets by first name when the row's
    # normalized tier says a real, named contact is reachable; everything else
    # gets the safe "Hi,". greeting_template re-validates the name.
    greeting = greeting_template(
        research.get("outreach_tier") or row.get("outreach_tier") or "company",
        research.get("first_name") or row.get("first_name") or "",
        "",
    )

    opener_tmpl, o_idx = _pick(offer_pack.openers[evidence], email, "opener")
    try:
        opener = opener_tmpl.format(
            peer=peer,
            loc=loc,
            snippet=(li_topic if evidence == "linkedin_posts" else snippet),
            channel=channel,
        )
    except (KeyError, IndexError, ValueError):
        opener = offer_pack.openers["weak"][o_idx % len(offer_pack.openers["weak"])].format(
            peer=peer, loc=loc, snippet=snippet, channel=channel,
        )
        evidence = "weak"

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

    hook = sequence_hook(research)
    sequence: list[tuple[str, str]] = []
    used_subjects: set[str] = set()
    for step, parts in enumerate(plans, start=1):
        body = trim_body(greeting, parts[:-1], parts[-1])
        # The hook is the lead's one specific observation; repeating it in all
        # three subjects reads templated ("second angle on X", "closing the
        # loop on X"). Prefer it on step 1, literals after.
        step_hook = hook if step == 1 else ""
        subj = build_subject(
            row,
            research.get("research_signal", ""),
            segment,
            step,
            offer_pack.subject_templates,
            used_subjects=used_subjects,
            hook=step_hook,
            key=email,
        )
        sequence.append((subj, body))

    return sequence, variant


def _retry_body_parts(
    row: dict, research: dict, offer_pack: OfferPack, segment: str, key: str
) -> list[str] | None:
    """An alternate deterministic body plan for fix_sequence repair."""
    try:
        seg_copy = offer_pack.segment_solutions(segment)
        evidence = research.get("evidence", "weak")
        if evidence not in offer_pack.openers:
            evidence = "weak"
        snippet = research.get("snippet", "")
        li_topic = research.get("linkedin_topic", "")
        channel = research.get("social_channel", "") or "social"
        city = (row.get("City") or "").strip()
        state = (row.get("State") or "").strip()
        loc = city or state or "your market"
        company = _company_ref(row, research)
        loc_norm = re.sub(r"[^a-z0-9]", "", loc.lower())
        company_norm = re.sub(r"[^a-z0-9]", "", (company or "").lower())
        if company and loc and (loc_norm in company_norm or company_norm in loc_norm):
            state_norm = re.sub(r"[^a-z0-9]", "", state.lower())
            loc = state if (state and state_norm not in company_norm) else "your area"
        peer = peer_phrase(row.get("First_category", ""))
        opener_tmpl, _ = _pick(offer_pack.openers[evidence], key, "opener")
        opener = opener_tmpl.format(
            peer=peer,
            loc=loc,
            snippet=(li_topic if evidence == "linkedin_posts" else snippet),
            channel=channel,
        )
        solution, _ = _pick(seg_copy["solutions"], key, "solution")
        cta1, _ = _pick(offer_pack.cta_pools[1], key, "cta1")
        return [opener, solution, cta1]
    except (KeyError, IndexError):
        return None


def fix_sequence(
    sequence: list[tuple[str, str]],
    row: dict,
    research: dict,
    offer_pack: OfferPack,
    *,
    key_salt: str = "",
) -> list[tuple[str, str]]:
    segment = row.get("aevora_segment", FALLBACK_SEGMENT)
    if segment not in offer_pack.segment_copy:
        segment = FALLBACK_SEGMENT
    company = _company_ref(row, research)
    signal = research.get("research_signal", "")
    key = (research.get("email") or row.get("primary_email", "")) + key_salt
    # Same hook generate_sequence used: a rebuilt subject must not lose the
    # lead's specific evidence (a LinkedIn hook used to degrade permanently to
    # a stock literal on the first rebuild).
    hook = sequence_hook(research)
    fixed = []
    used_subjects: set[str] = set()
    for step, (subj, body) in enumerate(sequence, start=1):
        if subject_has_spam(subj) or subject_is_fragment(subj) or len(subj) > 60 or subj in used_subjects:
            subj = build_subject(
                row, signal, segment, step, offer_pack.subject_templates,
                used_subjects=used_subjects, hook=hook if step == 1 else "",
                key=key,
            )
        if len(subj) > 60:
            cut = subj[:60]
            subj = cut[: cut.rfind(" ")] if " " in cut else cut
        body = body.replace("—", "-").replace("…", "")
        subj, body = sanitize_email(subj, body)
        q = qa(subj, body, company)
        if not q["pass"]:
            if q["word_count"] > 100:
                lines = body.split("\n\n")
                while len(lines) > 2 and qa(subj, "\n\n".join(lines), company)["word_count"] > 100:
                    lines.pop(-2)
                body = "\n\n".join(lines)
            q = qa(subj, body, company)
            if not q["pass"]:
                # generate_sequence is clean today, but any future pack edit or
                # snippet leak that introduces banned/spam/hard-CTA/company
                # content must not ship as-is: try alternate deterministic
                # variants and keep the first passing one.
                rebuilt = False
                for attempt in range(1, 4):
                    retry_key = f"{key}#fix{attempt}"
                    retry_parts = _retry_body_parts(row, research, offer_pack, segment, retry_key)
                    if retry_parts is None:
                        continue
                    greeting = greeting_template(
                        research.get("outreach_tier") or row.get("outreach_tier") or "company",
                        research.get("first_name") or row.get("first_name") or "",
                        "",
                    )
                    cand_body = trim_body(greeting, retry_parts[:-1], retry_parts[-1])
                    cand_subj = build_subject(
                        row, signal, segment, step, offer_pack.subject_templates,
                        used_subjects=set(used_subjects),
                        hook=hook if step == 1 else "", key=retry_key,
                    )
                    cand_subj, cand_body = sanitize_email(cand_subj, cand_body)
                    if qa(cand_subj, cand_body, company)["pass"]:
                        subj, body = cand_subj, cand_body
                        rebuilt = True
                        break
                if not rebuilt:
                    print(
                        f"Warning: fix_sequence could not repair step {step} for "
                        f"{key!r}: {q['issues']}; shipping best effort.",
                        file=sys.stderr,
                    )
        used_subjects.add(subj)
        fixed.append((subj, body))
    dupes = sequence_issues(fixed)
    if dupes:
        # Cross-step duplicates (same paragraph/subject twice) are not fixed by
        # per-step repair; flag rather than silently ship.
        print(
            f"Warning: sequence_issues after fix for {key!r}: {dupes}",
            file=sys.stderr,
        )
    return fixed
