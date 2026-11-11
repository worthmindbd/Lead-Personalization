"""Tests for premium, high-deliverability Listmonk email templates.

Ensures:
- Plain, personal-email presentation: no logo, card, images, or tracking pixel.
- No hidden text of any kind (hidden blocks are a spam signal).
- Dual-tier personalization: body variables and Listmonk fallback content.
- Casual, human tone: zero AI slop, zero em dashes, friendly opt-out.
- Valid Go template syntax and complete, working links.
"""

from __future__ import annotations

import re
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = ROOT / "templates" / "listmonk"
TEMPLATE_FILES = [
    TEMPLATES_DIR / "sequence_1_template.html",
    TEMPLATES_DIR / "sequence_2_template.html",
    TEMPLATES_DIR / "sequence_3_template.html",
]

AI_SLOP_WORDS = [
    "delve",
    "tapestry",
    "game-changer",
    "seamless",
    "cutting-edge",
    "revolutionize",
    "supercharge",
    "elevate",
    "beacon",
    "testament",
    "pivotal",
    "harness",
    "streamline",
    "robust",
    "unparalleled",
    "groundbreaking",
    "meticulous",
    "burgeoning",
    "bespoke",
    "empower",
    "demystify",
    "transcend",
    "panacea",
]


@pytest.mark.parametrize("path", TEMPLATE_FILES)
def test_template_exists(path: Path) -> None:
    assert path.is_file(), f"Missing template file: {path}"
    assert path.stat().st_size > 0, f"Template file is empty: {path}"


@pytest.mark.parametrize("path", TEMPLATE_FILES)
def test_template_is_plain_like_a_personal_email(path: Path) -> None:
    """Cold email must look like one person writing to another: no logo, card,
    image, or tracking pixel. Marketing-style HTML hurts primary-inbox placement."""
    content = path.read_text(encoding="utf-8")
    assert not re.findall(r"<img\b", content, re.IGNORECASE), f"Image found in {path.name}"
    assert "email-card" not in content and "email-container" not in content
    assert "{{ TrackView }}" not in content, f"Tracking pixel in {path.name}"


@pytest.mark.parametrize("path", TEMPLATE_FILES)
def test_template_has_no_hidden_text(path: Path) -> None:
    """Hidden text blocks (the former "Ghost Ink") are a classic spam/phishing
    signal for Gmail and Outlook. They must never come back."""
    content = path.read_text(encoding="utf-8")
    low = content.lower().replace(" ", "")
    for marker in ("data-gi=", "display:none", "font-size:0", "mso-hide:all",
                   "color:transparent", "opacity:0", "max-height:0"):
        assert marker not in low, f"Hidden-text marker {marker!r} in {path.name}"
    assert "&#847;" not in content and "&zwnj;" not in content


@pytest.mark.parametrize("path", TEMPLATE_FILES)
def test_template_fallback_subject_is_rule_compliant(path: Path) -> None:
    """No company name and no "quick question" in the fallback subject."""
    content = path.read_text(encoding="utf-8")
    title = re.search(r"<title>(.*?)</title>", content, re.S).group(1)
    assert "company_name" not in title
    assert "quick question" not in title.lower()
    assert "Re:" not in title


@pytest.mark.parametrize(
    ("path", "var_name"),
    [
        (TEMPLATES_DIR / "sequence_1_template.html", "email_1_body"),
        (TEMPLATES_DIR / "sequence_2_template.html", "email_2_body"),
        (TEMPLATES_DIR / "sequence_3_template.html", "email_3_body"),
    ],
)
def test_template_body_variables(path: Path, var_name: str) -> None:
    content = path.read_text(encoding="utf-8")
    assert f".Subscriber.Attribs.{var_name}" in content


@pytest.mark.parametrize("path", TEMPLATE_FILES)
def test_template_contains_founder_signature(path: Path) -> None:
    content = path.read_text(encoding="utf-8")
    assert "Best regards," in content, f"Signature greeting missing in {path.name}"
    assert "Kawsar Mahmud" in content, f"Founder name missing in {path.name}"
    assert "CEO and Founder" in content, f"Founder title missing in {path.name}"


@pytest.mark.parametrize("path", TEMPLATE_FILES)
def test_template_contains_listmonk_content_placeholder(path: Path) -> None:
    content = path.read_text(encoding="utf-8")
    pattern = re.compile(r'{{(\s+)?template\s+?"content"(\s+)?\.(\s+)?}}')
    matches = pattern.findall(content)
    assert len(matches) == 1, (
        f"Expected exactly 1 Listmonk content placeholder in {path.name}, found {len(matches)}"
    )


@pytest.mark.parametrize("path", TEMPLATE_FILES)
def test_template_casual_tone_and_no_slop(path: Path) -> None:
    """Ensure natural friendly phrasing, no AI buzzwords, and no em dashes."""
    content = path.read_text(encoding="utf-8")

    # Zero em dashes anywhere in file
    assert "—" not in content, f"Em dash found in {path.name}"

    # Strip HTML comments and Go template tags to check text body
    text_content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
    text_content = re.sub(r"\{\{.*?\}\}", "", text_content, flags=re.DOTALL)

    # Zero double dashes in text content
    assert "--" not in text_content, f"Double dash found in text of {path.name}"

    # Zero AI slop buzzwords
    for slop in AI_SLOP_WORDS:
        assert not re.search(r"\b" + slop + r"\b", text_content, re.IGNORECASE), (
            f"AI slop buzzword '{slop}' found in {path.name}"
        )

    # Friendly human opt-out
    assert "If you'd prefer not to hear from me" in content
    assert "{{ UnsubscribeURL }}" in content


@pytest.mark.parametrize("path", TEMPLATE_FILES)
def test_template_go_template_syntax_validity(path: Path) -> None:
    content = path.read_text(encoding="utf-8")

    # Balanced Go template action tags
    open_tags = len(re.findall(r"\{\{", content))
    close_tags = len(re.findall(r"\}\}", content))
    assert open_tags == close_tags, f"Mismatched {{ (count={open_tags}) and }} (count={close_tags}) in {path.name}"

    # No empty variable before := or =
    assert not re.search(r"\{\{-?\s*:=\s*", content), f"Syntax error: empty variable before ':=' in {path.name}"
    assert not re.search(r"\{\{-?\s*=\s*", content), f"Syntax error: empty variable before '=' in {path.name}"

    # No extra braces (e.g. {{{ or }}})
    assert not re.search(r"\{\{\{", content), f"Syntax error: extra '{{{{' in {path.name}"
    assert not re.search(r"\}\}\}", content), f"Syntax error: extra '}}}}' in {path.name}"


@pytest.mark.parametrize("path", TEMPLATE_FILES)
def test_template_no_broken_or_placeholder_links(path: Path) -> None:
    """Ensure all links in the templates are valid, have non-empty hrefs, and contain no broken placeholders."""
    content = path.read_text(encoding="utf-8")
    links = re.findall(r'<a\b[^>]*?href=["\']([^"\']*)["\'][^>]*>', content, re.IGNORECASE)

    # Must contain opt-out and preference management links
    assert len(links) >= 2, f"Expected at least 2 links in {path.name}, found {len(links)}"

    for href in links:
        # Check against empty or fragment placeholders
        assert href.strip(), f"Empty href found in {path.name}"
        assert href.strip() != "#", f"Placeholder '#' href found in {path.name}"
        assert not href.startswith("javascript:"), f"Invalid javascript: link found in {path.name}"
        assert not href.startswith("/"), f"Broken relative URL found in {path.name}: {href}"

        # If it uses Listmonk template tags, ensure it is the valid UnsubscribeURL tag
        if "{{" in href:
            assert re.search(r"\{\{\s*UnsubscribeURL(?:\s*\?[^}]+)?\s*\}\}", href), (
                f"Unknown or invalid template tag in href: {href}"
            )
        else:
            # If standard URL, must be an absolute http/https URL
            assert href.startswith(("http://", "https://")), f"Invalid non-absolute URL in {path.name}: {href}"
