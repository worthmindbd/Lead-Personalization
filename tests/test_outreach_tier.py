"""Dual-tier outreach: the greeting follows the row's normalized tier.

CLAUDE.md has always documented this table — person tier (named contact +
non-generic address) greets ``Hi {first_name},``; company tier greets
``Hi,``. But research hard-coded ``outreach_tier: "company"`` and the
copywriter always used the pack greeting, so the tier normalize_row computed
never reached a single email.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from lead_personalization.copywriter import generate_sequence  # noqa: E402
from lead_personalization.offer_pack import load_offer_pack  # noqa: E402
from lead_personalization.pipeline import normalize_row  # noqa: E402
from lead_personalization.research import research_lead  # noqa: E402
from lead_personalization.segments import resolve_outreach_tier  # noqa: E402


def raw_row(**over):
    base = {
        "Name": "Lakeview Custom Homes LLC",
        "Email": "hello@lakeview.com",
        "Website": "",
        "First_category": "Custom home builder",
        "City": "Austin",
        "State": "Texas",
    }
    base.update(over)
    return base


def person_row():
    return raw_row(
        Name="Jane Smith - Lakeview Custom Homes",
        Email="jane@lakeview.com",
    )


PACK = load_offer_pack("aevora")


def test_a_named_contact_with_a_personal_address_is_person_tier():
    row = normalize_row(0, person_row())
    assert row["outreach_tier"] == "person"
    assert resolve_outreach_tier("Jane", "Smith", "jane@lakeview.com") == "person"


def test_a_generic_inbox_is_company_tier_even_with_a_name():
    row = normalize_row(0, raw_row(Name="Jane Smith", Email="info@lakeview.com"))
    assert row["outreach_tier"] == "company"


def test_a_business_name_without_a_person_is_company_tier():
    row = normalize_row(0, raw_row())  # business-only name, generic inbox
    assert row["outreach_tier"] == "company"


def test_research_carries_the_rows_tier_through():
    row = normalize_row(0, person_row())
    item = research_lead(row, None, render_fallback=False, throttle_s=0)
    assert item["outreach_tier"] == "person"

    company = research_lead(
        normalize_row(0, raw_row()), None, render_fallback=False, throttle_s=0
    )
    assert company["outreach_tier"] == "company"


def test_person_tier_greets_by_first_name_and_company_tier_does_not():
    person = normalize_row(0, person_row())
    item = research_lead(person, None, render_fallback=False, throttle_s=0)
    seq, _ = generate_sequence(person, item, PACK)
    assert seq[0][1].split("\n\n")[0] in {"Hi Jane,", "Hey Jane,", "Hello Jane,", "Jane,"}

    company = normalize_row(0, raw_row())
    item2 = research_lead(company, None, render_fallback=False, throttle_s=0)
    seq2, _ = generate_sequence(company, item2, PACK)
    assert seq2[0][1].split("\n\n")[0] in {"Hi,", "Hey,", "Hello,"}


def test_person_greeting_passes_qa():
    from lead_personalization.qa import qa

    person = normalize_row(0, person_row())
    item = research_lead(person, None, render_fallback=False, throttle_s=0)
    seq, _ = generate_sequence(person, item, PACK)
    for subj, body in seq:
        assert qa(subj, body, item["company"])["pass"], (subj, body)
