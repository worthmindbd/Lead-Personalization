"""Tests for premium, high-deliverability Listmonk email templates.

Ensures:
- Premium Visual Presentation: centered container card, responsive Aevora Media logo, professional typography.
- Jay's Ghost Ink Framework: 8-style stack, single data-gi="1" block, guaranteed non-empty output across all test/live scenarios.
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
def test_template_visual_structure_and_branding(path: Path) -> None:
    """Ensure templates maintain the premium card structure, responsive branding, and tracking pixel."""
    content = path.read_text(encoding="utf-8")

    # 1. Centered white container card
    assert "class=\"email-container\"" in content, f"Missing email-container in {path.name}"
    assert "class=\"email-card\"" in content, f"Missing email-card in {path.name}"

    # 2. Responsive Aevora Media logo image
    img_matches = re.findall(r'<img\b[^>]*>', content, re.IGNORECASE)
    assert len(img_matches) == 1, f"Expected exactly 1 logo image tag in {path.name}, found {len(img_matches)}"
    assert "logo-light.png" in img_matches[0], f"Logo image src missing logo-light.png in {path.name}"
    assert "Aevora Media" in img_matches[0], f"Logo alt text missing 'Aevora Media' in {path.name}"
    assert "class=\"email-header\"" in content, f"Missing email-header in {path.name}"

    # 3. Deliverability: no tracking pixel (tracking pixels trigger spam filters)
    assert "{{ TrackView }}" not in content, f"Tracking pixel should be removed for high deliverability in {path.name}"


@pytest.mark.parametrize("path", TEMPLATE_FILES)
def test_template_ghost_ink_intact_and_non_empty(path: Path) -> None:
    """Verify Jay's Ghost Ink Framework 8 CSS styles, single block rule, and guaranteed non-empty text."""
    content = path.read_text(encoding="utf-8")
    gi_matches = list(re.finditer(r'<div\s+[^>]*?data-gi=["\']?1["\']?[^>]*?>(.*?)</div>', content, re.DOTALL | re.I))
    assert len(gi_matches) == 1, f"Expected exactly 1 ghost ink block in {path.name}, found {len(gi_matches)}"

    # Required styles
    required_styles = [
        "color:transparent",
        "font-size:0px",
        "line-height:0px",
        "max-height:0px",
        "mso-hide:all",
        "overflow:hidden",
        "display:none",
        "opacity:0",
    ]
    for style in required_styles:
        assert style in content, f"Missing required hiding style '{style}' in {path.name}"

    # Inner content must contain a substantial fallback passage (guaranteed non-empty)
    inner_block = gi_matches[0].group(1)
    # Strip Go template tags
    clean_text = re.sub(r'\{\{.*?\}\}', '', inner_block).strip()
    words = len(clean_text.split())
    assert words >= 250, (
        f"Ghost Ink fallback passage in {path.name} is too short or empty ({words} words). "
        "Must guarantee at least 250 words of authentic studio reflection."
    )


@pytest.mark.parametrize("path", TEMPLATE_FILES)
def test_template_ghost_ink_placed_at_top_single_block(path: Path) -> None:
    """Ensure strictly ONE Ghost Ink block is placed at top of card (active content zone, before body)."""
    content = path.read_text(encoding="utf-8")
    
    # Strictly Rule 2: Exactly 1 hidden div with data-gi="1", no other hidden text containers
    gi_matches = list(re.finditer(r'<div\s+[^>]*?data-gi=["\']?1["\']?[^>]*?>', content, re.I))
    assert len(gi_matches) == 1, f"Expected exactly 1 ghost ink block in {path.name}, found {len(gi_matches)}"

    gi_pos = content.find('data-gi="1"')
    assert gi_pos != -1, f"Ghost ink block not found in {path.name}"

    # Placed in active content zone BEFORE email-content to shield against promo tab filters
    content_pos = content.find('class="email-content"')
    assert content_pos != -1, f"email-content div not found in {path.name}"
    assert gi_pos < content_pos, f"Ghost ink must be placed in active zone BEFORE email-content in {path.name}"

    # No suspicious zero-width spam evasion characters
    assert "&#847;" not in content, f"Suspicious zero-width character &#847; found in {path.name}"
    assert "&zwnj;" not in content, f"Suspicious zero-width character &zwnj; found in {path.name}"


@pytest.mark.parametrize("path", TEMPLATE_FILES)
def test_template_ghost_ink_contains_all_six_passages_and_rotation(path: Path) -> None:
    """Ensure all 6 authentic studio reflections are embedded and rotate automatically via Sprig."""
    from lead_personalization.ghost_ink import GHOST_INK_PASSAGES

    content = path.read_text(encoding="utf-8")
    for p in GHOST_INK_PASSAGES:
        # Check snippet of each passage is present
        assert p["text"][:80] in content, f"Passage '{p['id']}' missing from {path.name}"

    # Ensure dynamic Sprig modulo rotation logic is present
    assert "mod (add $id" in content, f"Automatic Sprig rotation expression missing in {path.name}"


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
