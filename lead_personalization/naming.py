"""List-naming policy: campaign stems and slugs, spelled once.

Four scripts used to carry their own ``campaign_stem`` with slightly different
suffix lists, and three carried their own ``slugify`` — the exact drift pattern
the artifact-namespacing work fixed for filenames. Every stage derives the
same campaign name from the same list title through here.
"""

from __future__ import annotations

import re

# Stage suffixes and words that terminate a campaign name: a list file is
# named "<campaign>-<count>-<stage>.csv" and the campaign is what precedes the
# count. Union of the four former copies, so behavior for real inputs is
# unchanged (none of them ever saw an "-enriched" input at their call sites).
_STAGE_SUFFIXES = ("-with-email", "-cleaned", "-verified", "-valid", "-normalized")
_STAGE_WORDS = frozenset({
    "cleaned", "with-email", "verified", "valid", "normalized", "with", "email",
})


def campaign_stem(stem: str) -> str:
    """Return the campaign prefix without row-count or stage suffixes."""
    s = (stem or "").lower().replace("-38k", "")
    for suffix in _STAGE_SUFFIXES:
        if s.endswith(suffix):
            s = s[: -len(suffix)]
    alpha: list[str] = []
    for part in s.split("-"):
        if part.isdigit():
            break
        if part in _STAGE_WORDS:
            break
        alpha.append(part)
    return "-".join(alpha) or "mixed"


def slugify(title: str, fallback: str = "list") -> str:
    """Slug for Drive list titles ("July 25,2026" -> "july-25-2026")."""
    slug = re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")
    return slug or fallback
