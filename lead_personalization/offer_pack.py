"""Offer packs: the sender's copy, decoupled from code.

An offer pack is a versioned JSON file holding the variant pools (openers,
segment solutions, CTAs, closers, support lines) and subject-line templates
that used to be hardcoded in ``process_batch.py`` / ``subjects.py``. Swapping
packs re-skins the whole campaign without touching the engine, which is the
foundation for future multi-tenant use.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

PACKS_DIR = Path(__file__).resolve().parent / "offer_packs"
DEFAULT_PACK = "aevora"

# Evidence buckets an opener pool must cover (see research.classify_evidence).
REQUIRED_EVIDENCE = ("linkedin_posts", "site_video", "social_video", "positioning", "weak")
# Segment copy and subject templates must at least define this fallback key.
FALLBACK_SEGMENT = "low_fit"
REQUIRED_STEPS = (1, 2, 3)


class OfferPackError(ValueError):
    """Raised when an offer pack is missing required keys or malformed."""


@dataclass
class OfferPack:
    name: str
    version: int
    greeting: str
    openers: dict[str, list[str]]
    segment_copy: dict[str, dict[str, list[str]]]
    cta_pools: dict[int, list[str]]
    closers: list[str]
    support_lines: list[str]
    subject_templates: dict[str, dict[int, list[str]]]

    def segment_solutions(self, segment: str) -> dict[str, list[str]]:
        return self.segment_copy.get(segment, self.segment_copy[FALLBACK_SEGMENT])


def _validate(pack: OfferPack) -> None:
    from lead_personalization.qa import (
        AI_SLOP_PHRASES,
        BANNED,
        BRAND_FORBIDDEN,
        HARD_CTA_PATTERNS,
        SPAM_TRIGGERS,
    )
    if pack.version != 1:
        # The loader understands exactly one pack schema; accepting an unknown
        # version would mis-parse it into silently wrong copy.
        raise OfferPackError(
            f"offer pack '{pack.name}': unsupported version {pack.version} "
            f"(this loader understands version 1)"
        )
    missing = [e for e in REQUIRED_EVIDENCE if e not in pack.openers]
    if missing:
        raise OfferPackError(f"offer pack '{pack.name}' openers missing: {missing}")
    # An empty pool would pass a key-presence check and then crash with
    # ZeroDivisionError in the copywriter's _pick — mid-batch, after research
    # credits were spent.
    for evidence in REQUIRED_EVIDENCE:
        if not pack.openers[evidence]:
            raise OfferPackError(
                f"offer pack '{pack.name}' openers['{evidence}'] is empty"
            )
    if FALLBACK_SEGMENT not in pack.segment_copy:
        raise OfferPackError(f"offer pack '{pack.name}' segment_copy missing '{FALLBACK_SEGMENT}'")
    for seg, blocks in pack.segment_copy.items():
        for key in ("solutions", "second_angle"):
            if not blocks.get(key):
                raise OfferPackError(f"segment '{seg}' missing non-empty '{key}'")
    for step in REQUIRED_STEPS:
        if not pack.cta_pools.get(step):
            raise OfferPackError(f"cta_pools missing step {step}")
    if not pack.closers or not pack.support_lines:
        raise OfferPackError("closers and support_lines must be non-empty")
    if FALLBACK_SEGMENT not in pack.subject_templates:
        raise OfferPackError(f"subject_templates missing '{FALLBACK_SEGMENT}'")
    for step in REQUIRED_STEPS:
        if not pack.subject_templates[FALLBACK_SEGMENT].get(step):
            raise OfferPackError(f"subject_templates['{FALLBACK_SEGMENT}'] missing step {step}")
    # segment_copy and subject_templates must agree on every segment key they
    # define, or the pack has a half-configured segment that either writes
    # copy with low_fit subjects or writes subjects with low_fit copy.
    seg_copy_segs = set(pack.segment_copy)
    subject_segs = set(pack.subject_templates)
    if seg_copy_segs != subject_segs:
        only_copy = sorted(seg_copy_segs - subject_segs)
        only_subjects = sorted(subject_segs - seg_copy_segs)
        raise OfferPackError(
            f"offer pack '{pack.name}': segment_copy and subject_templates "
            f"disagree (only in segment_copy: {only_copy}, "
            f"only in subject_templates: {only_subjects})"
        )
    # A banned phrase, hard CTA, AI slop, or em dash in a pool ships to every lead
    # that draws it. Fail at load, before research spends anything.
    needles = (
        [b.lower() for b in BANNED]
        + [s.lower() for s in AI_SLOP_PHRASES]
        + [w.strip().lower() for w in BRAND_FORBIDDEN if w.strip()]
        + [t.lower() for t in SPAM_TRIGGERS]
        + [p.lower() for p in HARD_CTA_PATTERNS]
        + ["—", "...", "…"]
    )
    pools: list[tuple[str, str]] = []
    for evidence, items in pack.openers.items():
        pools.extend((f"openers[{evidence}]", s) for s in items)
    for seg, blocks in pack.segment_copy.items():
        for key in ("solutions", "second_angle"):
            pools.extend(
                (f"segment_copy[{seg}][{key}]", s) for s in blocks.get(key, [])
            )
    for step, items in pack.cta_pools.items():
        pools.extend((f"cta_pools[{step}]", s) for s in items)
    pools.extend(("closers", s) for s in pack.closers)
    pools.extend(("support_lines", s) for s in pack.support_lines)
    for seg, steps in pack.subject_templates.items():
        for step, items in steps.items():
            pools.extend(
                (f"subject_templates[{seg}][{step}]", s) for s in items
            )
    for where, text in pools:
        low = (text or "").lower()
        hit = next((n for n in needles if n and n in low), None)
        if hit:
            raise OfferPackError(
                f"offer pack '{pack.name}' {where} contains forbidden text {hit!r}"
            )


def _coerce_int_keys(mapping: dict) -> dict:
    """JSON object keys are strings; step-indexed pools need int keys."""
    return {int(k): v for k, v in mapping.items()}


def offer_pack_from_dict(data: dict) -> OfferPack:
    try:
        pack = OfferPack(
            name=data["name"],
            version=int(data.get("version", 1)),
            greeting=data.get("greeting", "Hi,"),
            openers=data["openers"],
            segment_copy=data["segment_copy"],
            cta_pools=_coerce_int_keys(data["cta_pools"]),
            closers=data["closers"],
            support_lines=data["support_lines"],
            subject_templates={
                seg: _coerce_int_keys(steps)
                for seg, steps in data["subject_templates"].items()
            },
        )
    except KeyError as exc:
        raise OfferPackError(f"offer pack missing required field: {exc}") from exc
    except (ValueError, TypeError) as exc:
        # Non-numeric step keys etc. must surface as OfferPackError: the CLI
        # guards spend on this exception type failing BEFORE research runs.
        raise OfferPackError(f"offer pack malformed: {exc}") from exc
    _validate(pack)
    return pack


def offer_pack_to_dict(pack: OfferPack) -> dict:
    return {
        "name": pack.name,
        "version": pack.version,
        "greeting": pack.greeting,
        "openers": pack.openers,
        "segment_copy": pack.segment_copy,
        "cta_pools": {str(k): v for k, v in pack.cta_pools.items()},
        "closers": pack.closers,
        "support_lines": pack.support_lines,
        "subject_templates": {
            seg: {str(k): v for k, v in steps.items()}
            for seg, steps in pack.subject_templates.items()
        },
    }


def load_offer_pack(name_or_path: str | Path = DEFAULT_PACK) -> OfferPack:
    """Load an offer pack by name (from offer_packs/) or explicit file path."""
    path = Path(name_or_path)
    if not path.suffix:
        path = PACKS_DIR / f"{name_or_path}.json"
    if not path.is_file():
        raise OfferPackError(f"offer pack not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        # A syntactically broken pack must fail as OfferPackError — callers
        # (process_batch, run_batches) pre-flight the pack precisely so a bad
        # pack never costs a batch of research fetches and Apify credits.
        raise OfferPackError(f"offer pack '{path.name}' is not valid JSON: {exc}") from exc
    return offer_pack_from_dict(data)
