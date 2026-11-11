"""Regression fixture: real prospect text that reached live sends.

Every string below shipped in a subject or as the quoted line of a body in
the Oct 19 / Jul 31 2026 lists. Per-lead QA passed all of them, because QA
only ever saw the finished email; this pins the filters that now run on the
raw research text before it can be quoted.
"""

from __future__ import annotations

import pytest

from lead_personalization.copywriter import fix_sequence, generate_sequence
from lead_personalization.linkedin import clean_post_topic
from lead_personalization.offer_pack import load_offer_pack
from lead_personalization.qa import (
    opener_is_client_centric,
    qa,
    snippet_reject_reasons,
    subject_is_fragment,
)
from lead_personalization.research import discard_error_page
from lead_personalization.segments import greeting_template, peer_phrase, resolve_outreach_tier
from lead_personalization.subjects import build_subject

PACK = load_offer_pack()

# Quoted verbatim in a body as "Your site leads with X" / "X is a strong promise".
SHIPPED_BAD_SNIPPETS = [
    "502 Bad Gateway",
    "UNIT8, 6-8 McLACHLAN AVE, ARTARMON NSW 2064",
    "Thanks for visiting Paradise Studios",
    "Case studies, writing, and how to get in touch",
    "Bill Miller Photography",
    "Tennessee & Kentucky",
    "Enquire today for a tailored quote",
    "Trying to find professional aerial photography services in Henderson?",
    "We are locally owned and operated in Denver, CO",
    "With over a decade of experience",
    "### Wedding Photography",
    "Sorry, you have been blocked",
    "Créez vos podcasts uniques avec nous",
    "Marketing Agentur München",
]


@pytest.mark.parametrize("snippet", SHIPPED_BAD_SNIPPETS)
def test_shipped_bad_snippet_is_rejected(snippet: str) -> None:
    assert snippet_reject_reasons(snippet), snippet


@pytest.mark.parametrize(
    "snippet",
    [
        "Luxury wedding cinematography",
        "Video Podcast Studio London",
        "Listing media that makes buyers stop scrolling",
        "Photography That Works as Hard as You Do",
    ],
)
def test_real_positioning_still_passes(snippet: str) -> None:
    assert not snippet_reject_reasons(snippet), snippet_reject_reasons(snippet)


def test_error_page_is_treated_as_no_page() -> None:
    page = {"fetched": True, "title": "502 Bad Gateway", "has_video": False}
    assert discard_error_page(page)["fetched"] is False
    ok = {"fetched": True, "title": "Brisbane Wedding Films", "has_video": True}
    assert discard_error_page(ok)["fetched"] is True


# Shipped as step-1 subjects. Each hook goes in through the Meta_Description
# path (the raw, unfiltered one) and must not come out as-is.
SHIPPED_BAD_SUBJECT_SOURCES = {
    "502 Bad Gateway": "502 bad gateway",
    "YOU AND YOUR LISTINGS, DESERVE TO SHINE": "you and your listings,",
    "Video Production, Photography & Marketing in Greater Vancouver": "video production,",
    "Sussex Wedding Photographer. A Reportage Style Capturing Candid Moments": "sussex wedding photographer.",
    "We are locally owned and operated in Denver, CO": "we are locally owned",
    "#1 Rated Video Production Company in East Houston": "#1 rated video production",
    "A flexible set for podcasts, interviews and reels": "a flexible set for podcasts,",
    "Record something worth watching every single week": "record something worth",
    "Jillian Nielsen is a Langley wedding photographer capturing love": "jillian nielsen is a langley",
    "Neuen Films creates emotional, cinematic wedding films": "neuen films creates emotional",
}


@pytest.mark.parametrize("meta,shipped", SHIPPED_BAD_SUBJECT_SOURCES.items())
def test_shipped_bad_subject_cannot_recur(meta: str, shipped: str) -> None:
    row = {
        "City": "Langley",
        "First_category": "Wedding photographer",
        "Meta_Description": meta,
        "company_name": "Neuen Films",
    }
    for step in (1, 2, 3):
        subj = build_subject(row, "", "production_studios", step, PACK.subject_templates, key="x@y.com")
        assert subj != shipped
        assert not subject_is_fragment(subj), subj
        assert subj[-1].isalnum(), subj


def test_subject_with_no_city_skips_city_templates() -> None:
    row = {"City": "", "First_category": "Wedding photographer"}
    for i in range(40):
        subj = build_subject(row, "", "production_studios", 1, PACK.subject_templates, key=f"{i}@x.com")
        assert "your market" not in subj


def test_linkedin_topic_is_never_cut_mid_sentence() -> None:
    post = (
        "Just wrapped a session with the incredibly knowledgeable Kelly Hejtmancik, "
        "Partner at a firm we admire, on scaling content."
    )
    topic = clean_post_topic(post)
    assert topic != "Just wrapped a session with the incredibly knowledgeable Kelly Hejtmancik, Partner at"
    assert not topic.endswith(" at")


def test_studio_never_hears_its_site_has_no_video() -> None:
    row = {
        "primary_email": "info@studio.com", "aevora_segment": "creative_marketing",
        "First_category": "Video production service", "City": "Clayfield",
        "company_name": "Playback Media", "outreach_tier": "company",
    }
    for evidence in ("site_video", "social_video", "positioning", "weak"):
        research = {
            "email": "info@studio.com", "evidence": evidence, "company": "Playback Media",
            "snippet": "Brisbane wedding films", "social_channel": "Instagram",
        }
        seq, variant = generate_sequence(row, research, PACK)
        seq = fix_sequence(seq, row, research, PACK)
        body = seq[0][1].lower()
        assert "carries no video" not in body and "rarer than it should be" not in body
        assert "video production service teams" not in body
        for subj, b in seq:
            assert qa(subj, b, "Playback Media")["pass"], qa(subj, b, "Playback Media")


@pytest.mark.parametrize(
    "category,peer",
    [
        ("Video production service", "video production businesses"),
        ("Wedding photographer", "wedding photographers"),
        ("Media company", "media companies"),
        ("Meditation center", "meditation centers"),
        ("", "businesses like yours"),
    ],
)
def test_peer_phrase_is_a_natural_plural(category: str, peer: str) -> None:
    assert peer_phrase(category) == peer


def test_brand_split_as_a_name_is_not_greeted() -> None:
    # "Lovelenscapes Photography" -> first "Lovelenscapes", last "Photography".
    assert resolve_outreach_tier("Lovelenscapes", "Photography", "lovelenscapes@gmail.com") == "company"
    greeting = greeting_template(
        "person", "Lovelenscapes", "Lovelenscapes Photography", "lovelenscapes@gmail.com"
    )
    assert greeting in {"Hi,", "Hey,", "Hello,"}


def test_greetings_rotate_across_leads() -> None:
    seen = {greeting_template("company", "", "", f"lead{i}@x.com") for i in range(60)}
    assert seen == {"Hi,", "Hey,", "Hello,"}
    named = {greeting_template("person", "Sarah", "", f"sarah{i}@x.com") for i in range(80)}
    assert named == {"Hi Sarah,", "Hey Sarah,", "Hello Sarah,", "Sarah,"}


def test_forbidden_word_in_snippet_falls_back_instead_of_losing_the_opener() -> None:
    row = {
        "primary_email": "a@b.com", "aevora_segment": "general", "First_category": "Bakery",
        "City": "Austin", "company_name": "Crumbs", "outreach_tier": "company",
    }
    research = {"email": "a@b.com", "evidence": "positioning", "company": "Crumbs",
                "snippet": "Cheap cakes delivered fast"}
    seq, _ = generate_sequence(row, research, PACK)
    seq = fix_sequence(seq, row, research, PACK)
    assert opener_is_client_centric(seq[0][1])
    assert len(seq[0][1].split("\n\n")) == 4  # greeting, opener, solution, CTA


def test_repetition_warnings_flag_a_collapsed_pool_only() -> None:
    from lead_personalization.qa import campaign_repetition, repetition_warnings

    healthy = [
        [(f"hook {i}", f"Hi,\n\nOpener number {i} about them.\n\nCTA?"),
         (f"follow {i % 10}", "Hi,\n\nAngle text here today.\n\nCTA?"),
         (f"close {i % 10}", "Hi,\n\nCloser text here today.\n\nCTA?")]
        for i in range(100)
    ]
    report = campaign_repetition(healthy)
    assert not [w for w in repetition_warnings(report) if "subject" in w]
    collapsed = [[("same subject", "Hi,\n\nx y z w.\n\nCTA?")] * 3 for _ in range(100)]
    assert any("same subject" in w for w in repetition_warnings(campaign_repetition(collapsed)))
