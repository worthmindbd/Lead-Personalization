"""Tests for Ghost Ink deliverability engine and its four golden rules."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from lead_personalization.ghost_ink import (
    GHOST_INK_ATTR,
    GHOST_INK_PASSAGES,
    GHOST_INK_STYLE,
    has_ghost_ink,
    inject_ghost_ink,
    pick_ghost_ink,
    render_ghost_ink_block,
    validate_ghost_ink_text,
)


def test_rule_1_style_declarations_exact() -> None:
    """Rule 1: The hiding has to survive every client.

    All 8 declarations must be present and untrimmed:
    color:transparent, font-size:0px, line-height:0px, max-height:0px,
    mso-hide:all, overflow:hidden, display:none, opacity:0.
    """
    required = [
        "color:transparent",
        "font-size:0px",
        "line-height:0px",
        "max-height:0px",
        "mso-hide:all",
        "overflow:hidden",
        "display:none",
        "opacity:0",
    ]
    for decl in required:
        assert decl in GHOST_INK_STYLE, f"Missing required declaration: {decl}"


def test_passages_entropy_and_word_count() -> None:
    """Passages must be natural human reflections (~280-320 words), no keyword stuffing."""
    assert len(GHOST_INK_PASSAGES) >= 6
    for p in GHOST_INK_PASSAGES:
        words = len(p["text"].split())
        assert 250 <= words <= 350, f"Passage {p['id']} has unexpected word count: {words}"
        # Validate through deliverability audit engine
        issues = validate_ghost_ink_text(p["text"])
        assert issues == [], f"Passage {p['id']} failed deliverability/authenticity audit: {issues}"


def test_validate_ghost_ink_text_catches_spam_and_slop() -> None:
    """Ghost Ink validation engine must flag spam triggers, AI slop, and length violations."""
    # Spam trigger injection
    spam_sample = "I was talking with a friend about video editing. " * 30 + "Act fast and buy now for 100% free results."
    spam_issues = validate_ghost_ink_text(spam_sample)
    assert any("spam_trigger:" in i for i in spam_issues)

    # AI slop injection
    slop_sample = "In today's fast-paced digital landscape, we delve into a rich tapestry of video solutions. " * 15
    slop_issues = validate_ghost_ink_text(slop_sample)
    assert any("ai_slop:" in i for i in slop_issues)

    # Short passage
    short_sample = "Too short reflection."
    short_issues = validate_ghost_ink_text(short_sample)
    assert any("word_count_out_of_range:" in i for i in short_issues)


def test_rule_2_one_block_per_email_never_two() -> None:
    """Rule 2: One block per email, never two. An injector must replace existing blocks."""
    html_raw = (
        "<html><body>"
        '<table class="email-container"><tr><td class="email-card">'
        "<p>Hello world</p>"
        "</td></tr></table>"
        "</body></html>"
    )

    # First injection
    injected_1 = inject_ghost_ink(html_raw, GHOST_INK_PASSAGES[0]["text"])
    assert has_ghost_ink(injected_1)
    matches_1 = re.findall(r'<div\s+[^>]*?data-gi=["\']?\d+["\']?[^>]*?>', injected_1, re.I)
    assert len(matches_1) == 1
    assert GHOST_INK_PASSAGES[0]["text"] in injected_1

    # Second injection (simulating re-processing)
    injected_2 = inject_ghost_ink(injected_1, GHOST_INK_PASSAGES[1]["text"])
    matches_2 = re.findall(r'<div\s+[^>]*?data-gi=["\']?\d+["\']?[^>]*?>', injected_2, re.I)
    assert len(matches_2) == 1, "Expected exactly 1 ghost ink block after re-injection"
    assert GHOST_INK_PASSAGES[1]["text"] in injected_2
    assert GHOST_INK_PASSAGES[0]["text"] not in injected_2


def test_rule_4_same_email_in_same_passage_out() -> None:
    """Rule 4: Same email in, same passage out (deterministic)."""
    email = "sarah.connor@cyberdyne.com"
    p1 = pick_ghost_ink(email, step=1)
    p2 = pick_ghost_ink(email, step=1)
    assert p1["id"] == p2["id"]
    assert p1["text"] == p2["text"]


def test_rule_3_rotation_across_steps_and_emails() -> None:
    """Rule 3: Never the same paragraph twice. Rotate across sequence steps and leads."""
    email = "john.doe@techcorp.io"
    step1 = pick_ghost_ink(email, step=1)
    step2 = pick_ghost_ink(email, step=2)
    step3 = pick_ghost_ink(email, step=3)

    # Sequence steps for the same recipient must rotate
    assert len({step1["id"], step2["id"], step3["id"]}) == 3

    # Across distinct emails, distribution should cover multiple passages
    distinct_ids = {pick_ghost_ink(f"user{i}@domain.com", step=1)["id"] for i in range(20)}
    assert len(distinct_ids) >= 4


def test_render_block_structure() -> None:
    passage = "This is a test reflection on agency workflows."
    block = render_ghost_ink_block(passage)
    assert block.startswith('<div data-gi="1"')
    assert f'style="{GHOST_INK_STYLE}"' in block
    assert block.endswith(f">{passage}</div>")
