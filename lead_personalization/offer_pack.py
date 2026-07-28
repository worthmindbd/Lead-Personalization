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

    def subjects_for(self, segment: str, step: int) -> list[str]:
        seg = self.subject_templates.get(segment, self.subject_templates[FALLBACK_SEGMENT])
        return seg.get(step, self.subject_templates[FALLBACK_SEGMENT][step])


def _validate(pack: OfferPack) -> None:
    missing = [e for e in REQUIRED_EVIDENCE if e not in pack.openers]
    if missing:
        raise OfferPackError(f"offer pack '{pack.name}' openers missing: {missing}")
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
    data = json.loads(path.read_text(encoding="utf-8"))
    return offer_pack_from_dict(data)


def save_offer_pack(pack: OfferPack, path: str | Path) -> Path:
    out = Path(path)
    if not out.suffix:
        out = PACKS_DIR / f"{path}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(offer_pack_to_dict(pack), indent=2), encoding="utf-8")
    return out


def list_offer_packs() -> list[str]:
    if not PACKS_DIR.is_dir():
        return []
    return sorted(p.stem for p in PACKS_DIR.glob("*.json"))
