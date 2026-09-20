"""QA rule tests: banned phrases, spam subjects, greetings, word count."""

from __future__ import annotations

from lead_personalization.qa import (
    contains_forbidden,
    greeting_is_valid,
    qa,
    subject_has_spam,
    subject_is_fragment,
    word_count,
)


def test_word_count() -> None:
    assert word_count("one two three") == 3


def test_contains_forbidden() -> None:
    assert contains_forbidden("we offer cheap edits") is True
    assert contains_forbidden("just following up") is True
    assert contains_forbidden("let's delve into your video strategy") is True
    assert contains_forbidden("this is a game-changer for your brand") is True
    assert contains_forbidden("seamlessly integrate with your workflow") is True
    assert contains_forbidden("in today's fast-paced digital landscape") is True
    assert contains_forbidden("a clean sentence about video") is False


def test_subject_spam_detection() -> None:
    assert subject_has_spam("FREE money now") is True
    assert subject_has_spam("act now!!!") is True
    assert subject_has_spam("re: your project") is True
    assert subject_has_spam("listing reel pacing") is False


def test_greeting_validation() -> None:
    assert greeting_is_valid("Hi,\n\nSome body") is True
    assert greeting_is_valid("Hi Sarah,\n\nSome body") is True
    assert greeting_is_valid("Hi Closet,\n\nSome body") is False
    assert greeting_is_valid("Hey there\n\nbody") is False


def test_qa_flags_long_body() -> None:
    body = "Hi,\n\n" + " ".join(["word"] * 120) + "\n\nWorth a look?"
    result = qa("clean subject", body)
    assert result["pass"] is False
    assert any("word count" in issue for issue in result["issues"])


def test_qa_passes_clean_email() -> None:
    result = qa(
        "listing reel pacing",
        "Hi,\n\nMost teams sit on usable footage already.\n\nWorth a short sample cut?",
    )
    assert result["pass"] is True
    assert result["issues"] == []


def test_qa_flags_banned_phrase() -> None:
    result = qa("clean subject", "Hi,\n\nJust following up on my last note.\n\nThoughts?")
    assert result["pass"] is False
    assert any(i.startswith("banned:") for i in result["issues"])


def test_subject_fragment_detection() -> None:
    # A hook cut at a word boundary can still land on a function word.
    assert subject_is_fragment("a wide selection of") is True
    assert subject_is_fragment("able company ltd is the") is True
    assert subject_is_fragment("closing the loop on a great source of") is True
    assert subject_is_fragment("coastal brand films") is False
    assert subject_is_fragment("listing reel pacing") is False
    assert subject_is_fragment("") is False


def test_qa_flags_fragment_subject() -> None:
    """A fragmented subject must fail QA — the bug that shipped 126 July 8 lines."""
    result = qa(
        "a wide selection of",
        "Hi,\n\nMost teams sit on usable footage already.\n\nWorth a short sample cut?",
    )
    assert result["pass"] is False
    assert "subject_fragment" in result["issues"]


def test_sequence_issues_flags_redundant_paragraphs() -> None:
    from lead_personalization.qa import sequence_issues

    seq = [
        ("subject one", "Hi,\n\nWe plug in as a white-label finishing bench on your client footage.\n\nWorth a look?"),
        ("subject two", "Hi,\n\nWe plug in as a white-label finishing bench on all your client footage.\n\nInterested?"),
        ("subject three", "Hi,\n\nClosing the loop here.\n\nShould I check back?"),
    ]
    issues = sequence_issues(seq)
    assert any(i.startswith("redundant_paragraph:steps_1_and_2") for i in issues)

