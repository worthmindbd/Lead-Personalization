"""Copy-quality invariants that the engine must hold at campaign scale.

These cover defects that shipped in live sends and were invisible to the
existing suite:

- greetings addressed to companies and CSV artifacts ("Hi None,", "Hi Build,")
- subject hooks that were raw Meta_Description data (phone numbers, street
  addresses, WordPress error pages, the company's own name)
- pool exhaustion: a 2-entry closer pool meant every email 3 in a 9,000-lead
  history was one of four texts, and nothing reported it
"""

from __future__ import annotations

import pytest

from lead_personalization.copywriter import generate_sequence
from lead_personalization.offer_pack import load_offer_pack
from lead_personalization.qa import (
    campaign_repetition,
    company_name_in_subject,
    junk_hook_reasons,
    qa,
)
from lead_personalization.segments import (
    GENERAL_SEGMENT,
    canonical_segment,
    greeting_template,
    is_plausible_first_name,
    name_matches_email,
    segment_for_category,
)
from lead_personalization.subjects import build_subject


# ---------------------------------------------------------------------------
# Greeting: only real people get "Hi {name},"
# ---------------------------------------------------------------------------

# Every one of these has shipped in a live send as "Hi <name>,", and every one
# passed qa() as a PASS. They are GMB business names and CSV export artifacts,
# not people.
GARBAGE_NAMES = [
    "None", "My", "Build", "Inner", "Neighbor", "Columbia", "Menuiserie",
    "Maretterra", "Hanson", "FnF", "Trash", "Digital", "Growth", "Casa",
    "Become.", "A+", "Ad-Star", "Hey!Film", "Soixan7e", "Bing's", "BH", "JR",
    "SW", "Denture", "Dentistry", "Commercial", "Architect", "Beemedia",
    "Video", "Film", "Photo", "Studio", "Aurevoir", "Bluebird", "Greenhouse",
    "The", "Dr", "Office", "Team", "Admin", "Owner", "Unknown", "N/A",
]

REAL_NAMES = [
    "Sarah", "Michael", "Jennifer", "David", "Jessica", "Ashley", "Daniel",
    "John", "Emily", "Joseph", "Olivia", "Grace", "Marcus", "Aisha", "Nikolai",
    "Sofia", "Andre", "Ingrid", "Yuki", "Lars", "Priya", "Omar", "Chiara",
    "Mateo", "Nadia", "Tariq", "Brooke", "Desmond", "Ryan", "Carmen", "Colin",
]


@pytest.mark.parametrize("name", GARBAGE_NAMES)
def test_business_and_artifact_names_never_reach_the_greeting(name: str) -> None:
    assert not is_plausible_first_name(name), f"would greet {name!r} by name"


@pytest.mark.parametrize("name", REAL_NAMES)
def test_real_first_names_still_get_addressed_by_name(name: str) -> None:
    assert is_plausible_first_name(name), f"would downgrade a real contact: {name!r}"


def test_garbage_greeting_becomes_the_safe_generic_greeting() -> None:
    assert greeting_template("person", "Build", "", "build@acme.com") == "Hi,"


def test_unknown_name_is_rescued_only_by_its_own_address() -> None:
    """A name off the allowlist is fine when the address corroborates it."""
    assert is_plausible_first_name("Mckinley", "mckinley@northside.com")
    assert not is_plausible_first_name("Mckinley", "info@northside.com")


def test_a_brand_masquerading_as_a_person_address_is_rejected() -> None:
    """zenith@zenith.com is a business mailbox, not a person named Zenith."""
    assert not is_plausible_first_name("Zenith", "zenith@zenith.com")
    assert not is_plausible_first_name("Dental", "dental@clinic.com")


def test_name_matches_email_requires_the_name_as_the_local_part() -> None:
    assert name_matches_email("Sarah", "sarah@acme.com")
    assert name_matches_email("Sarah", "sarah.jones@acme.com")
    assert not name_matches_email("Sarah", "info@acme.com")
    assert not name_matches_email("Sarah", "sales@acme.com")


def test_qa_rejects_a_greeting_addressed_to_a_business() -> None:
    result = qa("property tour pacing", "Hi Build,\n\nWe finish footage you supply.", "Acme")
    assert not result["pass"]
    assert "bad_greeting" in result["issues"]


# ---------------------------------------------------------------------------
# Subject hooks: unfiltered Meta_Description must never become a subject
# ---------------------------------------------------------------------------

# These are verbatim subjects that shipped to live inboxes.
JUNK_HOOKS = [
    "call (561) 368-0770",
    "2401 pga blvd., suite 270",
    "wordpress › error",
    "404 page not found",
    "genrietta arakelova, d.d.s",
    "visit us at www.example.com",
    "book online now",
    "your trusted paradise valley",
    "do you need of a new dentist",
    "services from $99",
]


@pytest.mark.parametrize("hook", JUNK_HOOKS)
def test_junk_hooks_are_detected(hook: str) -> None:
    assert junk_hook_reasons(hook), f"should be rejected as a subject: {hook!r}"


@pytest.mark.parametrize("hook", JUNK_HOOKS)
def test_junk_hooks_fall_through_to_a_literal_template(hook: str) -> None:
    pack = load_offer_pack()
    subject = build_subject(
        {"City": "Austin", "First_category": "Dentist", "Meta_Description": hook},
        "",
        "medical_aesthetic",
        1,
        pack.subject_templates,
        hook="",
        key="a@b.com",
    )
    assert not junk_hook_reasons(subject), f"shipped junk subject {subject!r}"


def test_company_name_in_the_subject_is_a_qa_failure() -> None:
    assert company_name_in_subject("at luxe dental dallas", "Luxe Dental")
    assert not company_name_in_subject("property tour pacing", "Luxe Dental")


def test_qa_flags_the_company_name_leaking_into_a_subject() -> None:
    result = qa("genrietta arakelova, d.d.s", "Hi,\n\nWe finish footage you supply.", "Genrietta Arakelova, D.D.S")
    assert not result["pass"]
    assert "company_name_in_subject" in result["issues"]


# ---------------------------------------------------------------------------
# No fit scoring, anywhere
# ---------------------------------------------------------------------------

def test_the_catch_all_segment_is_not_named_like_a_score() -> None:
    """Every industry is a prospect; the catch-all must not read as a demotion."""
    assert GENERAL_SEGMENT == "general"
    assert segment_for_category("Something Unmapped") == "general"
    assert segment_for_category("") == "general"


def test_legacy_segment_keys_still_resolve_to_their_copy() -> None:
    """Rows already on disk carry the pre-rename key and must not be stranded."""
    assert canonical_segment("low_fit") == "general"
    assert canonical_segment("") == "general"
    pack = load_offer_pack()
    assert pack.segment_solutions("low_fit") is pack.segment_solutions("general")


# ---------------------------------------------------------------------------
# Pool exhaustion: the defect that shipped for 9,000 leads
# ---------------------------------------------------------------------------

def _leads(count: int, segment: str = "creative_marketing") -> list:
    pack = load_offer_pack()
    sequences = []
    cities = ["Austin", "Dallas", "Houston", "Phoenix", "Denver", "Miami", "Tampa"]
    for i in range(count):
        row = {
            "primary_email": f"lead{i}@example.com",
            "aevora_segment": segment,
            "City": cities[i % len(cities)],
            "State": "Texas",
            "First_category": "Marketing agency",
            "outreach_tier": "company",
        }
        research = {"email": f"lead{i}@example.com", "evidence": "weak", "outreach_tier": "company"}
        sequences.append(generate_sequence(row, research, pack)[0])
    return sequences


def test_the_breakup_email_is_not_drawn_from_a_two_entry_pool() -> None:
    """Every email 3 used to be one of four texts. A 2-entry pool cannot pass."""
    pack = load_offer_pack()
    assert len(pack.closers) >= 8, f"closer pool too thin: {len(pack.closers)}"
    assert len(pack.support_lines) >= 8, f"support pool too thin: {len(pack.support_lines)}"


@pytest.mark.parametrize("step", [1, 2, 3])
def test_no_single_subject_dominates_a_step_across_every_segment(step: int) -> None:
    """The old guard covered home_design step 1 only, so 10 segments were unmeasured."""
    from lead_personalization.segments import MACRO_SEGMENTS

    for segment in MACRO_SEGMENTS:
        subjects = [seq[step - 1][0].strip().lower() for seq in _leads(300, segment)]
        top_share = subjects.count(max(set(subjects), key=subjects.count)) / len(subjects)
        assert top_share <= 0.45, (
            f"{segment} step {step}: one subject covers {top_share:.0%} of leads "
            f"({len(set(subjects))} distinct) — widen the pool"
        )


def test_the_breakup_body_varies_across_a_campaign() -> None:
    sequences = _leads(200)
    third_bodies = {seq[2][1] for seq in sequences}
    assert len(third_bodies) >= 20, f"only {len(third_bodies)} distinct email-3 bodies in 200 leads"


def test_later_steps_never_repeat_the_leads_own_hook() -> None:
    """{hook} on steps 2 and 3 is what made every sequence read templated."""
    pack = load_offer_pack()
    for segment in pack.subject_templates:
        for step in (2, 3):
            assert all("{hook}" not in t for t in pack.subject_templates[segment][step]), (
                f"{segment} step {step} still carries a {{hook}} template"
            )


def test_campaign_repetition_surfaces_pool_exhaustion() -> None:
    """A thin pool must be visible in the review, not inferred from reply rates.

    With a 4-entry solution pool and uniform hashing the top paragraph sits near
    50% by construction; the signal that a pool is exhausted is distinct-count
    per step, not a low top-share. The 2-entry pools this replaces put every
    email 3 in the campaign at one of four texts.
    """
    stats = campaign_repetition(_leads(200))
    assert stats["leads"] == 200
    assert stats["subjects"]["step_3"]["distinct"] >= 8
    assert stats["subjects"]["step_3"]["top_share"] <= 0.35
    assert stats["bodies"], "expected repeated body paragraphs to be reported"
    assert len(stats["bodies"]) >= 4


def test_campaign_repetition_handles_an_empty_campaign() -> None:
    stats = campaign_repetition([])
    assert stats["leads"] == 0
    assert stats["subjects"] == {}
