"""Copy-engine robustness: pathological packs and hook recovery.

``trim_body`` used to infinite-loop when greeting + CTA alone exceeded the word
budget — unreachable with the current pack, latent for any pack with longer
strings. ``fix_sequence`` used to rebuild subjects WITHOUT the lead's hook, and
``_hook_from_signal`` could not parse LinkedIn signals at all, so the first
rebuild permanently downgraded a LinkedIn-evidence lead's subject to a stock
literal.
"""

from __future__ import annotations

import signal
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from lead_personalization.copywriter import (  # noqa: E402
    fix_sequence,
    generate_sequence,
    sequence_hook,
    trim_body,
)
from lead_personalization.offer_pack import load_offer_pack  # noqa: E402
from lead_personalization.research import build_signal  # noqa: E402
from lead_personalization.subjects import _hook_from_signal  # noqa: E402

PACK = load_offer_pack("aevora")


@contextmanager
def timeout_after(seconds: int):
    def handler(signum, frame):
        raise TimeoutError(f"did not terminate within {seconds}s")

    old = signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def test_trim_body_returns_when_greeting_and_cta_alone_exceed_the_budget():
    long_greeting = "Hi, " + "very " * 40
    long_cta = "want " * 40 + "a sample?"
    with timeout_after(5):
        body = trim_body(long_greeting, ["a short part"], long_cta, max_words=10)
    assert long_cta in body


def test_sequence_hook_prefers_the_linkedin_topic_for_linkedin_evidence():
    assert sequence_hook({"evidence": "linkedin_posts",
                          "linkedin_topic": "hiring editors",
                          "snippet": "site words"}) == "hiring editors"
    assert sequence_hook({"evidence": "positioning",
                          "linkedin_topic": "hiring editors",
                          "snippet": "site words"}) == "site words"
    assert sequence_hook({"evidence": "weak"}) == ""


def test_hook_from_signal_round_trips_build_signal_outputs():
    row = {"City": "Austin", "State": "Texas", "aevora_segment": "home_builder"}
    for kwargs in (
        {"li_topic": "hiring in-house editors"},
        {"snippet": "custom homes on tight timelines"},
        {},
    ):
        sig, _, _ = build_signal(
            row,
            {"fetched": True, "has_video": False},
            kwargs.get("snippet", ""),
            "linkedin_posts" if kwargs.get("li_topic") else "positioning",
            [],
            kwargs.get("li_topic", ""),
        )
        hook = _hook_from_signal(sig)
        expected = kwargs.get("li_topic") or kwargs.get("snippet") or ""
        if expected:
            assert hook, f"hook lost for {kwargs}: signal={sig!r}"
            assert hook in expected.lower() or expected.lower().startswith(hook)


def test_fix_sequence_rebuild_keeps_a_linkedin_hook():
    row = {
        "aevora_segment": "home_builder",
        "City": "Austin",
        "First_category": "Custom home builder",
        "primary_email": "owner@x.com",
        "company_name": "X Homes",
    }
    research = {
        "email": "owner@x.com",
        "company": "X Homes",
        "evidence": "linkedin_posts",
        "linkedin_topic": "hiring in-house editors",
        "snippet": "",
        "research_signal": 'recent LinkedIn post: "hiring in-house editors"; Austin, Texas',
        "signal_strength": "strong",
        "social_channel": "",
    }
    seq, _ = generate_sequence(row, research, PACK)
    fixed = fix_sequence(seq, row, research, PACK)

    # The rebuilt first subject must still be able to carry the LinkedIn hook,
    # not the stock literal the hookless rebuild used to produce.
    assert "editor" in fixed[0][0]
