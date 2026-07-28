"""QA rule tests: banned phrases, spam subjects, greetings, word count."""

from __future__ import annotations

from lead_personalization.qa import (
    contains_forbidden,
    greeting_is_valid,
    qa,
    subject_has_spam,
    word_count,
)


def test_word_count() -> None:
    assert word_count("one two three") == 3


def test_contains_forbidden() -> None:
    assert contains_forbidden("we offer cheap edits") is True
    assert contains_forbidden("just following up") is True
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
