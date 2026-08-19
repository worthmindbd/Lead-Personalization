"""Offer-pack loading fails loudly, before any money is spent.

``process_batch`` and ``run_batches`` pre-flight the pack specifically so a
bad pack costs nothing — that guarantee only holds if every way a pack can be
broken raises OfferPackError. These tests pin each failure mode, plus the
pack↔segments parity that used to be real but unenforced (adding a segment to
segments.py silently shipped low_fit copy for it).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from lead_personalization.offer_pack import (  # noqa: E402
    OfferPackError,
    load_offer_pack,
    offer_pack_from_dict,
)
from lead_personalization.segments import MACRO_SEGMENTS  # noqa: E402


def valid_pack_dict() -> dict:
    pack = load_offer_pack("aevora")
    return json.loads(json.dumps({
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
    }))


def test_the_real_pack_loads():
    pack = load_offer_pack("aevora")
    assert pack.name


def test_the_pack_covers_every_macro_segment():
    """A new segment in segments.py must come with pack copy, or it silently
    degrades to low_fit for every lead in it."""
    pack = load_offer_pack("aevora")
    assert set(pack.segment_copy) == set(MACRO_SEGMENTS)
    assert set(pack.subject_templates) == set(MACRO_SEGMENTS)


def test_an_empty_opener_pool_is_rejected_not_crashed_on_later():
    data = valid_pack_dict()
    data["openers"]["weak"] = []
    with pytest.raises(OfferPackError, match="openers\\['weak'\\] is empty"):
        offer_pack_from_dict(data)


def test_malformed_json_raises_offer_pack_error(tmp_path):
    broken = tmp_path / "broken.json"
    broken.write_text('{"name": "x",', encoding="utf-8")
    with pytest.raises(OfferPackError, match="not valid JSON"):
        load_offer_pack(broken)


def test_a_missing_pack_file_raises_offer_pack_error():
    with pytest.raises(OfferPackError, match="not found"):
        load_offer_pack("no-such-pack")


def test_a_non_numeric_step_key_raises_offer_pack_error():
    data = valid_pack_dict()
    data["cta_pools"] = {"one": ["x"], "2": ["y"], "3": ["z"]}
    with pytest.raises(OfferPackError, match="malformed"):
        offer_pack_from_dict(data)


def test_a_missing_required_field_raises_offer_pack_error():
    data = valid_pack_dict()
    del data["closers"]
    with pytest.raises(OfferPackError, match="missing required field"):
        offer_pack_from_dict(data)


def test_segment_copy_and_subject_templates_must_agree():
    data = valid_pack_dict()
    data["segment_copy"]["brand_new_segment"] = {
        "solutions": ["s"], "second_angle": ["a"],
    }
    with pytest.raises(OfferPackError, match="disagree"):
        offer_pack_from_dict(data)


def test_an_unknown_pack_version_is_rejected():
    data = valid_pack_dict()
    data["version"] = 2
    with pytest.raises(OfferPackError, match="unsupported version"):
        offer_pack_from_dict(data)


def test_a_broken_pack_never_reaches_research(tmp_path):
    """The exact CLI guarantee: run_batches' pre-flight catches OfferPackError
    before a single fetch. A raw JSONDecodeError or ValueError would escape it."""
    broken = tmp_path / "broken.json"
    broken.write_text("{nope", encoding="utf-8")
    with pytest.raises(OfferPackError):
        load_offer_pack(broken)
