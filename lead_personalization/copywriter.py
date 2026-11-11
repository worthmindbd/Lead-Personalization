"""Deterministic copy engine: assemble 3-email sequences from an offer pack.

Copy contract (dual-tier):
- Greeting rotates per lead: "{Hi|Hey|Hello} {first_name}," or "{first_name},"
  for person-tier leads (named contact with a non-generic address), and a bare
  "Hi,/Hey,/Hello," for company-tier leads. The company name never appears in
  the greeting or body.
- The first line after the greeting is about the client, never the sender.
- Email 1: observation -> what we do -> soft CTA. Email 2: new angle -> one
  concrete proof point -> soft CTA. Email 3 is the breakup (closer + support
  line + question) and carries no new observation.
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

# Segment that a row's category overrides into even when its stored
# aevora_segment predates it (see resolve_segment).
STUDIO_SEGMENT = "production_studios"
from lead_personalization.qa import (
    contains_forbidden,
    qa,
    sequence_issues,
    subject_has_spam,
    subject_is_fragment,
)
from lead_personalization.sanitize import sanitize_email
from lead_personalization.segments import (
    canonical_segment,
    greeting_template,
    peer_phrase,
    segment_for_category,
)
from lead_personalization.subjects import build_subject


def _pick(pool: list[str], key: str, salt: str) -> tuple[str, int]:
    digest = int(hashlib.md5(f"{salt}:{key}".encode(), usedforsecurity=False).hexdigest(), 16)
    idx = digest % len(pool)
    return pool[idx], idx


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


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def resolve_loc(row: dict, research: dict) -> str:
    """City, else state, else a neutral phrase, never leaking the company name.

    If the company name was parsed as its city, injecting that location would
    leak the company name into the body. Either direction leaks: "Austin" in
    "Austin Homes" and "Austin Homes" in "Austin Homes, Texas".
    """
    city = (row.get("City") or "").strip()
    state = (row.get("State") or "").strip()
    loc = city or state or "your market"
    company_norm = _norm(_company_ref(row, research))
    loc_norm = _norm(loc)
    if company_norm and loc_norm and (loc_norm in company_norm or company_norm in loc_norm):
        loc = state if (state and _norm(state) not in company_norm) else "your area"
    return loc


def resolve_segment(row: dict, offer_pack: OfferPack, *, warn: bool = False) -> str:
    """The copy angle for a row.

    Rows normalized before ``production_studios`` existed carry
    ``creative_marketing`` or ``general`` for studios and photographers; their
    category still says what they are, so it wins for that one segment.
    """
    segment = canonical_segment(row.get("aevora_segment", FALLBACK_SEGMENT))
    by_category = segment_for_category(row.get("First_category", ""))
    if by_category == STUDIO_SEGMENT and by_category in offer_pack.segment_copy:
        return by_category
    if segment not in offer_pack.segment_copy:
        if warn:
            print(
                f"Warning: unknown aevora_segment {segment!r}; "
                f"falling back to '{FALLBACK_SEGMENT}' copy.",
                file=sys.stderr,
            )
        segment = FALLBACK_SEGMENT
    return segment


def _render_opener(
    row: dict, research: dict, offer_pack: OfferPack, segment: str, key: str, *, warn: bool = False
) -> tuple[str, str, int]:
    """Pick and fill the opener. Returns (opener, evidence actually used, index)."""
    evidence = research.get("evidence", "weak")
    if evidence not in offer_pack.openers:
        if warn:
            print(
                f"Warning: unknown evidence {evidence!r}; falling back to 'weak' openers.",
                file=sys.stderr,
            )
        evidence = "weak"
    fields = {
        "peer": peer_phrase(row.get("First_category", "")),
        "loc": resolve_loc(row, research),
        "snippet": (
            research.get("linkedin_topic", "") if evidence == "linkedin_posts"
            else research.get("snippet", "")
        ),
        "channel": research.get("social_channel", "") or "social",
    }
    pool = offer_pack.opener_pool(segment, evidence)
    tmpl, idx = _pick(pool, key, "opener")
    if "{snippet}" in tmpl and not fields["snippet"]:
        tmpl = ""  # never render an empty quote: ""
    try:
        if tmpl:
            opener = _sentence_case(tmpl.format(**fields))
            # A quoted snippet carrying a forbidden word would get the whole
            # line dropped by sanitize_email, leaving an email with no
            # observation at all ("Hi,\n\nWe plug in..."). Use the honest
            # generic line instead.
            if not contains_forbidden(opener):
                return opener, evidence, idx
    except (KeyError, IndexError, ValueError):
        pass
    weak = offer_pack.opener_pool(segment, "weak")
    return _sentence_case(weak[idx % len(weak)].format(**fields)), "weak", idx


def _sentence_case(text: str) -> str:
    """Capitalize the first letter even behind an opening quote:
    '"how we cut..." from your post' -> '"How we cut..." from your post'."""
    for i, ch in enumerate(text):
        if ch.isalpha():
            return text[:i] + ch.upper() + text[i + 1:]
    return text


def _greeting(row: dict, research: dict, key: str) -> str:
    # Dual-tier greeting: person tier greets by first name when the row's
    # normalized tier says a real, named contact is reachable; everything else
    # gets a bare rotated "Hi,/Hey,/Hello,". greeting_template re-validates the
    # name and uses the address to corroborate it and to pick the rotation.
    return greeting_template(
        research.get("outreach_tier") or row.get("outreach_tier") or "company",
        research.get("first_name") or row.get("first_name") or "",
        " ".join(filter(None, (_company_ref(row, research), row.get("Name") or ""))),
        key,
    )


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

    Email 1: observation -> what we do -> soft CTA.
    Email 2: a new angle -> one concrete proof point (not the pitch again) -> CTA.
    Email 3: breakup closer -> support line -> a question.
    """
    email = (research.get("email") or row.get("primary_email", "")) + key_salt
    segment = resolve_segment(row, offer_pack, warn=True)
    seg_copy = offer_pack.segment_solutions(segment)
    greeting = _greeting(row, research, email)
    opener, evidence, o_idx = _render_opener(row, research, offer_pack, segment, email, warn=True)

    solution, s_idx = _pick(seg_copy["solutions"], email, "solution")
    angle2, a_idx = _pick(seg_copy["second_angle"], email, "angle2")
    if offer_pack.proof_lines:
        proof, p_idx = _pick(offer_pack.proof_lines, email, "proof")
    else:
        p_idx = (s_idx + 1) % len(seg_copy["solutions"])
        proof = seg_copy["solutions"][p_idx]
    closer, cl_idx = _pick(offer_pack.closers, email, "closer")
    support, su_idx = _pick(offer_pack.support_lines, email, "support")
    cta1, c1 = _pick(offer_pack.cta_pools[1], email, "cta1")
    cta2, c2 = _pick(offer_pack.cta_pools[2], email, "cta2")
    cta3, c3 = _pick(offer_pack.cta_pools[3], email, "cta3")

    plans = [
        [opener, solution, cta1],
        [angle2, proof, cta2],
        [closer, support, cta3],
    ]

    variant = (
        f"{evidence}.o{o_idx}s{s_idx}a{a_idx}p{p_idx}cl{cl_idx}su{su_idx}c{c1}{c2}{c3}"
    )

    hook = sequence_hook(research)
    sequence: list[tuple[str, str]] = []
    used_subjects: set[str] = set()
    for step, parts in enumerate(plans, start=1):
        body = trim_body(greeting, parts[:-1], parts[-1])
        # The hook is the lead's one specific observation; repeating it in all
        # three subjects reads templated. Prefer it on step 1, literals after.
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
        opener, _, _ = _render_opener(row, research, offer_pack, segment, key)
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
    segment = resolve_segment(row, offer_pack)
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
        q = qa(subj, body, company, key)
        if not q["pass"]:
            if q["word_count"] > 100:
                lines = body.split("\n\n")
                while len(lines) > 2 and qa(subj, "\n\n".join(lines), company, key)["word_count"] > 100:
                    lines.pop(-2)
                body = "\n\n".join(lines)
            q = qa(subj, body, company, key)
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
                    greeting = _greeting(row, research, key)
                    cand_body = trim_body(greeting, retry_parts[:-1], retry_parts[-1])
                    cand_subj = build_subject(
                        row, signal, segment, step, offer_pack.subject_templates,
                        used_subjects=set(used_subjects),
                        hook=hook if step == 1 else "", key=retry_key,
                    )
                    cand_subj, cand_body = sanitize_email(cand_subj, cand_body)
                    if qa(cand_subj, cand_body, company, key)["pass"]:
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
