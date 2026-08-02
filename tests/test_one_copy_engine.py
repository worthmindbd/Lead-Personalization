"""There is one copy engine, and the pipeline runs it.

``scripts/personalization`` used to carry a full duplicate of the copy engine:
its own ``qa.py``, ``sanitize.py``, ``segments.py``, ``subjects.py``, and ~370
lines of variant pools and sequence assembly inside ``process_batch.py``. Two
parity tests held the copies together — which is a way of managing drift, not
preventing it, and it only worked for as long as somebody kept the parity tests
honest.

These tests replace the parity guards. They fail if a second copy comes back.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lead_personalization import copywriter, qa as lp_qa, sanitize as lp_sanitize  # noqa: E402
from lead_personalization.offer_pack import load_offer_pack  # noqa: E402
from personalization import process_batch as pb  # noqa: E402

# The names that used to be defined twice.
DUPLICATED_MODULES = ["qa", "sanitize", "segments", "subjects"]
COPY_POOLS = ["OPENERS", "SEGMENT_COPY", "CTA_POOLS", "CLOSERS", "SUPPORT_LINES"]


@pytest.mark.parametrize("name", DUPLICATED_MODULES)
def test_the_shipping_package_has_no_copy_of_the_engine(name):
    """A second qa.py under scripts/personalization is how the drift started."""
    assert not (REPO_ROOT / "scripts" / "personalization" / f"{name}.py").exists()


@pytest.mark.parametrize("pool", COPY_POOLS)
def test_process_batch_holds_no_copy_pools(pool):
    """The words belong in the offer pack, not in a research module."""
    assert not hasattr(pb, pool)


def test_process_batch_calls_the_library_copy_engine():
    """Not a same-named local function: the same object."""
    assert pb.generate_sequence is copywriter.generate_sequence
    assert pb.fix_sequence is copywriter.fix_sequence
    assert pb.contains_forbidden is lp_qa.contains_forbidden


def test_the_export_and_sanitize_paths_use_the_library_too():
    from personalization import apply_sanitize_all as asa, build_enriched as be

    assert be.qa is lp_qa.qa
    assert be.sequence_issues is lp_qa.sequence_issues
    assert asa.sanitize_email is lp_sanitize.sanitize_email


def test_normalize_leads_uses_the_library_segments():
    from lead_personalization import segments as lp_segments
    from personalization import normalize_leads as nl

    assert nl.segment_for_category is lp_segments.segment_for_category
    assert nl.CATEGORY_TO_SEGMENT is lp_segments.CATEGORY_TO_SEGMENT


def test_the_shipping_pack_is_a_real_pack():
    """process_batch names its pack by string; a typo there would only surface
    mid-run, after the batch had already spent its research calls."""
    pack = load_offer_pack(pb.OFFER_PACK_NAME)
    assert pack.name == pb.OFFER_PACK_NAME


def test_a_bad_offer_pack_name_fails_before_any_research(monkeypatch, capsys):
    """Discovering the typo after the batch has spent its fetches and Apify
    credits is the expensive way to find out."""
    monkeypatch.setattr(pb, "OFFER_PACK_NAME", pb.OFFER_PACK_NAME)  # restored on undo
    monkeypatch.setattr(
        sys, "argv",
        ["process_batch.py", "--batch-id", "001", "--offer-pack", "no-such-pack"],
    )
    monkeypatch.setattr(
        pb, "process_batch",
        lambda *a, **k: pytest.fail("research ran despite an unloadable offer pack"),
    )
    with pytest.raises(SystemExit) as exc:
        pb.main()
    assert exc.value.code != 0
    assert "no-such-pack" in capsys.readouterr().err


def test_the_offer_pack_flag_swaps_the_words(monkeypatch, tmp_path):
    """--offer-pack re-skins the campaign without editing process_batch.py."""
    from lead_personalization.offer_pack import offer_pack_to_dict

    data = offer_pack_to_dict(load_offer_pack("aevora")) | {"name": "test-pack"}
    pack_path = tmp_path / "test-pack.json"
    pack_path.write_text(json.dumps(data), encoding="utf-8")

    monkeypatch.setattr(pb, "OFFER_PACK_NAME", pb.OFFER_PACK_NAME)
    monkeypatch.setattr(
        sys, "argv",
        ["process_batch.py", "--batch-id", "001", "--offer-pack", str(pack_path)],
    )
    seen = {}

    def capture(*args, **kwargs):
        seen["pack"] = load_offer_pack(pb.OFFER_PACK_NAME).name
        return {}

    monkeypatch.setattr(pb, "process_batch", capture)
    pb.main()
    assert seen["pack"] == "test-pack"


def test_there_is_one_render_script():
    """process_batch used to point at a byte-identical copy next to itself."""
    assert pb.RENDER_SCRIPT.is_file()
    assert pb.RENDER_SCRIPT == REPO_ROOT / "lead_personalization" / "render_page.js"
    assert not (REPO_ROOT / "scripts" / "personalization" / "render_page.js").exists()
