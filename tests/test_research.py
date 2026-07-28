"""Research signal classification and guard tests (no network)."""

from __future__ import annotations

from lead_personalization.research import (
    build_signal,
    classify_evidence,
    linkedin_topic,
    needs_render,
    positioning_snippet,
    snippet_is_usable,
    social_channel,
)


def test_needs_render_when_fetch_failed() -> None:
    assert needs_render({"fetched": False}) is True


def test_needs_render_when_no_usable_signals() -> None:
    assert needs_render({"fetched": True, "title": "", "description": "", "h1": "", "has_video": False}) is True


def test_no_render_when_signals_present() -> None:
    assert needs_render({"fetched": True, "title": "Great homes"}) is False


def test_classify_linkedin_wins() -> None:
    page = {"fetched": True, "has_video": True}
    assert classify_evidence({}, page, "snippet", li_topic="a topic") == "linkedin_posts"


def test_classify_site_video() -> None:
    page = {"fetched": True, "has_video": True}
    assert classify_evidence({}, page, "", "") == "site_video"


def test_classify_social_video() -> None:
    page = {"fetched": True, "has_video": False}
    row = {"Youtube_URL": "https://youtube.com/@x"}
    assert classify_evidence(row, page, "", "") == "social_video"


def test_classify_positioning() -> None:
    page = {"fetched": True, "has_video": False}
    assert classify_evidence({}, page, "Clear positioning phrase", "") == "positioning"


def test_classify_weak_default() -> None:
    assert classify_evidence({}, {"fetched": False}, "", "") == "weak"


def test_social_channel_prefers_youtube() -> None:
    assert social_channel({"Youtube_URL": "x", "Instagram_URL": "y"}) == "YouTube"
    assert social_channel({"Instagram_URL": "y"}) == "Instagram"
    assert social_channel({}) == ""


def test_snippet_is_usable_rejects_forbidden_and_ellipsis() -> None:
    assert snippet_is_usable("Custom homes for coastal living") is True
    assert snippet_is_usable("cheap edits") is False
    assert snippet_is_usable("great work...") is False
    assert snippet_is_usable("book a call today") is False


def test_positioning_snippet_rejects_company_echo() -> None:
    page = {"h1": "Lakeview Custom Homes", "title": "", "description": ""}
    assert positioning_snippet("Lakeview Custom Homes", page) == ""


def test_positioning_snippet_extracts_clean_phrase() -> None:
    page = {"h1": "Homes built around family living", "title": "", "description": ""}
    assert positioning_snippet("Acme", page) == "Homes built around family living"


def test_linkedin_topic_skips_company_name() -> None:
    posts = [{"topic": "Acme launches a new product line today"}]
    assert linkedin_topic(posts, "Acme") == ""
    posts = [{"topic": "why finishing beats more filming every time"}]
    assert linkedin_topic(posts, "Acme") == "why finishing beats more filming every time"


def test_build_signal_strength_follows_evidence() -> None:
    _, _, strong = build_signal({}, {"fetched": True, "has_video": True}, "", "site_video")
    assert strong == "strong"
    _, _, weak = build_signal({}, {"fetched": False}, "", "weak")
    assert weak == "weak"
