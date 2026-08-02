"""Subject selection: the research hook must actually reach the subject line,
and leads without one must still get varied, spam-safe lines.

Before this was fixed, every step-1 template list read
``["<literal>", "{hook}", "<literal>"]`` and the first spam-free candidate won,
so the literal always beat ``{hook}`` — 762 emails shipped with 13 distinct
subjects and one of them went to 245 prospects.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lead_personalization.offer_pack import load_offer_pack  # noqa: E402
from lead_personalization.qa import subject_has_spam  # noqa: E402
from lead_personalization.subjects import build_subject  # noqa: E402

PACK = load_offer_pack("aevora")
SEGMENTS = sorted(PACK.subject_templates)
STEPS = (1, 2, 3)


def row(email: str = "lead@example-biz.com") -> dict:
    return {
        "primary_email": email,
        "First_category": "Custom home builder",
        "City": "Austin",
        "State": "Texas",
        "Meta_Description": "",
    }


def subject(hook: str = "", *, segment: str = "home_design", step: int = 1,
            email: str = "lead@example-biz.com") -> str:
    return build_subject(
        row(email), "", segment, step, PACK.subject_templates,
        hook=hook, key=email,
    )


# ---------------------------------------------------------------------------
# The hook reaches the line
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("segment", SEGMENTS)
def test_different_hooks_give_different_first_subjects(segment: str) -> None:
    a = subject("coastal brand films that convert", segment=segment, email="a@x.com")
    b = subject("lessons from our latest handoff", segment=segment, email="b@x.com")
    assert a != b, f"{segment}: hook does not reach the subject"
    assert "coastal" in a and "lessons" in b


def test_hookless_lead_still_gets_a_clean_subject() -> None:
    subj = subject("")
    assert subj
    assert not subject_has_spam(subj)
    assert "{" not in subj  # no unfilled placeholder


def test_same_lead_is_stable_across_runs() -> None:
    assert subject("a coastal build hook") == subject("a coastal build hook")


# ---------------------------------------------------------------------------
# Hostile hooks — prospect-supplied text is never trusted
# ---------------------------------------------------------------------------


def test_brand_forbidden_hook_falls_back_to_a_literal() -> None:
    subj = subject("affordable video for every budget")
    assert "affordable" not in subj
    assert not subject_has_spam(subj)


def test_spam_word_hook_falls_back_to_a_literal() -> None:
    subj = subject("free consultation, act now")
    assert not subject_has_spam(subj)


def test_long_hook_is_trimmed_to_whole_words() -> None:
    long_hook = "we build extraordinary award winning residences across the coast"
    subj = subject(long_hook, segment="home_design", step=1)
    assert len(subj) <= 50
    assert "..." not in subj and "…" not in subj
    # Every word that survived is a whole word from the hook, not a fragment.
    hook_words = set(long_hook.lower().split())
    assert set(subj.split()) <= hook_words


def test_over_length_subject_is_cut_at_a_word_boundary() -> None:
    """The last-resort fallback interpolates the raw City, which can overrun 50.

    Forced here by marking every template as already used. A hard ``[:50]``
    slice used to leave a fragment ("... custom ree").
    """
    long_city = "Rancho Santa Margarita and Coto de Caza"
    lead = row() | {"City": long_city}
    used = {
        _fill_template(t, long_city, "", lead["First_category"])
        for t in PACK.subject_templates["home_design"][1]
    }
    subj = build_subject(
        lead, "", "home_design", 1, PACK.subject_templates,
        used_subjects=used, key=lead["primary_email"],
    )
    assert len(subj) <= 50
    assert subj.split()[-1] in (long_city.lower().split() + ["custom", "reel"])


def _fill_template(template: str, city: str, hook: str, category: str) -> str:
    from lead_personalization.subjects import _fill

    return _fill(template, city, hook, category)


def _all_literals(segment: str, step: int) -> list[str]:
    return [t for t in PACK.subject_templates[segment][step] if "{hook}" not in t]


# ---------------------------------------------------------------------------
# Campaign-wide variety
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("step", STEPS)
def test_no_single_subject_dominates_a_step(step: int) -> None:
    """200 hookless leads in one segment must not all share one subject.

    Hookless is the worst case — with a hook every step-1 line is unique. This
    guards the deterministic rotation across the literal pool.
    """
    counts = Counter(
        subject("", segment="home_design", step=step, email=f"lead{i}@example-biz.com")
        for i in range(200)
    )
    top_share = counts.most_common(1)[0][1] / 200
    pool = len(_all_literals("home_design", step))
    assert top_share <= (1 / pool) + 0.15, f"step {step}: {counts.most_common(3)}"


def test_hooked_batch_produces_near_unique_first_subjects() -> None:
    subjects = {
        subject(f"hook number {i} for this build", email=f"lead{i}@example-biz.com")
        for i in range(100)
    }
    assert len(subjects) >= 95


# There used to be a drift guard here, asserting that
# scripts/personalization/subjects.py held the same SUBJECT_TEMPLATES as the
# offer pack. That module is gone; the templates exist once, in the pack. See
# tests/test_one_engine.py for what replaced it.
